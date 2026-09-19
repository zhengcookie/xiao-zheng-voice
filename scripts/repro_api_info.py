"""Repro harness for `TypeError: argument of type 'bool' is not iterable`.

Drives the exact failing seam — gradio's `Blocks.get_api_info()`, which is where
`gradio.routes.api_info` calls `gradio_client.utils.json_schema_to_python_type`
and hits the bug (`if "const" in schema` on a bool).

Usage:
    .venv\\Scripts\\python scripts\\repro_api_info.py

Exit 0 + "OK"    -> get_api_info works (bug absent)
Exit 1 + "RED"   -> get_api_info raised the bug
Prints installed versions first so we can confirm what's actually in the venv.
"""

import os
import sys
import traceback

# The repo root must be importable first, then both ordering-sensitive shims must
# be applied before gradio/gradio_client are imported or used. See src/bootstrap.py.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from src import bootstrap  # noqa: E402

bootstrap.prepare()

import gradio as gr  # noqa: E402
import gradio_client  # noqa: E402


def main() -> int:
    print("python:", sys.version.split()[0])
    print("gradio:", gr.__version__)
    print("gradio_client:", gradio_client.__version__)

    from app import build_app  # exercises the real upload-tab components

    demo = build_app()
    try:
        demo.get_api_info()
    except Exception:
        print("\n--- traceback ---")
        traceback.print_exc()
        print("\nRED: get_api_info raised the bug")
        return 1

    print("\nOK: get_api_info succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())