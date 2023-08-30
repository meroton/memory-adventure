#!/usr/bin/env python3

"""
Parse Bazel's profiling data.
This can print what functions were evaluated
within a certain time threshold of the end of the profile.
Or the last function evaluated by each executor thread.

Background:

    $ acat profile.gz | jq '.traceEvents[] | select(.cat == "gc notification")' | grep name | sort | uniq -c
          7   "name": "major GC",
        158   "name": "minor GC",

Some allowances are made:

    * The traceEvents[] array can be truncated during crashes.
      So we throw away the last incomplete entry and close the array and json object
      to parse all successfully written events.

    * The `duration` is not always set for garbage collection.

        $ acat profile.gz | jq '.traceEvents[] | select(.cat == "gc notification")' | choose 0 | sort | uniq -c
            165 {
            165 }
            165 "cat":
            161 "dur":
            165 "name":
            165 "ph":
            165 "pid":
            165 "tid":
            165 "ts":

TODO:

    * Implement a normalized overlapping GC measure.
      How many garbage collections are triggered during a function's execution?
      That should correlate with the memory pressure.

    * Implement a partition and total duration measure.
      We see that with lower RAM limits the number of function calls increase,
      presumably because the garbage collections preempt regular executions.
      We can sum the total duration time of each function and plot that against the memory limit.

      The idea is that a memory hungry function would increase its total duration more,
      as it should be the proximate cause of garbage collection.

      This measure ought to correlate with the normalized GC overlap measure.

      One could also plot the number of calls to each function,
      for much the same purpose.

      Both of these could be made relative to the total duration and call count,
      to see if they take a bigger proportion of analysis resources
      with lower memory limits.

Limitations:

    * This does not handle stacked events,
      the profile often contain multiple largely overlapping events for an evaluator.
      That form the Starlark call stack.
      We sort by the end-time of all events so presumably only the top-level function would be shown
      (which is less-than-ideal in the presence of anonymous functions "lambda").
      But in practice we see a richer distribution from the stack trace,
      possibly for truncation events, or how Bazel schedules work across executors(?).

"""

from dataclasses import dataclass
from typing import Dict, List, TypeVar, Callable, Tuple, Optional, Union
import argparse
import json
import matplotlib.pyplot as plt
import sys
import re

PROGRAM = sys.argv[0]

TIMESTAMPUNIT = "UNIT"  # TODO: microseconds?

SENTINEL_STRING = "SENTINEL"
SENTINEL_INTEGER = -1234

HISTOGRAM = "histogram"
THREADS = "threads"
FAR = "far"
MEDIUM = "medium"
CLOSE = "close"
BIN_NAMES = [FAR, MEDIUM, CLOSE]
OUTPUT_FILTERS = [HISTOGRAM, THREADS, FAR, MEDIUM, CLOSE]

# Event categories
FUNCTION_CALL = "Starlark user function call"
GARBAGE_COLLECTION = "gc notification"
MAJOR_GC = "major GC"


@dataclass
class Event:
    category: str = SENTINEL_STRING
    name: str = SENTINEL_STRING
    ph: str = SENTINEL_STRING
    timestamp: int = SENTINEL_INTEGER
    duration: int = SENTINEL_INTEGER
    pid: int = SENTINEL_INTEGER
    tid: int = SENTINEL_INTEGER

    # TODO: consider memoize
    def end(self) -> int:
        return self.timestamp + self.duration

    def brief(self) -> str:
        return f"{self.name} {self.end()}"


def parse(jsons: List[dict]) -> List[Event]:
    dummy = Event()
    events = [dummy] * len(jsons)
    for i, j in enumerate(jsons):
        try:
            cat = j["cat"]
            dur = j.get("dur", SENTINEL_INTEGER)
            if dur == SENTINEL_INTEGER and not cat == GARBAGE_COLLECTION:
                raise KeyError("duration is not set")

            event = Event(
                cat,
                j["name"],
                j["ph"],
                j["ts"],
                dur,
                j["pid"],
                j["tid"],
            )
            events[i] = event
        except:
            print(f"Error parsing json blob: {j}", file=sys.stderr)
            raise

    return events


T = TypeVar("T")


def filled_partition(
    xs: List[T], inclusive: Callable[[T], bool]
) -> Tuple[List[Optional[T]], List[Optional[T]]]:
    """Like `partition` but put `None` into the other list

    So the two lists can be plotted against a shared x-axis.
    """
    ok: Dict[bool, List[Optional[T]]] = {
        True: [],
        False: [],
    }

    for x in xs:
        ok[inclusive(x)].append(x)
        ok[not inclusive(x)].append(None)

    return ok[True], ok[False]


def partition(xs: List[T], inclusive: Callable[[T], bool]) -> Tuple[List[T], List[T]]:
    yes, no = [], []

    for x in xs:
        if inclusive(x):
            yes.append(x)
        else:
            no.append(x)

    return yes, no


def plot(
    *,
    yaxis: Tuple[Union[List[int], List[Optional[int]]], str],
    xaxis: Tuple[List[int], str],
    image: str,
    title: Optional[str] = None,
    otherys: Optional[List[Optional[int]]] = None,
    legend: Optional[Tuple[str, str]] = None,
    plot_options: Dict[str, Union[str, int]] = {"markersize": 1},
):
    xs, xlabel = xaxis
    ys, ylabel = yaxis

    fig, ax = plt.subplots()

    opts = {**plot_options}
    if legend:
        opts["label"] = legend[0]

    ax.plot(xs, ys, ". ", **opts)

    if otherys:
        opts = {**plot_options}
        if legend:
            opts["label"] = legend[1]
        ax.plot(xs, otherys, ". ", **opts)
        plt.legend()

    if title:
        ax.set_title(title)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    fig.tight_layout()
    plt.savefig(image)
    print(f"Saved {image}")


def repair(blob: str) -> Tuple[str, bool]:
    """Tells whether the input was repaired or not."""
    end = blob[-2:]
    if end == "\n}":
        return blob, False

    # Lines are contained objects of the `traceEvent` array
    # so we can throw out the last truncated event and close the array.
    parts = blob.splitlines()
    parts[-2] = parts[-2].rstrip(",")
    parts[-1] = "]}"

    return "\n".join(parts), True


def main(
    json_input: str,
    output_filter: str,
    *,
    threshold_limits: List[str],
    plot_active_gc: Optional[str] = None,
    plot_gc_duration: Optional[str] = None,
    plot_gc_difference: Optional[str] = None,
):
    assert (
        output_filter in OUTPUT_FILTERS
    ), f"unexpected output filter '{output_filter}'"
    # NB: A successful build returns good json that can be loaded.
    # But failures truncate the character stream.
    repaired, damaged = repair(json_input)
    if damaged:
        print(
            "Warning: input was truncated, a best effort repair has been performed. Any number of events may have been lost.",
            file=sys.stderr,
        )

    profile = json.loads(repaired)

    raw_events = profile["traceEvents"]
    to_parse = []
    names = {}

    for raw in raw_events:
        if raw.get("name", SENTINEL_STRING) == "thread_name":
            tid = raw["tid"]
            name = raw["args"]["name"]
            # NB: Some events have a space for the evaluator name.
            name = name.replace(" ", "-")
            names[tid] = name

        if raw.get("cat", SENTINEL_STRING) in [
            FUNCTION_CALL,
            GARBAGE_COLLECTION,
        ]:
            to_parse.append(raw)

    parsed: List[Event] = parse(to_parse)
    # Sort by end-time.
    events = sorted(parsed, key=lambda e: e.end())
    function_calls, gcs = partition(events, lambda x: x.category == FUNCTION_CALL)

    # TODO: we could optimize the code to only parse thresholds if the `filter`
    # requires it.
    assert len(threshold_limits) == 3
    thresholds = {
        CLOSE: threshold_limits[0],
        MEDIUM: threshold_limits[1],
        FAR: threshold_limits[2],
    }
    assert sorted(thresholds.keys()) == sorted(BIN_NAMES)

    bins: Dict[str, List[Event]] = {key: [] for key in thresholds.keys()}

    # # Keep track of each evaluator / thread
    threads = {}
    # Threads are named when they are created,
    # Events are only tied to the thread id.

    first = function_calls[0].timestamp
    latest = function_calls[-1].end()

    for e in function_calls:
        threads[e.tid] = e

        diff = latest - e.end()
        assert diff >= 0

        for k, v in thresholds.items():
            if diff < v:
                bins[k].append(e)

    printer = lambda e: e.brief()
    # To compute total duration use `printer = lambda e: e.name + " " + str(e.duration)`

    # # Output Filters
    if output_filter == HISTOGRAM:
        for binname, bin in bins.items():
            for e in bin:
                print(binname, printer(e))

    elif output_filter in BIN_NAMES:
        for e in bins[output_filter]:
            print(printer(e))

    elif output_filter == THREADS:
        for tid, e in threads.items():
            diff = latest - e.end()
            # Some evaluators do not do much, and their last job can be very far
            # from the end.
            # So prune by the distance.
            if diff > thresholds["far"]:
                continue

            tname = names[tid]
            print(tname, printer(e))

    else:
        assert False, "unexpected output_filter"

    garbage_collections(
        gcs,
        plot_active_gc=plot_active_gc,
        plot_gc_duration=plot_gc_duration,
        plot_gc_difference=plot_gc_difference,
    )


def garbage_collections(
    gcs: List[Event],
    *,
    plot_active_gc: Optional[str] = None,
    plot_gc_duration: Optional[str] = None,
    plot_gc_difference: Optional[str] = None,
):
    """Plot some exploratory garbage collection measures."""
    if (not plot_active_gc) and (not plot_gc_duration):
        # Nothing to do
        return

    # # stack monoid
    # (time, start | end)
    stack = [(-1, 0)] * 2 * len(gcs)
    index = 0
    for gc in gcs:
        start = gc.timestamp
        assert start > 0, "Unexpected start timestamp for GC"
        stack[index] = (start, +1)
        index += 1
        stack[index] = (gc.end(), -1)
        index += 1

    stack = sorted(stack, key=lambda t: t[0])
    times = [0] * len(stack)
    active_gcs = [-1] * len(stack)

    cumulative = 0
    for i, change in enumerate(stack):
        time = change[0]
        times[i] = time
        cumulative += change[1]
        if not cumulative >= 0:
            print(
                f"Warning: {time} negative active GC number, probably because some messages have no end time.",
                file=sys.stderr,
            )

        active_gcs[i] = cumulative

    if plot_active_gc:
        plot(
            yaxis=(active_gcs, "Active garbage collections [#]"),
            xaxis=(times, f"Time [{TIMESTAMPUNIT}]"),
            image=plot_active_gc,
        )

    if plot_gc_duration:
        majors, minors = filled_partition(gcs, lambda x: x.name == MAJOR_GC)
        plot(
            yaxis=(
                [x.duration if x else None for x in majors],
                f"Garbage collection duration [{TIMESTAMPUNIT}]",
            ),
            otherys=[x.duration if x else None for x in minors],
            xaxis=(
                [x.timestamp for x in gcs],
                f"Garbage collection start time [{TIMESTAMPUNIT}]",
            ),
            image=plot_gc_duration,
            legend=("Major GC", "Minor GC"),
        )

    if plot_gc_difference:
        differences: List[Tuple[str, int]] = [("", 0)] * (len(gcs) - 1)
        for i in range(1, len(gcs)):
            index = i - 1
            event = gcs[i]
            diff = event.timestamp - gcs[i - 1].timestamp
            differences[index] = (event.name, diff)
        dmajors, dminors = filled_partition(differences, lambda x: x[0] == MAJOR_GC)

        plot(
            yaxis=(
                [x[1] if x else None for x in dmajors],
                f"Time since last GC started [{TIMESTAMPUNIT}]",
            ),
            otherys=[x[1] if x else None for x in dminors],
            xaxis=(range(len(gcs) - 1), "Index"),
            image=plot_gc_difference,
            plot_options={"markersize": 2},
            legend=("Major GC", "Minor GC"),
        )


def arguments(args: List[str]):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f"""\
Parse Bazel's profile data to show active Starlark evaluators at the end.
This can help finding which Starlark function is most likely responsible for the crash.
This can be used as create statistical data for many crashes,
where suspicious functions show up more often.

    zcat /path/to/profile.gz | {PROGRAM}

The output filter can be chosen:
   {THREADS}: The last event for each skyframe evaluator, within {FAR} cutoff of the end.
   {HISTOGRAM}: Histogram of cut-offs.
   {FAR}: All events within the {FAR} cutoff.
   {MEDIUM}: All events within the {MEDIUM} cutoff.
   {CLOSE}: All events within the {CLOSE} cutoff.

The end time of events is a little bit fuzzy, and during tear down one event tends
to execute longer than the others, this is an indicator that it could be the problem
but sometimes a previous function leaked the memory and the final Out-of-Memory
is from an innocuous allocation.
""",
    )
    # TODO: `threads` without a cutoff?
    # TODO: single latest event?
    # TODO: argument to set the cutoffs?
    # TODO: output format? original events? named events?
    # TODO: should the time filter be split? So we can show active threads
    #       within the threshold?
    parser.add_argument(
        "--show",
        choices=OUTPUT_FILTERS,
        default=THREADS,
        help="change output filter.",
    )
    parser.add_argument(
        "--plot-active-gc",
        help="Plot number of concurrent active garbage collection events to a file",
    )
    parser.add_argument(
        "--plot-gc-duration",
        help="Plot duration of garbage collection events to a file",
    )
    parser.add_argument(
        "--plot-gc-difference",
        help="Plot difference of garbage collection start times to a file",
    )
    parser.add_argument(
        "--thresholds",
        help="Select thresholds for <close>,<medium>,<far>.",
        default="1e5,1e6,1e7",
    )

    return parser.parse_args(args)


if __name__ == "__main__":
    args = arguments(sys.argv[1:])

    pipe: str = sys.stdin.read()
    # from now on `pdb` works
    sys.stdin = open("/dev/tty")

    thresholds = [int(float(s)) for s in args.thresholds.split(",")]
    assert len(thresholds) == 3, "invalid threshold value: " + args.thresholds

    main(
        pipe,
        output_filter=args.show,
        threshold_limits=thresholds,
        plot_active_gc=args.plot_active_gc,
        plot_gc_duration=args.plot_gc_duration,
        plot_gc_difference=args.plot_gc_difference,
    )
