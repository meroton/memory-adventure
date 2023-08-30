Eat Memory
~~~~~~~~~~

OOM cases
=========

1: Fails to allocate during analysis

2: Fails to check cached actions, maybe the files themselves are too large.
   We can avoid this by limiting the file size.

Scenarios
=========

Multiplicative 100::

     10:20 m ██ ~/tas/mer/basic-codegen bazel $STARTUP_FLAGS build //... --aspects //memory:eat.bzl%traverse --output_groups=default,eat_memory --generate_json_trace_profile --profile=profile.gz --show_result=1000
    Analyzing: 16 targets (1 packages loaded, 1 target configured)
    FATAL: bazel ran out of memory and crashed. Printing stack trace:
    net.starlark.java.eval.Starlark$UncheckedEvalError: OutOfMemoryError thrown during Starlark evaluation (//memory:memory)
            at <starlark>.aspect_impl(/home/nils/task/meroton/basic-codegen/memory/eat.bzl:37)
    Caused by: java.lang.OutOfMemoryError: Overflow: String length out of range
            at java.base/java.lang.StringConcatHelper.checkOverflow(Unknown Source)
            at java.base/java.lang.StringConcatHelper.mixLen(Unknown Source)
            at net.starlark.java.eval.EvalUtils.binaryOp(EvalUtils.java:96)
            at net.starlark.java.eval.Eval.inplaceBinaryOp(Eval.java:470)
            at net.starlark.java.eval.Eval.execAugmentedAssignment(Eval.java:389)
            at net.starlark.java.eval.Eval.execAssignment(Eval.java:107)
            at net.starlark.java.eval.Eval.exec(Eval.java:268)
            at net.starlark.java.eval.Eval.execStatements(Eval.java:82)
            at net.starlark.java.eval.Eval.execFor(Eval.java:126)
            at net.starlark.java.eval.Eval.exec(Eval.java:276)
            at net.starlark.java.eval.Eval.execStatements(Eval.java:82)
            at net.starlark.java.eval.Eval.execFunctionBody(Eval.java:66)
            at net.starlark.java.eval.StarlarkFunction.fastcall(StarlarkFunction.java:173)
            at net.starlark.java.eval.Starlark.fastcall(Starlark.java:638)
            at com.google.devtools.build.lib.skyframe.StarlarkAspectFactory.create(StarlarkAspectFactory.java:65)
            at com.google.devtools.build.lib.analysis.ConfiguredTargetFactory.createAspect(ConfiguredTargetFactory.java:561)
            at com.google.devtools.build.lib.skyframe.AspectFunction.createAspect(AspectFunction.java:861)
            at com.google.devtools.build.lib.skyframe.AspectFunction.compute(AspectFunction.java:370)
            at com.google.devtools.build.skyframe.AbstractParallelEvaluator$Evaluate.run(AbstractParallelEvaluator.java:562)
            at com.google.devtools.build.lib.concurrent.AbstractQueueVisitor$WrappedRunnable.run(AbstractQueueVisitor.java:365)
            at java.base/java.util.concurrent.ForkJoinTask$RunnableExecuteAction.exec(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinTask.doExec(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinPool$WorkQueue.topLevelExec(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinPool.scan(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinPool.runWorker(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinWorkerThread.run(Unknown Source)

Multiplicative 30::

     10:21 m ██ ~/tas/mer/basic-codegen bazel $STARTUP_FLAGS build //... --aspects //memory:eat.bzl%traverse --output_groups=default,eat_memory --generate_json_trace_profile --profile=profile.gz --show_result=1000
    WARNING: Running Bazel server needs to be killed, because the startup options are different.
    Starting local Bazel server and connecting to it...
    INFO: Analyzed 16 targets (49 packages loaded, 461 targets configured).
    INFO: Found 16 targets...
    [48 / 49] checking cached actions
    FATAL: bazel crashed due to an internal error. Printing stack trace:
    java.lang.RuntimeException: Unrecoverable error while evaluating node 'ActionLookupData{actionLookupKey=[]#//memory:eat.bzl%traverse ConfiguredTargetKey{label=//memory:memory, config=BuildConfigurationKey[442d8db79c046018027f86fb6ba2e9e3560c56c0504c8b6423d08c7d06207c4d]} {}, actionIndex=0}' (requested by nodes 'AspectCompletionKey{topLevelArtifactContext=com.google.devtools.build.lib.analysis.TopLevelArtifactContext@9ecf540d, actionLookupKey=[]#//memory:eat.bzl%traverse ConfiguredTargetKey{label=//memory:memory, config=BuildConfigurationKey[442d8db79c046018027f86fb6ba2e9e3560c56c0504c8b6423d08c7d06207c4d]} {}}')
            at com.google.devtools.build.skyframe.AbstractParallelEvaluator$Evaluate.run(AbstractParallelEvaluator.java:633)
            at com.google.devtools.build.lib.concurrent.AbstractQueueVisitor$WrappedRunnable.run(AbstractQueueVisitor.java:365)
            at java.base/java.util.concurrent.ForkJoinTask$AdaptedRunnableAction.exec(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinTask.doExec(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinPool$WorkQueue.topLevelExec(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinPool.scan(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinPool.runWorker(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinWorkerThread.run(Unknown Source)
    Caused by: java.lang.IllegalStateException: failed to write string
            at com.google.devtools.build.lib.util.Fingerprint.addString(Fingerprint.java:239)
            at com.google.devtools.build.lib.analysis.actions.FileWriteAction.computeKey(FileWriteAction.java:251)
            at com.google.devtools.build.lib.actions.ActionKeyCacher.computeActionKey(ActionKeyCacher.java:64)
            at com.google.devtools.build.lib.actions.ActionKeyCacher.getKey(ActionKeyCacher.java:52)
            at com.google.devtools.build.lib.actions.ActionCacheChecker.mustExecute(ActionCacheChecker.java:543)
            at com.google.devtools.build.lib.actions.ActionCacheChecker.getTokenIfNeedToExecute(ActionCacheChecker.java:479)
            at com.google.devtools.build.lib.skyframe.SkyframeActionExecutor.checkActionCache(SkyframeActionExecutor.java:635)
            at com.google.devtools.build.lib.skyframe.ActionExecutionFunction.checkCacheAndExecuteIfNeeded(ActionExecutionFunction.java:757)
            at com.google.devtools.build.lib.skyframe.ActionExecutionFunction.computeInternal(ActionExecutionFunction.java:323)
            at com.google.devtools.build.lib.skyframe.ActionExecutionFunction.compute(ActionExecutionFunction.java:161)
            at com.google.devtools.build.skyframe.AbstractParallelEvaluator$Evaluate.run(AbstractParallelEvaluator.java:562)
            ... 7 more
    Caused by: com.google.protobuf.CodedOutputStream$OutOfSpaceException: CodedOutputStream was writing to a flat byte array and ran out of space.
            at com.google.protobuf.CodedOutputStream$OutputStreamEncoder.writeStringNoTag(CodedOutputStream.java:2963)
            at com.google.devtools.build.lib.util.Fingerprint.addString(Fingerprint.java:237)
            ... 17 more
    Caused by: java.lang.ArrayIndexOutOfBoundsException: Failed writing
     at index 1024
            at com.google.protobuf.Utf8$UnsafeProcessor.encodeUtf8(Utf8.java:1536)
            at com.google.protobuf.Utf8.encode(Utf8.java:293)
            at com.google.protobuf.CodedOutputStream$OutputStreamEncoder.writeStringNoTag(CodedOutputStream.java:2943)
            ... 18 more

Multiplicative 20::

    $ bazel $STARTUP_FLAGS build \
        --aspects //memory:eat.bzl%traverse \
        --output_groups=default,eat_memory \
        --generate_json_trace_profile --profile=profile.gz \
        //...

    $ bazel $STARTUP_FLAGS dump --rules
    ...
    ASPECT                          COUNT     ACTIONS          BYTES         EACH
    traverse                           62          58      2,553,336       41,182

    $ find bazel-bin/ -name '*.aspect.tree' | xargs du -h
    284K    bazel-bin/Parameters/filter.aspect.tree
    16K     bazel-bin/Parameters/lucas.aspect.tree
    16K     bazel-bin/Parameters/Parameters.aspect.tree
    9.7M    bazel-bin/Runner.aspect.tree
    648K    bazel-bin/config/Runner.aspect.tree
    440K    bazel-bin/config/ConfiguredBinary.aspect.tree
    4.0K    bazel-bin/toolchain/toolchain_type.aspect.tree
    4.0K    bazel-bin/toolchain/ruff.aspect.tree
    212M    bazel-bin/memory/memory.aspect.tree
    8.0K    bazel-bin/test.aspect.tree
    4.0K    bazel-bin/capture.aspect.tree
    440K    bazel-bin/Program.aspect.tree
    424K    bazel-bin/Library/Static.aspect.tree
    20K     bazel-bin/Library/Library.aspect.tree
    20K     bazel-bin/Library/naive_test.aspect.tree

Head 1000::

    $ bazel $STARTUP_FLAGS build //... --aspects //memory:eat.bzl%traverse --output_groups=default,eat_memory --generate_json_trace_profile --profile=profile.gz

    $ bazel $STARTUP_FLAGS dump --rules
    ...
    ASPECT                          COUNT     ACTIONS          BYTES         EACH
    traverse                           62          58              0            0

    $ find bazel-bin/ -name '*.aspect.tree' |
    xargs du -h
    4.0K    bazel-bin/Parameters/filter.aspect.tree
    4.0K    bazel-bin/Parameters/lucas.aspect.tree
    4.0K    bazel-bin/Parameters/Parameters.aspect.tree
    4.0K    bazel-bin/Runner.aspect.tree
    4.0K    bazel-bin/config/Runner.aspect.tree
    4.0K    bazel-bin/config/ConfiguredBinary.aspect.tree
    4.0K    bazel-bin/toolchain/toolchain_type.aspect.tree
    4.0K    bazel-bin/toolchain/ruff.aspect.tree
    4.0K    bazel-bin/memory/memory.aspect.tree
    4.0K    bazel-bin/test.aspect.tree
    4.0K    bazel-bin/capture.aspect.tree
    4.0K    bazel-bin/Program.aspect.tree
    4.0K    bazel-bin/Library/Static.aspect.tree
    4.0K    bazel-bin/Library/Library.aspect.tree
    4.0K    bazel-bin/Library/naive_test.aspect.tree

Tracing Execution
-----------------

In this synthetic repo the cause of OOM errors is evident in the trace,
as there is nothing else happening in other skylark evaluator threads.

Real world: llvm-project
------------------------

With multiplicative = 1.
It is still exponential

::

    ~/git/llv/uti/bazel $ bazel $STARTUP_FLAGS build @llvm-project//... --aspects @example//memory:eat.bzl%traverse --output_groups=default,eat_memory --generate_json_trace_profile --profile=profile.gz --override_repository example=~/task/meroton/basic-codegen/
    Analyzing: 4292 targets (94 packages loaded, 22476 targets configured)
    FATAL: bazel ran out of memory and crashed. Printing stack trace:
    net.starlark.java.eval.Starlark$UncheckedEvalError: OutOfMemoryError thrown during Starlark evaluation (@llvm-project//libc:cosf)
            at <starlark>.format(<builtin>:0)
            at <starlark>.aspect_impl(/home/nils/.cache/bazel/_bazel_nils/7e3bc6f480774551f13a2b92560b7cfa/external/example/memory/eat.bzl:37)
    Caused by: java.lang.OutOfMemoryError: Java heap space
            at java.base/java.util.Arrays.copyOf(Unknown Source)
            at java.base/java.lang.AbstractStringBuilder.ensureCapacityInternal(Unknown Source)
            at java.base/java.lang.AbstractStringBuilder.append(Unknown Source)
            at java.base/java.lang.StringBuilder.append(Unknown Source)
            at net.starlark.java.eval.FormatParser.format(FormatParser.java:65)
            at net.starlark.java.eval.StringModule.format(StringModule.java:975)
            at jdk.internal.reflect.GeneratedMethodAccessor8.invoke(Unknown Source)
            at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(Unknown Source)
            at java.base/java.lang.reflect.Method.invoke(Unknown Source)
            at net.starlark.java.eval.MethodDescriptor.call(MethodDescriptor.java:162)
            at net.starlark.java.eval.BuiltinFunction.fastcall(BuiltinFunction.java:77)
            at net.starlark.java.eval.Starlark.fastcall(Starlark.java:638)
            at net.starlark.java.eval.Eval.evalCall(Eval.java:682)
            at net.starlark.java.eval.Eval.eval(Eval.java:497)
            at net.starlark.java.eval.Eval.execAugmentedAssignment(Eval.java:386)
            at net.starlark.java.eval.Eval.execAssignment(Eval.java:107)
            at net.starlark.java.eval.Eval.exec(Eval.java:268)
            at net.starlark.java.eval.Eval.execStatements(Eval.java:82)
            at net.starlark.java.eval.Eval.execFor(Eval.java:126)
            at net.starlark.java.eval.Eval.exec(Eval.java:276)
            at net.starlark.java.eval.Eval.execStatements(Eval.java:82)
            at net.starlark.java.eval.Eval.execFunctionBody(Eval.java:66)
            at net.starlark.java.eval.StarlarkFunction.fastcall(StarlarkFunction.java:173)
            at net.starlark.java.eval.Starlark.fastcall(Starlark.java:638)
            at com.google.devtools.build.lib.skyframe.StarlarkAspectFactory.create(StarlarkAspectFactory.java:65)
            at com.google.devtools.build.lib.analysis.ConfiguredTargetFactory.createAspect(ConfiguredTargetFactory.java:561)
            at com.google.devtools.build.lib.skyframe.AspectFunction.createAspect(AspectFunction.java:861)
            at com.google.devtools.build.lib.skyframe.AspectFunction.compute(AspectFunction.java:370)
            at com.google.devtools.build.skyframe.AbstractParallelEvaluator$Evaluate.run(AbstractParallelEvaluator.java:571)
            at com.google.devtools.build.lib.concurrent.AbstractQueueVisitor$WrappedRunnable.run(AbstractQueueVisitor.java:382)
            at java.base/java.util.concurrent.ForkJoinTask$RunnableExecuteAction.exec(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinTask.doExec(Unknown Source)

But here too the tracing clearly shows what is up.
So we cannot have a cpu-heavy memory eater.
As the profiler clearly shows cpu eaters.


Multiplicative 30, no head, with 3gb limit::

    FATAL: bazel crashed due to an internal error. Printing stack trace:
    java.lang.RuntimeException: Unrecoverable error while evaluating node 'ActionLookupData{actionLookupKey=[]#//memory:eat.bzl%traverse ConfiguredTargetKey{label=//memory:memory, config=BuildConfigurationKey[442d8db79c046018027f86fb6ba2e9e3560c56c0504c8b6423d08c7d06207c4d]} {}, actionIndex=0}' (requested by nodes 'AspectCompletionKey{topLevelArtifactContext=com.google.devtools.build.lib.analysis.TopLevelArtifactContext@9a21d050, actionLookupKey=[]#//memory:eat.bzl%traverse ConfiguredTargetKey{label=//memory:memory, config=BuildConfigurationKey[442d8db79c046018027f86fb6ba2e9e3560c56c0504c8b6423d08c7d06207c4d]} {}}')
            at com.google.devtools.build.skyframe.AbstractParallelEvaluator$Evaluate.run(AbstractParallelEvaluator.java:633)
            at com.google.devtools.build.lib.concurrent.AbstractQueueVisitor$WrappedRunnable.run(AbstractQueueVisitor.java:365)
            at java.base/java.util.concurrent.ForkJoinTask$AdaptedRunnableAction.exec(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinTask.doExec(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinPool$WorkQueue.topLevelExec(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinPool.scan(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinPool.runWorker(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinWorkerThread.run(Unknown Source)
    Caused by: java.lang.IllegalStateException: failed to write string
            at com.google.devtools.build.lib.util.Fingerprint.addString(Fingerprint.java:239)
            at com.google.devtools.build.lib.analysis.actions.FileWriteAction.computeKey(FileWriteAction.java:251)
            at com.google.devtools.build.lib.actions.ActionKeyCacher.computeActionKey(ActionKeyCacher.java:64)
            at com.google.devtools.build.lib.actions.ActionKeyCacher.getKey(ActionKeyCacher.java:52)
            at com.google.devtools.build.lib.actions.ActionCacheChecker.mustExecute(ActionCacheChecker.java:543)
            at com.google.devtools.build.lib.actions.ActionCacheChecker.getTokenIfNeedToExecute(ActionCacheChecker.java:479)
            at com.google.devtools.build.lib.skyframe.SkyframeActionExecutor.checkActionCache(SkyframeActionExecutor.java:635)
            at com.google.devtools.build.lib.skyframe.ActionExecutionFunction.checkCacheAndExecuteIfNeeded(ActionExecutionFunction.java:757)
            at com.google.devtools.build.lib.skyframe.ActionExecutionFunction.computeInternal(ActionExecutionFunction.java:323)
            at com.google.devtools.build.lib.skyframe.ActionExecutionFunction.compute(ActionExecutionFunction.java:161)
            at com.google.devtools.build.skyframe.AbstractParallelEvaluator$Evaluate.run(AbstractParallelEvaluator.java:562)
            ... 7 more
    Caused by: com.google.protobuf.CodedOutputStream$OutOfSpaceException: CodedOutputStream was writing to a flat byte array and ran out of space.
            at com.google.protobuf.CodedOutputStream$OutputStreamEncoder.writeStringNoTag(CodedOutputStream.java:2963)
            at com.google.devtools.build.lib.util.Fingerprint.addString(Fingerprint.java:237)
            ... 17 more
    Caused by: java.lang.ArrayIndexOutOfBoundsException: Failed writing
     at index 1024
            at com.google.protobuf.Utf8$UnsafeProcessor.encodeUtf8(Utf8.java:1536)
            at com.google.protobuf.Utf8.encode(Utf8.java:293)
            at com.google.protobuf.CodedOutputStream$OutputStreamEncoder.writeStringNoTag(CodedOutputStream.java:2943)
            ... 18 more


TODO
====
Try to hide it with other cpu-intensive tasks
---------------------------------------------

We want a *straw that breaks the camel's back* situation
where other innocuous, moderately allocating, rules sometime tip the scale
and reach OOM.
But the lion share of allocations should come from one culprit.

And that culprit should not be obvious when profiling cpu use.

[ ]

Heatmap approach
----------------

Parse the profiling data and see which code is consistently involved in OOM scenarios.
It should still be visible with statistical analysis.

[ ]

Script
++++++

::


    $ bazel $STARTUP_FLAGS build \
    --generate_json_trace_profile --profile=profile.gz --show_result=100 \
    --aspects //memory:eat.bzl%traverse --aspects //cpu:spin.bzl%spinlock \
    --output_groups=default,eat_memory,allocate_memory,spinlock \
    //...
    WARNING: Running Bazel server needs to be killed, because the startup options are different.
    Starting local Bazel server and connecting to it...
    Analyzing: 16 targets (50 packages loaded, 461 targets configured)
    FATAL: bazel ran out of memory and crashed. Printing stack trace:
    net.starlark.java.eval.Starlark$UncheckedEvalError: OutOfMemoryError thrown during Starlark evaluation (//memory:memory)
            at <starlark>.traverse_impl(/home/nils/task/meroton/basic-codegen/memory/eat.bzl:713)
    Caused by: java.lang.OutOfMemoryError: Overflow: String length out of range
    ...

    $ acat profile.gz | jq '.traceEvents[] | select(.cat == "Starlark user function call") | .name' | sort | uniq -c
      2 "cc_binary"
      1 "cc_binary_impl"
      4 "_cc_library_impl"
      1 "_create_transitive_linking_actions"
      1 "_detect_java_version"
      8 "_impl"
      1 "_impl_rule"
      1 "_local_java_repository_impl"
      1 "_sh_config_impl"
     55 "spinlock_impl"
      8 "<toplevel>"
     10 "traverse_impl"

Good, we now have more spinlocks than the culprit.
And (rarely) is the spinlock the breaking straw::

    ...
    FATAL: bazel ran out of memory and crashed. Printing stack trace:
    net.starlark.java.eval.Starlark$UncheckedEvalError: OutOfMemoryError thrown during Starlark evaluation (//cpu:lock_85)
            at <starlark>.to_json(<builtin>:0)
            at <starlark>.traverse_impl(/home/nils/task/meroton/basic-codegen/memory/eat.bzl:709)
    Caused by: java.lang.OutOfMemoryError: Java heap space


All the spinlocks
-----------------

We have a factory that can create up to 70 spinlocks rules,
here just a few are used to limit wait times::

    bazel $STARTUP_FLAGS build \
                                            --generate_json_trace_profile --profile=profile.gz --show_result=100 \
                                            --aspects //memory:eat.bzl%traverse \
                                            --output_groups=default,eat_memory,allocate_memory,spinlock \
                                            //...
    WARNING: Running Bazel server needs to be killed, because the startup options are different.
    Starting local Bazel server and connecting to it...
    Analyzing: 20 targets (51 packages loaded, 467 targets configured)
    FATAL: bazel ran out of memory and crashed. Printing stack trace:
    net.starlark.java.eval.Starlark$UncheckedEvalError: OutOfMemoryError thrown during Starlark evaluation (//cpu:lock_2)
            at <starlark>.write(<builtin>:0)
            at <starlark>.traverse_impl(/home/nils/task/meroton/basic-codegen/memory/eat.bzl:722)
    Caused by: java.lang.OutOfMemoryError: Java heap space
            at java.base/java.io.ByteArrayOutputStream.<init>(Unknown Source)
            at com.google.devtools.build.lib.analysis.actions.FileWriteAction$CompressedString.<init>(FileWriteAction.java:175)
            at com.google.devtools.build.lib.analysis.actions.FileWriteAction.<init>(FileWriteAction.java:89)
            at com.google.devtools.build.lib.analysis.actions.FileWriteAction.create(FileWriteAction.java:162)
            at com.google.devtools.build.lib.analysis.starlark.StarlarkActionFactory.write(StarlarkActionFactory.java:346)
            at jdk.internal.reflect.GeneratedMethodAccessor167.invoke(Unknown Source)
            at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(Unknown Source)
            at java.base/java.lang.reflect.Method.invoke(Unknown Source)
            at net.starlark.java.eval.MethodDescriptor.call(MethodDescriptor.java:162)
            at net.starlark.java.eval.BuiltinFunction.fastcall(BuiltinFunction.java:77)
            at net.starlark.java.eval.Starlark.fastcall(Starlark.java:638)
            at net.starlark.java.eval.Eval.evalCall(Eval.java:682)
            at net.starlark.java.eval.Eval.eval(Eval.java:497)
            at net.starlark.java.eval.Eval.exec(Eval.java:271)
            at net.starlark.java.eval.Eval.execStatements(Eval.java:82)
            at net.starlark.java.eval.Eval.execFunctionBody(Eval.java:66)
            at net.starlark.java.eval.StarlarkFunction.fastcall(StarlarkFunction.java:173)
            at net.starlark.java.eval.Starlark.fastcall(Starlark.java:638)
            at com.google.devtools.build.lib.skyframe.StarlarkAspectFactory.create(StarlarkAspectFactory.java:65)
            at com.google.devtools.build.lib.analysis.ConfiguredTargetFactory.createAspect(ConfiguredTargetFactory.java:561)
            at com.google.devtools.build.lib.skyframe.AspectFunction.createAspect(AspectFunction.java:861)
            at com.google.devtools.build.lib.skyframe.AspectFunction.compute(AspectFunction.java:370)
            at com.google.devtools.build.skyframe.AbstractParallelEvaluator$Evaluate.run(AbstractParallelEvaluator.java:562)
            at com.google.devtools.build.lib.concurrent.AbstractQueueVisitor$WrappedRunnable.run(AbstractQueueVisitor.java:365)
            at java.base/java.util.concurrent.ForkJoinTask$RunnableExecuteAction.exec(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinTask.doExec(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinPool$WorkQueue.topLevelExec(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinPool.scan(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinPool.runWorker(Unknown Source)
            at java.base/java.util.concurrent.ForkJoinWorkerThread.run(Unknown Source)

    $ acat profile.gz | jq '.traceEvents[] | select(.cat == "Starlark user function call") | .name' | sort | uniq -c
      2 "cc_binary"
      1 "cc_binary_impl"
      1 "_create_transitive_linking_actions"
      1 "_detect_java_version"
      7 "_impl"
     93 "lambda"
      1 "_local_java_repository_impl"
      1 "_sh_config_impl"
     93 "spinlock_impl"
      4 "<toplevel>"
     15 "traverse_impl"

This is good, we now have more good citizens,
so the traverse aspect is hiding among more good people,
However we still share the implementation function.
Ideally we would have a bunch of numbers for spinlock here!

Argh::

    $ acat profile.gz | jq '.traceEvents[] | select(.cat == "Starlark user function call") | .name' | sort | uniq -c
      2 "cc_binary"
      1 "cc_binary_impl"
      1 "_create_transitive_linking_actions"
      1 "_detect_java_version"
      7 "_impl"
     93 "impl"
    186 "lambda"
      1 "_local_java_repository_impl"
      5 "<toplevel>"
      9 "traverse_impl"

We must give them real names.::

    $acat profile.gz | jq '.traceEvents[] | select(.cat == "Starlark user function call") | .name' | sort | uniq -c
          2 "cc_binary"
          1 "cc_binary_impl"
          1 "_create_transitive_linking_actions"
          1 "_detect_java_version"
          4 "end"
          7 "_impl"
         31 "impl2"
         31 "impl3"
         31 "impl4"
         93 "lambda"
          1 "_local_java_repository_impl"
          1 "_sh_config_impl"
          4 "<toplevel>"
          5 "traverse_impl"

limit memory to reach OOM faster
--------------------------------

[ ]

Other tools
===========

jmap histogram
--------------

63d24897933f954c753be1ae37e3c73bf17598cb
`jmap -histo`

Memory Analyzer
---------------

1 Take a heap dump
2 Check the "dominator tree"
