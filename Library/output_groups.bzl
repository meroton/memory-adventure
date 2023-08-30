"""Library pretty-printer for providers and output groups."""


LIST_SEP = "   - "
LINE_SEP = "\n" + LIST_SEP

def mapPath(x):
    if x == None:
        return "None"
    else:
        return x.path

def header(x):
    return "\n" + x + ":\n"


def format(target):
    if not OutputGroupInfo in target:
        return """{{
            data_runfiles: {},
            default_runfiles: {},
            files: {},
            files_to_run: {},
            label: {}
        }}""".format(
            getattr(target, "data_runfiles", "[]"),
            getattr(target, "default_runfiles", "[]"),
            getattr(target, "files", "[]"),
            getattr(target, "files_to_run", "[]"),
            getattr(target, "label", "''"),
        )

    output = target[OutputGroupInfo]

    output_groups = LIST_SEP + LINE_SEP.join(dir(output))

    res = "\n".join(["output_groups:", output_groups]) + "\n"

    for group in [
        "_hidden_top_level_INTERNAL_",
        "compilation_outputs",
        "compilation_prerequisites_INTERNAL_",
        "default",
        "python_zip_file",
        "to_json",
        "to_proto",
    ]:
        if group in output:
            res += header("OutputGroupInfo " + group)
            res += LIST_SEP + ", ".join([f.path for f in output[group].to_list()])
            res += "\n"

    return res
