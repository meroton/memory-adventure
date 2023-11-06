Memory Adventure
~~~~~~~~~~~~~~~~

This is the home of the analysis code developed for our `Bazelcon 2023 talk`_
and further development.

.. TODO: Add link when it is available.

Background
==========

We want to find allocations from crashed Bazel builds,
some Starlark code somewhere is eating too much memory.
Most of the built-in tools provide post-hoc analysis
that require the Bazel server to survive, we can then dig into its data structures.
But if it crashes, all the data is torn down and we have very little to work with.

Reproduction: Memory eater
--------------------------

This project contains a small reproduction of pathological memory allocation,
in a convoluted build tree.
There is an aspect ``./memory/eat.bzl`` to consume large quantities of RAM,
and a set of rules ``./cpu/rules.bzl`` that perform innocuous CPU work, with bounded allocations,

.. _memory-bound aspect:

The memory eater aspect encodes the full dependency tree of all targets,
providers and all, with many small strings that are concatenated.
The big string is then tied to an ``Action`` object with ``ctx.actions.write``.
So this string can not be freed until the action is executed.
This can be tuned based on the dependency tree height to allocate more and more memory,
but with this repository it is in the 200 - 500 MB range,
to make iteration faster.
We expect to find this as ``traverse_impl`` in the logs somewhere.

.. _CPU-bound rules:

And the CPU-bound rules are all the same,
just implemented with numbered functions,
to dilute their individual presence in the profiling logs.

Of course real code bases are much larger, and more annoying to analyze,
but we hope that this can serve as a jumping-off-point for a discussion.

Post-hoc analysis
-----------------

The first step when troubleshooting memory is to follow the `memory profiling guide`_,
which highlights ``bazel dump --rules``
this is often useful at indicating list errors,
where a depset can drastically improve memory requirements.
But we found that in this example it does not give the correct answer.

Then drill deeper with ``bazel dump --skylark_memory=memory.pprof``,
which writes the memory allocations to a ``pprof`` format file.
Using a java ``memory instrumenter`` which is explained in the `guide`_.

.. _guide: `memory profiling guide`_

.. note::

    The script ``benchmark-different-memory`` and ``$STARTUP_FLAGS`` are described below

::

    $ ./benchmark-different-memory manual/2023-10-30/ 10g 2
    # The dump is done within the script:
    # $ bazel $STARTUP_FLAGS --host_jvm_args=-Xmx"10g" dump --skylark_memory=manual/2023-10-30/10g-1/memory.pprof

    $ pprof manual/2023-10-30/10g-2/memory.pprof
    Main binary filename not available.
    Type: memory
    Time: Oct 30, 2023 at 12:16pm (CET)
    Entering interactive mode (type "help" for commands, "o" for options)
    (pprof) top
    Showing nodes accounting for 2816.70kB, 73.34% of 3840.68kB total
    Showing top 10 nodes out of 19
          flat  flat%   sum%        cum   cum%
         512kB 13.33% 13.33%      512kB 13.33%  impl2
      256.16kB  6.67% 20.00%   256.16kB  6.67%  traverse_impl
      256.11kB  6.67% 26.67%   256.11kB  6.67%  _add_linker_artifacts_output_groups
      256.09kB  6.67% 33.34%   256.09kB  6.67%  alias
      256.09kB  6.67% 40.00%   256.09kB  6.67%  rule
      256.08kB  6.67% 46.67%   256.08kB  6.67%  to_list
      256.06kB  6.67% 53.34%   256.06kB  6.67%  impl7
      256.04kB  6.67% 60.01%   256.04kB  6.67%  _is_stamping_enabled
      256.04kB  6.67% 66.67%   256.04kB  6.67%  impl18
      256.03kB  6.67% 73.34%   768.15kB 20.00%  cc_binary_impl

This looks good, and contains a lot of information,
but we are not able to find the real culprit.
The exponential string allocation of the memory eater aspect,
`traverse_impl`, shows up with modest allocation.
But the 17MB allocation is nowhere to be seen.

``impl4`` and ``spin10`` are two of the `CPU-bound rules`_.

To illustrate, using too little memory (200m)::

    $ ./benchmark-different-memory manual/2023-10-30/ 200m 1
    WARNING: Running Bazel server needs to be killed, because the startup options are different
    .
    Starting local Bazel server and connecting to it...
    INFO: Starting clean (this may take a while). Consider using --async if the clean takes more than several minutes.
    WARNING: Running Bazel server needs to be killed, because the startup options are different
    .
    Starting local Bazel server and connecting to it...
    INFO: Invocation ID: 72092cbf-edf1-45db-bb5b-29658e731d75
    Loading:
    Loading:
    Loading: 0 packages loaded
    Analyzing: 42 targets (8 packages loaded, 0 targets configured)
    Analyzing: 42 targets (51 packages loaded, 376 targets configured)
    FATAL: bazel ran out of memory and crashed. An attempt will be made to write a heap dump to
     /CAS/bazel-cache/38ee34394b564c6d0289781c6b6bf0c1/72092cbf-edf1-45db-bb5b-29658e731d75.heapdump.hprof.
    Printing stack trace:
    net.starlark.java.eval.Starlark$UncheckedEvalError: OutOfMemoryError thrown during Starlark
     evaluation (//cpu:lock_19)
            at <starlark>.write(<builtin>:0)
            at <starlark>.traverse_impl(/home/nils/task/meroton/basic-codegen/memory/eat.bzl:57
    )
    Caused by: java.lang.OutOfMemoryError: Java heap space

Fails for allocation errors in the aspect,
but we cannot dump the memory after Bazel crashed.

Analyze your own memory with this reproduction project
======================================================

Measurement Data
----------------

This requires Bazel's `profiling data`_ for multiple build with different memory limits.
Bazel's memory can be limited through the startup option::

    --export STARTUP_FLAGS \
        --host_jvm_args=-Xmx500m

And you want the allocation instrumenter, as is explained in the `memory profiling guide`_::

    set --export STARTUP_FLAGS \
        --host_jvm_args=-javaagent:java-allocation-instrumenter-3.3.0.jar \
        --host_jvm_args=-DRULE_MEMORY_TRACKER=1 \
        --host_jvm_args=-Xmx500m

.. _memory profiling guide: https://bazel.build/rules/performance#memory-profiling

Profiling data
--------------

To enable the profiling data add the following flags to your build
``--generate_json_trace_profile`` and ``--profile=<profile file>``,
for better fidelity we recommend ``--noslim_profile``, to avoid merging events,
which is faster but requires extra effort to parse.

You can also save the console output, the build event protocol (``--build_event_json_file``),
Starlark CPU pprof-profile (``--starlark_cpu_profile=<pprof file>``),
and heap (``--heap_dump_on_oom``). This will capture the most data for you,
so you can analyze it further after the fact.
There is certainly more signal to find in all this data than what we have today.

Sample benchmarking file
------------------------

You can start with ``benchmark-different-memory`` in this repository,
it is designed to make multiple attempts with different memory limits.

This contains a bunch of flags, first skymeld, nobuild, or just regular,
then the `profiling data`_ flags,
followed by remote execution to a local Buildbarn deployment
and finally our memory traversal aspect that we want to benchmark.
You probably want to split this up into multiple bash arrays or bazelrc configs.

Note that this does not set the ``STARTUP_FLAGS``,
you need to set that in your interactive terminal.

There is currently no way to change build mode (skymeld, nobuild) from the measurement driver.
You need to modify the file manually to change mode of operation,
but it is possible to add that the benchmarking script's API.

.. TODO: Setup "$@" to accept flags.

.. TODO: Set STARTUP_FLAGS in the script if they are missing.

Measurement driver
------------------

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

.. _hyperfine: https://github.com/sharkdp/hyperfine

Extract stats
-------------

We now have the measurements we need, and can begin analyzing them.
Here we split the path, first we will discuss the plots of build duration of this script,
then we will discuss `further analysis`_ you can do to find memory thieves,
which is not part of this program.

This program requires the duration and garbage collection count from a measurement.
The data is fed in one or two files (so you can cache the computation, see the `usage`_ section),
containing comma-separated (csv) data::

    <memory limit: <str>>,<iteration: int>,<gc count: int>,<duration: int>,<status: str: "crash"|"ok">


Plot the memory consumption
---------------------------

This can then be plotted with ``memory-plot.py``,
a tool that takes one or two data serieses, as described above.

.. _usage:

::

    # Generate the data, this takes a couple of seconds per build of this Bazel
    # workspace. So using 'tee' to cache the result speeds up iteration significantly.
    # This uses bash's pseudo file redirection <(...) for convenience,
    you can save the files directly if you want.
    $ ./memory-plot.py --out plot-combined.png \
        <(echo ./measurement-regular/*/ | xargs -n1 ./stats.sh | grep -v WARMUP | tee cache-regular) \
        <(echo ./measurement-skymeld/*/ | xargs -n1 ./stats.sh | grep -v WARMUP | tee cache-skymeld)

    # Iterate the plot on the same data.
    $ ./memory-plot.py [--out phase-regular.png] --exclude-crashes cache-regular

Further analysis
================

We think that the following data points are very interesting:

    1. The active functions at the time of a crash
    2. All functions in a successful build

These can be combined:

    1. The most commonly seen functions when Bazel crashes
    2. The most overrepresented functions when Bazel crashes,
       this requires the baseline distribution.

Additionally you can look at functions and correlate with GC events

    1. Number of time-adjusted GC events during evaluation of a function.

Or the number of restarts for a function:

    1. Additional restarts for each function in a low memory execution compared to high memory
    2. Correlation of restarts in other functions.
       Maybe a function causes other functions to restart,
       so see if a correlated, or concurrent measure of restarts can be bound to all active threads.

And much much more, please tell us your ideas.

Basic Analysis
--------------

Some basic measurements for memory pressure through garbage collection
were implemented in ``parse-profile.py`` as part of the exploratory work,
you can look at them, but we did not see any interesting signals.

Documentation for the example project itself
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    This is a forked from https://github.com/meroton/bazel-examples

Building
========

This project shows an example of a cc program that depends on generated code,
through a cc_library, that can optionally be statically linked.
And this has a rudimentary rule for that code generation.

There is also a linter aspect for the python code, that is configured with a toolchain.

::

    $ bazel query //... --output=maxrank
    0 //:Runner
    0 //:test
    0 //toolchain:ruff_toolchain
    0 //:Touch
    0 //config:ConfiguredBinary
    0 //toolchain:ruff
    0 //config:Runner
    0 //Parameters:filter
    1 //Library:Static
    1 //config:debug_build
    1 //toolchain:toolchain_type
    1 //:capture
    1 //config:opt_build
    2 //:Program
    3 //Library:Library
    4 //Parameters:Parameters
    5 //Parameters:Generate
    5 //config:config_file

The main points to build and run are ``//:Runner`` and ``//:Program``.
This compiles all the code and generated defines that are printed below::

    $ bazel run //:Program
    Target //:Program up-to-date:
      bazel-bin/Program
    Hello: Meroton 105%

    # There is also a python runner to execute the program
    bazel run //:Runner
    Target //:Runner up-to-date:
      bazel-bin/Runner
    Hello: Meroton 105%
    1: from
    2: python

The generated code is available here::

    $ bazel build //Parameters
    Target //Parameters:Parameters up-to-date:
      bazel-bin/Parameters/Parameters.h

    # This code generator is handled by a bazel rule
    $ bazel run //Parameters:Generate -- --help
    Target //Parameters:Generate up-to-date:
      bazel-bin/Parameters/Generate
    usage: Generate.py [-h] --output OUTPUT --base BASE inputs [inputs ...]
    ...

Query
=====

The basic use for query is to show what targets are available
and what kinds they are::

    $ bazel query //...
    $ bazel query --output=label_kind //...

And advanced use can show dependencies between targets
and limit scopes::

    # all dependencies within //Library/...
    $ bazel query 'deps(//:Runner) intersect //Library/...'
    $ bazel query --output=label_kind 'allpaths(//:Runner, //Parameters)'
    cc_binary rule //:Program
    py_binary rule //:Runner
    cc_library rule //Library:Library
    codegen rule //Parameters:Parameters

    # We also depend on the python code generation tool
    $ bazel query --output=label_kind 'allpaths(//:Runner, //Parameters:all)'
    ...
    py_binary rule //Parameters:Generate

    # But not if we disable implicit and tool dependencies (--notool_deps)
    # This is the same as the allpaths query.
    $ bazel query --output=label_kind --noimplicit_deps 'allpaths(//:Runner, //Parameters:all)'
    cc_binary rule //:Program
    py_binary rule //:Runner
    cc_library rule //Library:Library
    codegen rule //Parameters:Parameters


We can find targets expanded by macros, and filter based on the macro name
"generator_function" is the old name for "macro", some such old names leak through the Bazel abstractions.

If we had a "write_source_file" target and macro, this would show both a write and a test target.
You could add that for the reference output of ``//:Program``!
https://github.com/bazelbuild/bazel-skylib/blob/main/docs/write_file_doc.md

::

    $ bazel query 'attr(generator_function, diff_test, //:all)'
    _diff_test rule //:test

Macros can be expanded to see all the attributes,
compare this to what you see in the BUILD file.
There is also a stack trace with filepaths to open all relevant BUILD and .bzl files.::

    $ bazel query --output=build //:test
    # /home/nils/task/meroton/basic-codegen/BUILD.bazel:48:10
    _diff_test(
      name = "test",
      generator_name = "test",
      generator_function = "diff_test",
      generator_location = "/home/nils/task/meroton/basic-codegen/BUILD.bazel:48:10",
      file1 = "//:reference.txt",
      file2 = "//:capture",
      is_windows = select({"@bazel_tools//src/conditions:host_windows": True, "//conditions:default": False}),
    )
    # Rule test instantiated at (most recent call last):
    #   /home/nils/task/meroton/basic-codegen/BUILD.bazel:48:10                                                               in <toplevel>
    #   /home/nils/.cache/bazel/_bazel_nils/38ee34394b564c6d0289781c6b6bf0c1/external/bazel_skylib/rules/diff_test.bzl:169:15 in diff_test
    # Rule _diff_test defined at (most recent call last):
    #   /home/nils/.cache/bazel/_bazel_nils/38ee34394b564c6d0289781c6b6bf0c1/external/bazel_skylib/rules/diff_test.bzl:140:18 in <toplevel>

    $ bazel query --output=build //:capture
    # /home/nils/task/meroton/basic-codegen/BUILD.bazel:39:8
    genrule(
      name = "capture",
      tools = ["//:Program"],
      outs = ["//:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"],
      cmd = "\n        ./$(location Program) > \"$@\"\n    ",
    )

We can also look for certain kinds of rules with the ``kind`` function: ``kind(<regexp>, <pattern>)``.::

    $ bazel query 'kind(config_setting, //...)'
    config_setting rule //config:debug_build
    config_setting rule //config:opt_build

Source files are also available, though they are not themselves part of the wildcard for ``//...``::

    $ bazel query --output=label 'kind("source file", deps(//...))' | grep '^//'
    //:Main.c
    //:reference.txt
    //:run.py
    //:touch.sh
    //Library:Library.c
    //Library:Library.h
    //Parameters:Generate.py
    //Parameters:Parameters.json
    //config:main.c
    //config:run.py

Without the ``grep`` we see source files from external repositories too!

External repositories
---------------------

Can be shown::

    bazel query //external:'*'

There are probably more than you thought, most of them are built in to Bazel,
and not actually used in this repository.
However, the real name ``@<repo>//...`` must be used to query for dependency paths.::

    $ bazel query 'allpaths(//..., //external:*)'
    INFO: Empty results

Cquery
======

Cquery is used to query the configured graph, where selects are followed.
So we only see dependencies for desired options and operating systems.
You can always query for a different operating system than your own,
just disable the auto-platform-configuration (if it is enabled),
it will automatically add --config=linux and so on.

    --noenable_platform_specific_config

Follow selects
--------------

We have a configured dependency in ``//config:ConfiguredBinary``.
With just query we see that it depends of both the regular and the statically linked library.::

    bazel query 'deps(//config:ConfiguredBinary, 1) intersect //Library:all'
    cc_library rule //Library:Library
    cc_static_library rule //Library:Static

But the ``config_setting`` are mutually exclusive, based on the ``--compilation_mode={fastbuild,opt,debug}`` value.
The flag is customarily used in its short form ``-c=<value>``, and ``fastbuild`` is the default.

bash ::

    $ diff \
        <(bazel cquery $TERSE -c fastbuild 'deps(//config:ConfiguredBinary, 1) intersect //Library:all') \
        <(bazel cquery -c opt 'deps(//config:ConfiguredBinary, 1) intersect //Library:all')
    1c1
    < //Library:Library (ca63adb)
    ---
    > //Library:Static (bfe6c4d)

This switch will also show up visually in the ``graph`` output format.

Graph
-----

Here is an example that shows the configuration of all targets in a graph.
We do some ``sed`` to make it look nicer.::

    $ bazel cquery                             \
        --notool_deps --noimplicit_deps        \
        'deps(//:Runner)' --output=graph       \
        | sed                                  \
            -e 's/(ca63adb)/(Generated)/g'     \
            -e 's/(null)/(Source)/g'           \
            -e '{/->/b; s/(Source)"/& [style=filled, fillcolor='lightgreen']/}'
    digraph mygraph {
      node [shape=box];
      "//:Runner (Generated)"
      "//:Runner (Generated)" -> "//:Program (Generated)"
      "//:Runner (Generated)" -> "//:run.py (Source)"
      "//:Runner (Generated)" -> "@rules_python//python/runfiles:runfiles (Generated)"
    ...

This can be rendered to an svg with ``graphviz`` and the ``dot`` program.

   $ bazel cquery ... | dot -Tsvg -o graph.svg

Config hash
-----------

In this example the config hash is "ca63adb", it may differ for you,
update the ``sed`` command accordingly.

    $ bazel cquery //:Runner
    //:Runner (ca63adb)

You can inspect this with ``bazel config`` to show platforms and many, many, more options.::

    $ bazel config ca63adb | head
    INFO: Displaying config with id ca63adb
    BuildConfigurationValue ca63adb307a1bd0f693440015ddae19ec8302707b6d51da41eab328714b1af2a:
    Skyframe Key: BuildConfigurationKey[ca63adb307a1bd0f693440015ddae19ec8302707b6d51da41eab328714b1af2a]
    ...

ST hash
-------

This example does not have any ST hashes, they stick out from config hashes, in that they have ``ST_`` in the middle.
Those are created by transitions that change the config of a target,
and cannot be printed directly with ``bazel config <ST hash>``.
You need their config hash, which can be found by calling ``bazel config`` without any arguments.::

    $ bazel config | grep <ST hash>

This will give you the config hash.

Providers and output groups
---------------------------

There is a cquery Starlark file in the project root ``output_groups.cquery``
that can be used to list all providers and output groups of a target.
And pretty-print some of them, you would typically create such pretty printers for all internal providers.
It helps a lot during rule development to inspect the rule outputs,
and keep that code out of the implementation.
To select the prints interactively rather than coding in print-statements.

It also servers as a basis for powerful shell completion tools.
This was used to develop the Codegen code,
see block comments in ``Parameters/BUILD.bazel`` and ``Parameters/Codegen.bzl``.

::

    $ bazel cquery --output=starlark --starlark:file=output_groups.cquery //:Program
    providers:
       - CcInfo
       - InstrumentedFilesInfo
       - DebugPackageInfo
       - CcLauncherInfo
       - RunEnvironmentInfo
       - FileProvider
       - FilesToRunProvider
       - OutputGroupInfo

    output_groups:
       - _hidden_top_level_INTERNAL_
       - _validation
       - compilation_outputs
       - compilation_prerequisites_INTERNAL_
       - temp_files_INTERNAL_
       - to_json
       - to_proto

    FileProvider:
       - bazel-out/k8-fastbuild/bin/Program

    FilesToRunProvider:
       - bazel-out/k8-fastbuild/bin/Program
       - bazel-out/k8-fastbuild/bin/Program.runfiles/MANIFEST

    $ bazel cquery --output=starlark --starlark:file=output_groups.cquery //:Runner
    INFO: Analyzed target //:Runner (1 packages loaded, 12 targets configured).
    INFO: Found 1 target...
    providers:
       - PyInfo
       - PyRuntimeInfo
       - InstrumentedFilesInfo
       - PyCcLinkParamsProvider
       - FileProvider
       - FilesToRunProvider
       - OutputGroupInfo

    output_groups:
       - _hidden_top_level_INTERNAL_
       - compilation_outputs
       - compilation_prerequisites_INTERNAL_
       - python_zip_file
       - to_json
       - to_proto

    FileProvider:
       - run.py
       - bazel-out/k8-fastbuild/bin/Runner

    FilesToRunProvider:
       - bazel-out/k8-fastbuild/bin/Runner
       - bazel-out/k8-fastbuild/bin/Runner.runfiles/MANIFEST

Here is a side-by-side that may be useful::

    providers:                                                   ┃  providers:
       - *Py*Info                                                ┃     - *Cc*Info
       - PyRuntimeInfo                                           ┃  ------------------------------------------------------------
       - InstrumentedFilesInfo                                   ┃     - InstrumentedFilesInfo
       - *PyCcLinkParamsProvider*                                ┃     - *DebugPackageInfo*
    -------------------------------------------------------------┃     - CcLauncherInfo
    -------------------------------------------------------------┃     - RunEnvironmentInfo
       - FileProvider                                            ┃     - FileProvider
       - FilesToRunProvider                                      ┃     - FilesToRunProvider
       - OutputGroupInfo                                         ┃     - OutputGroupInfo
                                                                 ┃
    output_groups:                                               ┃  output_groups:
       - _hidden_top_level_INTERNAL_                             ┃     - _hidden_top_level_INTERNAL_
    -------------------------------------------------------------┃     - _validation
       - compilation_outputs                                     ┃     - compilation_outputs
       - compilation_prerequisites_INTERNAL_                     ┃     - compilation_prerequisites_INTERNAL_
       - *python_zip_file*                                       ┃     - *temp_files_INTERNAL_*
       - to_json                                                 ┃     - to_json
       - to_proto                                                ┃     - to_proto
                                                                 ┃
    FileProvider:                                                ┃  FileProvider:
       - *run.py*                                                ┃     - *bazel-out/k8-fastbuild/bin/Program*
       - bazel-out/k8-fastbuild/bin/Runner                       ┃  ------------------------------------------------------------
                                                                 ┃
    FilesToRunProvider:                                          ┃  FilesToRunProvider:
       - bazel-out/k8-fastbuild/bin/*Runner*                     ┃     - bazel-out/k8-fastbuild/bin/*Program*
       - bazel-out/k8-fastbuild/bin/*Runner*.runfiles/MANIFEST   ┃     - bazel-out/k8-fastbuild/bin/*Program*.runfiles/MANIFEST


Pretty-print providers
++++++++++++++++++++++

This pretty-prints the custom ``ToolchainInfo`` providers from ``//toolchain:toolchain.bzl``::

    $ bazel cquery --output=starlark --starlark:file=output_groups.cquery //toolchain:ruff
    providers:
       - ToolchainInfo
       - FileProvider
       - FilesToRunProvider
       - OutputGroupInfo

    ...

    ToolchainInfo:
       - info.tool: bazel-out/k8-opt-exec-2B5CBBC6/bin/external/bin/ruff

Any provider can be printed.
One tip is to check for struct-members with ``dir(<some struct>)``, so you know what can be dereferenced,
when writing the pretty-printing code.


Aquery
======

To show actions and their command lines use ``aquery``.
You can see a summary of what will be done::

    $ bazel aquery --output=summary //...
    47 total actions.

    Mnemonics:
      CcStrip: 1
      TestRunner: 1
      SolibSymlink: 1
      ArMerge: 1
      CppArchive: 1
      Genrule: 1
      ExecutableSymlink: 1
      GenerateParameters: 1
      CppLink: 2
      CppCompile: 2
      PythonZipper: 3
      FileWrite: 6
      TemplateExpand: 6
      SymlinkTree: 6
      SourceSymlinkManifest: 6
      Middleman: 8

    Configurations:
      k8-fastbuild: 47

    Execution Platforms:
      @local_config_platform//:host: 47


And dig into a specific target::

    $ bazel aquery //Parameters:Parameters
    action 'GenerateParameters Parameters/Parameters.h'
      Mnemonic: GenerateParameters
      Target: //Parameters:Parameters
      Configuration: k8-fastbuild
      Execution platform: @local_config_platform//:host
      ActionKey: 1a618927f613610aaa53e7e0d055f716011b7552e900ac3a8e20058108276ef0
      Inputs: [Parameters/Generate.py, Parameters/Parameters.json, bazel-out/k8-opt-exec-2B5CBBC6/bin/Parameters/Generate, bazel-out/k8-opt-exec-2B5CBBC6/internal/_middlemen/Parameters_SGenerate-runfiles, config/config.json]
      Outputs: [bazel-out/k8-fastbuild/bin/Parameters/Parameters.h]
      Command Line: (exec bazel-out/k8-opt-exec-2B5CBBC6/bin/Parameters/Generate \
        --base \
        config/config.json \
        --output \
        bazel-out/k8-fastbuild/bin/Parameters/Parameters.h \
        Parameters/Parameters.json)
    # Configuration: ca63adb307a1bd0f693440015ddae19ec8302707b6d51da41eab328714b1af2a
    # Execution platform: @local_config_platform//:host

Configuration Examples
======================

Select
------

There is an example ``cc_binary`` with a ``select`` statement,
used to illustrate how ``cquery`` can help understanding dependencies,
see `Follow selects`_.

Label Flag
----------

A contrived example is written, and developed through the commit history
to show how a ``label_flag`` can be used to add configuration to a rule.
It will be used by the tool, but belongs to the rule as we will see below.
This is good for ad-hoc selection, that does not belong to any well defined ``config_settings``.
Config files for tools that do not encode platform information is a good example.
But there is a big area where ``select`` and ``label_flags`` can be used to solve the same problem.

Runfile to a binary
+++++++++++++++++++

We see that it does not work well for a ``py_binary`` to use it as a data dependency,
as we do not know what *file* to look for within the runfiles.
This is done in the config directory, there is a Runner but it does not work.
Try it for yourself with ``bazel run //config:Runner``.

::

    $ bazel query --output=build //config:Runner
    # .../config/BUILD.bazel:27:10
    py_binary(
      name = "Runner",
      deps = ["@rules_python//python/runfiles:runfiles"],
      data = ["//config:config_file"],
      main = "//config:run.py",
      srcs = ["//config:run.py"],
      args = [":config_file"],
    )

The ``args`` here cannot tell the program which file to look for,
it just gets the label for the flag,
not of the real target we attempt to use.

Next, we attempt to implement it into the rule, where we can access the ``File`` object
and find its path, even if it is changed on the command line.
But we still cannot find it as a runfile::

    $ bazel build //Parameters  # Output is redacted slightly
    ERROR: /home/nils/task/meroton/basic-codegen/Parameters/BUILD.bazel:10:8: GenerateParameters Parameters/Parameters.h failed: (Exit 1): Generate failed: error executing command (from target //Parameters:Parameters) bazel-out/k8-opt-exec-2B5CBBC6/bin/Parameters/Generate --base config/config.json --output bazel-out/k8-fastbuild/bin/Parameters/Parameters.h Parameters/Parameters.json
    Use --sandbox_debug to see verbose messages from the sandbox and retain the sandbox build root for debugging

    lookup: config/config.json
    found: /home/nils/.cache/bazel/_bazel_nils/38ee34394b564c6d0289781c6b6bf0c1/sandbox/linux-sandbox/20/execroot/example/bazel-out/k8-opt-exec-2B5CBBC6/bin/Parameters/Generate.runfiles/config/config.json

    Traceback (most recent call last):
      File "/home/nils/.cache/bazel/_bazel_nils/38ee34394b564c6d0289781c6b6bf0c1/sandbox/linux-sandbox/20/execroot/example/bazel-out/k8-opt-exec-2B5CBBC6/bin/Parameters/Generate.runfiles/example/Parameters/Generate.py", line 59, in <module>
        main(sys.argv[0], sys.argv[1:])
      File "/home/nils/.cache/bazel/_bazel_nils/38ee34394b564c6d0289781c6b6bf0c1/sandbox/linux-sandbox/20/execroot/example/bazel-out/k8-opt-exec-2B5CBBC6/bin/Parameters/Generate.runfiles/example/Parameters/Generate.py", line 37, in main
        with open(input, 'r') as f:
    FileNotFoundError: [Errno 2] No such file or directory: '/home/nils/.cache/bazel/_bazel_nils/38ee34394b564c6d0289781c6b6bf0c1/sandbox/linux-sandbox/20/execroot/example/bazel-out/k8-opt-exec-2B5CBBC6/bin/Parameters/Generate.runfiles/config/config.json'

Runfiles
++++++++

This illustrates some points, we did "find" the runfile, with the library.
But that file could not be opened, and the action failed.
That is because this is not actually a runfile to the program
//Generate:Generate does not have a data attribute,
we depend on it through the rule.
So we do not need the runfile library at all.
This is just a matter for the Starlark implementation and the action to resolve.

But we see that the runfile library does not know whether a file exists or not,
and its construction of the path is purely mechanical.
Runfiles do not work so well if the files are expected to change,
but static file names can be given as args, as we saw in //Config:Runner.

Just a regular input to the action
++++++++++++++++++++++++++++++++++

We just keep it simple, we do not need the runfiles library here.
As the config does not belong to the tool,
it could do so, and then not be an attribute of the rule,
but only the rule has the capability to look at the File object and its path.

Note, the base config file is de facto an input like all the others,
and could potentially be sent as a positional argument for the same effect.
But this shows the structure better.

::

    $ bazel build //Parameters  # Output is redacted slightly
    Target //Parameters:Parameters up-to-date:
      bazel-bin/Parameters/Parameters.h
    $ cat bazel-bin/Parameters/Parameters.h
    /* Generated by /home/nils/.cache/bazel/_bazel_nils/38ee34394b564c6d0289781c6b6bf0c1/sandbox/linux-sandbox/25/execroot/example/bazel-out/k8-opt-exec-2B5CBBC6/bin/Parameters/Generate.runfiles/example/Parameters/Generate.py */
    #define MER_PERCENT 105
    #define key value

Change the program dependency to the statically linked program
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

You can add another label flag to switch between ``//Library:Library`` and ``//Library:Static``
on the command line rather than changing BUILD files::

    diff --git a/BUILD.bazel b/BUILD.bazel
    index 539518a..16faf0d 100644
    --- a/BUILD.bazel
    +++ b/BUILD.bazel
    @@ -6,7 +6,7 @@ cc_binary(
             "Main.c"
         ],
         deps = [
    -        "//Library:Library"
    +        "//Library:Static"
         ],
     )

Build a la carte
================

Some notes on build target selection.

``--build_manual_tests`` seems to actually add "manual" targets back into the build.
Even for build actions, so the flag does not have the best name.

By default they are not built::

    $ bazel build --show_result=1000 //:all 2>&1 | grep Touch
    $ bazel build --show_result=1000 --build_manual_tests //:all 2>&1 | grep Touch
    Target //:Touch up-to-date:
      bazel-bin/Touch

But they show up with ``--build_manual_tests``.

Manual tag
----------

Some test may be expensive to execute, so we tag it as manual to avoid execution.
Something, something about cloud billing.
But we want to lint the source code to avoid mistakes.
That is typically not possible with "manual" tags.

These targets are tagged "manual"::

    bazel query --output=label_kind 'attr(tags, manual, //...)'
    sh_binary rule //:Touch
    py_binary rule //Parameters:Generate
    toolchain rule //toolchain:ruff_toolchain

The linter example
++++++++++++++++++

If we make ``//Parameters:Generate`` manual it can not be linted through a wildcard,
even though its docstring is too long, we really want the first build to fail::

    $ bazel build --aspects //:ruff.bzl%ruff //Parameters:all
    INFO: Analyzed 2 targets (0 packages loaded, 0 targets configured).
    INFO: Found 2 targets...
    INFO: Elapsed time: 0.036s, Critical Path: 0.00s
    INFO: 1 process: 1 internal.
    INFO: Build completed successfully, 1 total action

    $ bazel build --aspects //:ruff.bzl%ruff //Parameters:Generate
    INFO: Analyzed target //Parameters:Generate (0 packages loaded, 0 targets configured).
    INFO: Found 1 target...
    ERROR: /home/nils/task/meroton/basic-codegen/Parameters/BUILD.bazel:3:10: Ruff Parameters/Generate.ruff failed: (Exit 1): Touch failed: error executing command (from target //Parameters:Generate) bazel-out/k8-opt-exec-2B5CBBC6/bin/Touch bazel-out/k8-fastbuild/bin/Parameters/Generate.ruff bazel-out/k8-opt-exec-2B5CBBC6/bin/external/bin/ruff check Parameters/Generate.py

    Use --sandbox_debug to see verbose messages from the sandbox and retain the sandbox build root for debugging
    Parameters/Generate.py:3:89: E501 Line too long (94 > 88 characters)
    Found 1 error.
    Aspect //:ruff.bzl%ruff of //Parameters:Generate failed to build
    Use --verbose_failures to see the command lines of failed build steps.
    INFO: Elapsed time: 0.047s, Critical Path: 0.01s
    INFO: 2 processes: 2 internal.
    FAILED: Build did NOT complete successfully

But with ``--build_manual_tests`` it does work.::

    $ bazel build --aspects //:ruff.bzl%ruff --build_manual_tests //Parameters:Generate
    INFO: Analyzed target //Parameters:Generate (0 packages loaded, 0 targets configured).
    INFO: Found 1 target...
    ERROR: /home/nils/task/meroton/basic-codegen/Parameters/BUILD.bazel:3:10: Ruff Parameters/Generate.ruff failed: (Exit 1): Touch failed: error executing command (from target //Parameters:Generate) bazel-out/k8-opt-exec-2B5CBBC6/bin/Touch bazel-out/k8-fastbuild/bin/Parameters/Generate.ruff bazel-out/k8-opt-exec-2B5CBBC6/bin/external/bin/ruff check Parameters/Generate.py

    Use --sandbox_debug to see verbose messages from the sandbox and retain the sandbox build root for debugging
    Parameters/Generate.py:3:89: E501 Line too long (94 > 88 characters)
    Found 1 error.
    Aspect //:ruff.bzl%ruff of //Parameters:Generate failed to build
    Use --verbose_failures to see the command lines of failed build steps.
    INFO: Elapsed time: 0.040s, Critical Path: 0.01s
    INFO: 2 processes: 2 internal.
    FAILED: Build did NOT complete successfully

So we can allow more use of "manual", and not be wary of them sink-holing all the targets.
But as we do enable them again in the BUILD phase, the reason why they should not still needs to be handled.
And that may well be a platform compatibility issue that should be handled in the rule or with execution platforms.
So if your code based can use this flag it is okay to use "manual",
and then it only applies to *test* execution.
But if you need to remove targets from the build phase you need to express that differently.

Before this flag nothing could be done
++++++++++++++++++++++++++++++++++++++

Before ``--build_manual_tests`` was introduce there was no way to build manual targets through wildcards.
There is (still) a flag to filter and remove based on tags, and it can also add stuff back.
But anything tagged as manual can not be retrieved through ``--build_tag_filters``.
Neither of the following does anything::

    $ bazel build --aspects //:ruff.bzl%ruff --build_tag_filters=enable_again //Parameters:all
    $ bazel build --aspects //:ruff.bzl%ruff --build_tag_filters=+enable_again //Parameters:all
    $ bazel build --aspects //:ruff.bzl%ruff --build_tag_filters=manual //Parameters:all
    $ bazel build --aspects //:ruff.bzl%ruff --build_tag_filters=+manual //Parameters:all

The workaround then was to use a query, and xargs that to ``bazel build``.::

    bazel query //... | xargs bazel build

The targets are then all named will be built.

Rule Factory
============

Can be used to set default values for some attributes.
In ``//factory:factory.bzl`` we recreate the codegen rule.
But set its default value for base, this is a common pattern.

::

    bazel build //factory:test
    Target //factory:test up-to-date:
      bazel-bin/factory/test.h
    cat bazel-bin/factory/test.h
    /* Generated by /home/nils/.cache/bazel/_bazel_nils/38ee34394b564c6d0289781c6b6bf0c1/sandbox/linux-sandbox/2/execroot/example/bazel-out/k8-opt-exec-2B5CBBC6/bin/Parameters/Generate.runfiles/example/Parameters/Generate.py */
    #define a a
    #define base json

There are some things to note for introspection::

    bazel query --output=build //factory:test
    # /home/nils/task/meroton/basic-codegen/factory/BUILD.bazel:3:8
    codegen(
      name = "test",
      srcs = ["//factory:a.json"],
    )
    # Rule test instantiated at (most recent call last):
    #   /home/nils/task/meroton/basic-codegen/factory/BUILD.bazel:3:8 in <toplevel>
    # Rule codegen defined at (most recent call last):
    #   /home/nils/task/meroton/basic-codegen/factory/factory.bzl:51:15 in <toplevel>
    #   /home/nils/task/meroton/basic-codegen/factory/factory.bzl:9:16  in make

We see that there is an additional call to ``make`` in the stacktrace, good!
But the attribute for the base is completely hidden.

We can see it with special flags
--------------------------------

But that is annoying::

    $ bazel query --output=xml //factory:test | grep base.json
        <rule-input name="//factory:base.json"/>

... and with aquery of course.

We would prefer to show it
--------------------------

Let the users know what happens.
We would prefer to show it, but make it immutable.
But the classic default argument through a macro is not good,
because then it could be changed.

Can we make a macro factory?

Make a macro factory
--------------------

It is straight forward, the trick is to use a lambda for the macro inside the factory.
And we can now query again::

    bazel query --output=build //factory:test
    # /home/nils/task/meroton/basic-codegen/factory/BUILD.bazel:3:8
    _codegen(
      name = "test",
      visibility = ["//visibility:private"],
      tags = [],
      generator_name = "test",
      generator_function = "lambda",
      generator_location = "factory/BUILD.bazel:3:8",
      srcs = ["//factory:a.json"],
      base = "//factory:base.json",
    )
    # Rule test instantiated at (most recent call last):
    #   /home/nils/task/meroton/basic-codegen/factory/BUILD.bazel:3:8   in <toplevel>
    #   /home/nils/task/meroton/basic-codegen/factory/factory.bzl:29:97 in lambda
    # Rule _codegen defined at (most recent call last):
    #   /home/nils/task/meroton/basic-codegen/factory/factory.bzl:64:25 in <toplevel>
    #   /home/nils/task/meroton/basic-codegen/factory/factory.bzl:9:19  in make

It is a macro, with the name "lambda", oh well,
and the base is clearly visible.
But it is not an exported attribute and can not be modified in the BUILD file.

Nit: The rule name is stupid
----------------------------

This is an unfortunate consequence of the rule using whichever variable name it is assigned to,
and the macro must have its name.
And we often want them to be the same,
the easy way out is to add an underscore,
the more structured way is to hoist the rule to another file, "rule.bzl" or some such,
and have the macro load that.
The load statement can rename it.

::

    load(":rule.bzl", realrule = "rule")
    def rule(...):
        realrule(...)
