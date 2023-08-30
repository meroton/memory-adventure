"""Trick the Starlark evaluator garbage collector.

This aims to fool the CPU and RAM diagnostic tools
by using a lot of cpu,
while other threads allocate too much.
"""
load(":rules.bzl", "rules")

def target(index, **kwargs):
    rules[index](
        **kwargs
    )
