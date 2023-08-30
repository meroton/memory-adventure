"""Trick the Starlark evaluator garbage collector.

This means to fool the RAM diagnostic tools
by using a lot of memory in intermediate steps
but return from the rule with a small footprint.
"""

load("@example//Library:output_groups.bzl", "format")
load(":block.bzl", "block")
# load("@//Parameters:Codegen.bzl", "CodeGenInfo")

TraverseInfo = provider("content", fields = ["content"])
DoNotTraverseInfo = provider("marker", fields = ["marker"])

def traverse_impl(target, ctx):
    """allocation

    Args:
        target:
        ctx:
    Returns:
        OutputGroupInfo
    """
    name = ctx.rule.attr.name
    out = ctx.actions.declare_file(name + ".aspect.tree")

    per_dep = []
    providers = []
    # # target
    per_dep.append("{name}: {" + name + "}: " + format(target))
    # print(per_dep)

    # # transitive
    for attr in ["srcs", "data", "deps"]:
        for dep in getattr(ctx.rule.attr, attr, []):
            # print("appending", name, attr)
            per_dep.append(format(dep))
            if TraverseInfo in dep:
                # print("appending", name, attr, "Provider")
                providers.append(dep[TraverseInfo])

    # # join
    joined_providers = ""
    for p in providers:
        joined_providers += p.to_json()
    multiplicative = int(ctx.attr._multiplicative)
    content = ""
    for i in range(multiplicative):
        content += "{}: {}: {}\n".format(
        i,
        per_dep,
        joined_providers,
    )

    # # dump
    head = content # head = content[:1000]
    ctx.actions.write(
        output = out,
        content = head,
    )

    return [
        TraverseInfo(
            content = content,
        ),
        OutputGroupInfo(
            eat_memory = [out],
        ),
    ]

traverse = aspect(
    implementation = traverse_impl,
    # required_providers = [ # TODO: This breaks propagation over `attr_aspects` (we should look into why).
    #     [CcInfo],
    #     [PyInfo],
    #     [CodeGenInfo],
    # ],
    attr_aspects = ["*"],
    # provides = [TraverseInfo],
    attrs = {
        "_multiplicative": attr.string(default = "6"),
    }
)

def allocate_impl(target, ctx):
    """allocation

    Args:
        target:
        ctx:
    Returns:
        OutputGroupInfo
    """

    if DoNotTraverseInfo in target:
        return []

    name = ctx.rule.attr.name
    multiplicative = int(ctx.attr._multiplicative)

    out = ctx.actions.declare_file(name + ".allocate")
    allocation = block * multiplicative
    head = allocation[:100]

    ctx.actions.write(
        output = out,
        content = head,
    )

    return [
        OutputGroupInfo(
            allocate_memory = [out],
        ),
    ]

allocate = aspect(
    implementation = allocate_impl,
    attr_aspects = ["*"],
    attrs = {
        "_multiplicative": attr.string(default = "10000"),
    }
)

def _impl(ctx):
    name = ctx.attr.name
    out = ctx.actions.declare_file(name + ".tree")

    content = ctx.attr.srcs[0][TraverseInfo].to_json()

    ctx.actions.write(
        output = out,
        content = content,
    )

    return [
        OutputGroupInfo(
            default = [out],
        ),
    ]

eat = rule(
    implementation = _impl,
    attrs = {
        "srcs": attr.label_list(
            aspects = [traverse]
        ),
    },
)
