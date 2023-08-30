FileCountInfo = provider(
    'count',
    fields = {
        'count' : 'number of files'
    }
)

def _file_count_aspect_impl(_, ctx):
    name = ctx.rule.attr.name
    count = 0
    # Make sure the rule has a srcs attribute.
    if hasattr(ctx.rule.attr, 'srcs'):
        # Iterate through the sources counting files
        for src in ctx.rule.attr.srcs:
            for _ in src.files.to_list():
                count = count + 1
    # Get the counts from our dependencies.
    for dep in ctx.rule.attr.deps:
        if FileCountInfo in dep:
            count = count + dep[FileCountInfo].count

    print(name, count)
    return [FileCountInfo(count = count)]

count = aspect(
    implementation = _file_count_aspect_impl,
    # required_providers = [
    #     [PyInfo],
    #     [FileCountInfo],
    # ],
    attr_aspects = ['deps'],
)
