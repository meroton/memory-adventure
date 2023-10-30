#!/usr/bin/env python3

"""
# Memory Plot
Plot time and garbage collection pressure for Bazel builds with varying memory.

## Usage

::

    # Generate the data, this takes a couple of seconds per build of this Bazel
    # workspace. So using `tee` to cache the result speeds up iteration significantly.
    $ ./memory-plot.py --out plot-combined.png \
        <(echo ./measurement-regular/*/ | xargs -n1 ./stats.sh | grep -v WARMUP | tee cache-regular) \
        <(echo ./measurement-skymeld/*/ | xargs -n1 ./stats.sh | grep -v WARMUP | tee cache-skymeld)
    # Iterate the plot on the same data.
    $ ./memory-plot.py [--out phase-regular.png] --exclude-crashes cache-regular

## Measurement Data

This requires Bazel's `profiling data`_ for multiple build with different memory limits.
Bazel's memory can be limited through the startup option:

    --export STARTUP_FLAGS \
        --host_jvm_args=-Xmx500m

And you want the allocation instrumenter, as is explained in the `memory guide`_

    set --export STARTUP_FLAGS \
        --host_jvm_args=-javaagent:java-allocation-instrumenter-3.3.0.jar \
        --host_jvm_args=-DRULE_MEMORY_TRACKER=1 \
        --host_jvm_args=-Xmx500m

.. _profiling data:

To enable the profiling data add the following flags to your build
`--generate_json_trace_profile` and `--profile=<profile file>`,
for better fidelilty we recommend `--noslim_profile`, to avoid merging events,
which is faster but requires extra effort to parse.

You can also save the console output, the build event protocol (`--build_event_json_file`),
Starlark CPU pprof-profile (`--starlark_cpu_profile=<pprof file>`),
and heap (`--heap_dump_on_oom`). This will capture the most data for you,
so you can analyze it further after the fact.
There is certainly more signal to find in all this data than what we have today.

.. _sample benchmarking file:

You can start with `./benchmark-different-memory` in this repository,
it is designed to make multiple attempts with different memory limits.

This has a bunch of flags, first skymeld, nobuild, or just regular,
then the `profiling data`_ flags,
followed by remote execution to a local Buildbarn deployment
and finally our memory traversal aspect that we want to benchmark.
You probably want to split this up into multiple bash arrays or bazelrc configs.

.. _measurement driver:

You can drive measurements with any looper-program, or two nested shell loops.
We used `hyperfine`_,
which is a great general purpose benchmarking tool
but we do not actually use its time measurement.

First is the loop of memory limits,
then you decide the number of iterations for each limit.
Following good practices, we used warmup runs for each limit,
but did not see any difference in the behavior compared to real runs.

Example::

    hyperfine \
        --parameter-list run "$( { echo WARMUP; seq 5; } | paste -sd ',')" \
        --parameter-list mem "$( { seq 155 1 180; seq 190 5 250; seq 250 10 300; seq 300 50 1000; } | paste -sd ',')" \
        --runs 1 \
        --ignore-failure \
        -- './benchmark-different-memory measurements-skymeld/ {mem}m {run} --skip-if-exists'

Note that the memory is currently analyzed from the directory name.
.. TODO: parse it from the profile, or write to a file in the directory.

.. _extract stats:

We now have the measurements we need, and can begin analyzing them.
Here we split the path, first we will discuss the plots of build duration of this script,
then we will discuss `further analysis`_ you can do to find memory thieves,
which is not part of this program.

This program requires the duration and garbage collection count from a measurement.
The data is fed in one or two files (so you can cache the computation, see the `usage`_ section),
containing comma-separated (csv) data:
    <memory limit: <str>>,<iteration: int>,<gc count: int>,<duration: int>,<status: str: "crash"|"ok">

.. _further analysis:

We think that the following data points are very interesting:
    # The active functions at the time of a crash
    # All functions in a successful build
These can be combined
    # The most commonly seen functions when Bazel crashes
    # The most overrepresented functions when Bazel crashes,
      this requires the baseline distribution.
Additionally you can look at functions and correlate with GC events
    # Number of time-adjusted GC events during evaluation of a function.
And much much more, please tell us your ideas.

.. _basic analysis:

Some basic measurements for memory pressure through garbage collection
were implemented in `parse-profile.py` as part of the exploratory work,
you can look at them, but we did not see any interesting signals.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, TypeVar, Callable, Tuple, Optional, Union
from collections import defaultdict
import statistics as stats
import argparse
import json
import matplotlib.pyplot as plt
import sys

PROGRAM = sys.argv[0]

TIMESTAMPUNIT = "s"
MEMORYUNIT = "MB"

Mean = float
StandardDeviation = float
Index = int


class Status(Enum):
    Ok = "ok"
    Crash = "crash"

    @staticmethod
    def status(x: str):
        if x == "ok":
            return Status.Ok

        if x == "crash":
            return Status.Crash

        raise Exception("Invalid Status: " + x)


@dataclass
class Run:
    memory: str
    attempt: int
    gc_count: int
    duration: int
    status: Status


@dataclass
class Memory:
    memory: str
    gc_counts: List[int]
    durations: List[int]
    status: Status
    crashes: List[Index]
    crash_fraction: float


def numeric_memory(x: Union[Run, Memory]) -> int:
    return int(x.memory.rstrip("m"))


def memory(parsed: List[Run], exclude_crashes: bool = False) -> List[Memory]:
    durations = defaultdict(list)
    gc_counts = defaultdict(list)
    statuses: Dict[str, List[Status]] = defaultdict(list)

    for run in parsed:
        statuses[run.memory].append(run.status)
        durations[run.memory].append(run.duration)
        gc_counts[run.memory].append(run.gc_count)

    res = []
    for key in durations.keys():
        crash_indices = [i for i, s in enumerate(statuses[key]) if s == Status.Crash]
        fraction = len(crash_indices) / len(statuses[key])

        gc_count = gc_counts[key]
        duration = durations[key]

        status = Status.Ok if len(crash_indices) == 0 else Status.Crash
        result = Memory(key, gc_count, duration, status, crash_indices, fraction)

        res.append(result)

    return res


def parse(lines: List[str]) -> List[Run]:
    """CSV encoded from an external program."""
    runs = []
    for line in lines:
        parts = line.split(",")
        assert len(parts) == 5
        parts = [x.strip() for x in parts]
        run, attempt, gc_count, duration, status = parts
        runs.append(
            Run(run, int(attempt), int(gc_count), int(duration), Status(status))
        )

    return runs


def fill_out_indices(
    indices: List[Index],
    points: list[int],
    range: Optional[Tuple[int, int]] = None,
) -> list[int]:
    """If an underlying array is filled with empty, the indices must be adjusted."""

    positions = [points[i] for i in indices]
    filled_out_range = fill_with_empty(points, points, range)
    res = []
    for i, val in enumerate(filled_out_range):
        if val and val in positions:
            res.append(i)

    return res


def fill_with_empty(
    values: Union[list[float], list[int]],
    points: list[int],
    range: Optional[Tuple[int, int]] = None,
) -> list[Optional[float]]:
    """Create a dense list for each `point` in `range` with None where there is not `value`."""
    assert points == sorted(points), "Points must be sorted"

    if not range:
        range = (points[0], points[-1])

    res: List[Optional[float]] = [None] * (range[1] - range[0] + 1)
    for i, point in enumerate(points):
        index = point - range[0]
        res[index] = values[i]

    return res


def filter_away(ins: list, indices: List[int]) -> list:
    res = []
    for i, x in enumerate(ins):
        if not i in indices:
            res.append(x)
    return res


def statistics(
    measurements: List[Memory],
    exclude_crashes: bool = False,
    time_scale: float = 1,
) -> Tuple[List[Mean], List[StandardDeviation], List[Mean], List[StandardDeviation]]:
    """Calculate Mean and StandardDeviation for `gc_counts` and `duration`.

    Returns four lists.
    >>> gc_mean, gc_stdev, dur_mean, dur_stdev = statistic(....)
    """
    count = len(measurements)
    gc_mean: List[Mean] = [0] * count
    dur_mean: List[Mean] = [0] * count
    gc_stdev: List[StandardDeviation] = [0] * count
    dur_stdev: List[StandardDeviation] = [0] * count

    for i, measurement in enumerate(measurements):
        gc_mean[i] = sum(measurement.gc_counts) / len(measurement.gc_counts)
        dur_mean[i] = sum(measurement.durations) / len(measurement.durations)
        dur_mean[i] /= time_scale

        gc_counts = measurement.gc_counts
        if exclude_crashes:
            gc_counts = filter_away(gc_counts, indices=measurement.crashes)
        gc_stdev[i] = stats.stdev(gc_counts) if len(gc_counts) > 1 else 0
        durations = measurement.durations
        if exclude_crashes:
            durations = filter_away(durations, indices=measurement.crashes)
        dur_stdev[i] = stats.stdev(durations) if len(durations) > 1 else 0
        dur_stdev[i] /= time_scale

        if dur_mean[i] - dur_stdev[i] < 0:
            mean = dur_mean[i]
            stdev = dur_stdev[i]
            print("Outlier warning: ", mean, stdev, measurement.memory)

    return gc_mean, gc_stdev, dur_mean, dur_stdev


def filter(xs: list, inclusive: Callable[Any, bool]) -> Tuple[list, list]:
    yes, no = [], []

    for x in xs:
        if inclusive(x):
            yes.append(x)
        else:
            no.append(x)

    return yes, no


def partition(vals: list, mask: List[int]) -> Tuple[list, list]:
    yes, no = [], []
    count = len(vals)

    for index in range(count):
        if index in mask:
            yes.append(vals[index])
        else:
            no.append(vals[index])

    return (yes, no)


def filled_partition(
    xs: List[Any], *, mask: List[int]
) -> Tuple[List[Optional[float]], List[Optional[float]]]:
    """Like `partition` but put `None` into the other list

    So the two lists can be plotted against a shared x-axis.
    """
    count = len(xs)
    a: List[Optional[float]] = [None] * count
    b: List[Optional[float]] = [None] * count

    for index in range(count):
        val = xs[index]
        if index in mask:
            a[index] = val
        else:
            b[index] = val

    return a, b


def plot(
    fig: Any,  # matplotlib Figure
    ax: Any,  # matplotlib Axes
    *,
    ys: Tuple[List[Mean], List[StandardDeviation]],
    xs: List[float],
    crashes: Optional[
        List[Index]
    ] = None,  # Indices from `ys` that should be split and indicated as crashes.
    plot_options: Dict[str, Union[str, int]] = {
        "markersize": 3,
        "marker": "o",
        "linestyle": "None",
        "label": "Duration (Ok)",
    },
    crash_plot_options: Dict[str, Union[str, int]] = {
        "marker": "x",
        "markersize": 3,
        "color": "red",
        "linestyle": "None",
        "label": "Duration (Crash)",
    },
) -> List[Any]:
    plots: List[Any] = []  # matplotlib plot object.

    yvalues, yerrors = ys
    ycrashes: List[Optional[Mean]] = []
    if crashes:
        # TODO: Make sure these are all consistent
        ycrashes, yvalues = partition(yvalues, mask=crashes)
        yerr_crashes, yerr_oks = partition(yerrors, mask=crashes)
        xcrashes, xoks = partition(xs, mask=crashes)
    else:
        xoks = xs
        yerr_oks = yerrors

    plots.append(ax.errorbar(xoks, yvalues, yerr=yerr_oks, **plot_options))

    if crashes:
        plots.append(
            ax.errorbar(xcrashes, ycrashes, yerr=yerr_crashes, **crash_plot_options)
        )

    bars = [p[2] for p in plots]
    for b in bars:
        b[0].set_alpha(0.3)

    return plots


def main(
    # (name, content)
    datasets: list[Tuple[str, str]],
    *,
    plot_file: Optional[str],
    exclude_crashes: bool,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
):
    assert len(datasets) <= 2, "One or two datasets are supported."
    show_garbage_collections = len(datasets) < 2

    plotsets: List[List[Memory]] = []
    for name, data in datasets:
        # TODO: do we need name what should it be set to?
        parsed: List[Run] = parse(data.splitlines())
        parsed = sorted(parsed, key=lambda x: numeric_memory(x))

        measurements: List[Memory] = memory(parsed, exclude_crashes=exclude_crashes)
        if minimum:
            measurements = [m for m in measurements if numeric_memory(m) > int(minimum)]
        if maximum:
            measurements = [m for m in measurements if numeric_memory(m) < int(maximum)]

        plotsets.append(measurements)

    plots = []
    fig, ax = plt.subplots()
    ax2 = ax.twinx() if show_garbage_collections else None

    def options(marker, color, label, linestyle="None", **kwargs):
        return {
            "linewidth": 1,
            "markersize": 3,
            "marker": marker,
            "color": color,
            "label": label,
            "linestyle": linestyle,
            **kwargs,
        }

    colors = {
        # -        "crash": ["#de2222", "#e54e4e"],
        # -        "ok": ["#5822de", "#9472ea"],
        "crash": ["#de2222", "#888888"],
        "ok": ["#4169E1", "#888888"],
        "gc": ["orange", "#aaaaaa"],
    }
    labels = {
        "ok": ["Regular", "Skymeld"],
        "crash": ["Regular (Crash)", "Skymeld (Crash)"],
    }

    # NB: We index the colors backwards, to grey out previously shown graphs.
    # The other lists are indexed as usual.
    backwards = lambda x: len(plotsets) - 1 - x

    for index, measurements in enumerate(plotsets):
        # Crashes in unfilled indices.
        crash_indices = []
        for i, val in enumerate(measurements):
            if val.status == Status.Crash:
                crash_indices.append(i)

        points = [numeric_memory(m) for m in measurements]

        deconstruct = statistics(
            measurements, exclude_crashes=exclude_crashes, time_scale=1e6
        )
        gc_mean, gc_stdev, dur_mean, dur_stdev = deconstruct
        xs = [float(p) for p in points]

        minus = [0] * len(deconstruct[2])
        for i, mean in enumerate(deconstruct[2]):
            minus[i] = mean - deconstruct[3][i]
            mem = measurements[i].memory
            status = measurements[i].status
            crash_fraction = measurements[i].crash_fraction
            print(
                "memory|duration|mean|stdev|minus|status|crash-fraction",
                mem,
                mean,
                deconstruct[3][i],
                minus[i],
                status,
                crash_fraction,
            )

        plots.extend(
            plot(
                fig,
                ax,
                ys=(dur_mean, dur_stdev),
                xs=xs,
                crashes=crash_indices,
                plot_options=options(
                    "o",
                    colors["ok"][backwards(index)],
                    labels["ok"][index],
                    linestyle="-",
                ),
                crash_plot_options=options(
                    "x",
                    colors["crash"][backwards(index)],
                    labels["crash"][index],
                    linestyle="--",
                ),
            )
        )

        if show_garbage_collections:
            plots.extend(
                plot(
                    fig,
                    ax2,
                    ys=(gc_mean, gc_stdev),
                    xs=xs,
                    plot_options=options(
                        "o",
                        colors["gc"][backwards(index)],
                        "Regular",
                        linestyle="-",
                    ),
                )
            )

    # TODO: Tidy up
    xlabel = f"Memory limit [{MEMORYUNIT}]"
    ylabel_a = f"Duration [{TIMESTAMPUNIT}]"

    ax.semilogx()
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel_a)
    if show_garbage_collections:
        ylabel_b = "Garbage Collections"
        ax2.set_ylabel(ylabel_b)

    labs = [p.get_label() for p in plots]
    ax.legend(plots, labs, loc=0)

    title = None
    if title:
        ax.set_title(title)

    # Make sure 0 is shown.
    ylims = ax.get_ylim()
    ylims = (0, max(201, ylims[1]))
    ax.set_ylim(ylims)
    xlims = ax.get_xlim()
    xlims = (min(0, xlims[0]), max(1040, xlims[1]))
    ax.set_xlim(xlims)

    if show_garbage_collections:
        ylims = ax2.get_ylim()
        ylims = (min(0, ylims[0]), ylims[1])
        ax2.set_ylim(ylims)

    ticks = [
        (100, "100"),
        (150, "150"),
        (200, ""),
        (300, "300"),
        (400, ""),
        (500, "500"),
        (600, ""),
        (700, "700"),
        (800, ""),
        (900, ""),
        (1000, "1000"),
    ]
    ticks, _ = filter(
        ticks, inclusive=lambda t: t[0] <= int(maximum) if maximum else True
    )
    plt.xticks(
        [position[0] for position in ticks],
        [label[1] for label in ticks],
        rotation="vertical",
    )

    fig.tight_layout()
    if plot_file:
        plt.savefig(plot_file)
        print(f"Saved {plot_file}")
    else:
        plt.show()


def arguments(args: List[str]):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        help="Plot to a file",
    )
    parser.add_argument("--min", help=f"Minimum memory to plot [{MEMORYUNIT}]")
    parser.add_argument("--max", help=f"Maximum memory to plot [{MEMORYUNIT}]")
    parser.add_argument(
        "--exclude-crashes",
        help="Exclude crashes from duration standard deviation.",
        action="store_true",
    )
    parser.add_argument(
        "data",
        help="Datafile, use `./stats.sh` to extract data from profiles.",
        nargs="+",
    )

    return parser.parse_args(args)


if __name__ == "__main__":
    args = arguments(sys.argv[1:])

    # from now on `pdb` works
    sys.stdin = open("/dev/tty")
    datasets: List[Tuple[str, str]] = []
    for i, datafile in enumerate(args.data):
        with open(datafile, "r") as f:
            datasets.append((str(i), f.read()))

    main(
        plot_file=args.out,
        datasets=datasets,
        minimum=args.min,
        maximum=args.max,
        exclude_crashes=args.exclude_crashes,
    )
