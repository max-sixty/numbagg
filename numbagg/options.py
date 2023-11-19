import os

OPTIONS_DEFAULT = dict(
    use_cache=True,
    use_parallel=True,
)


def get_options() -> dict[str, object]:
    out: dict[str, object] = {}
    for k, v in OPTIONS_DEFAULT.items():
        if os.environ.get(f"NUMBAGG_{k.upper()}") is not None:
            out[k] = os.environ[f"NUMBAGG_{k.upper()}"]
        else:
            out[k] = v

    return out
