"""Implementation to avoid cycles."""

load("@example//memory:eat.bzl", "DoNotTraverseInfo")

step = 1 * 1e6
MULTIPLICATIVE = 1

def start(ctx, index):
    name = ctx.rule.attr.name
    out = ctx.actions.declare_file(name + "{}.spinlock".format(index))
    other_out = ctx.actions.declare_file(name +"{}.allocation".format(index))
    count = int(ctx.attr._count)

    # # transitive
    providers = []
    for attr in ["srcs", "data", "deps"]:
        for dep in getattr(ctx.rule.attr, attr, []):
            if OutputGroupInfo in dep:
                providers.append(dep[OutputGroupInfo].spinlock)

    return out, other_out, count, providers

def end(ctx, number, out, other_out, providers, output):
    # # join
    joined_providers = ""
    for p in providers:
        joined_providers += p.to_list()[0].path
    content = ""
    for _ in range(MULTIPLICATIVE):
        content += "{}: {}\n".format(
            output,
            joined_providers,
        )

    # # dump Starlark content
    ctx.actions.write(
        output = out,
        content = content,
    )

    # # run an allocating program
    ctx.actions.run(
        outputs = [other_out],
        mnemonic = "Allocate",
        executable = ctx.executable._allocate,
        arguments = [other_out.path, "{}".format(number)],
        execution_requirements = {
            "no-cache": "1",
        },
    )

    return [
        DoNotTraverseInfo(),
        OutputGroupInfo(
            spinlock = [out, other_out],
        ),
    ]

def spinlock_rule_impl(ctx):
    out = ctx.attr.srcs[0][OutputGroupInfo].spinlock

    return [
        OutputGroupInfo(
            default = out,
        ),
    ]
