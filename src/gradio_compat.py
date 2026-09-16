"""gradio_client compatibility shim for upstream bug #11722.

`gradio_client.utils.json_schema_to_python_type` crashes with
``TypeError: argument of type 'bool' is not iterable`` when a component's schema
carries canonical JSON-Schema boolean ``additionalProperties`` (e.g. the
``Meta``/``FileData`` wrapper that ``gr.File`` / ``gr.Audio`` emit). The
unconditional ``if "const" in schema`` in ``get_type`` chokes on the bool.

Affects gradio 4.44.x / 5.1.0 with gradio_client 1.3.0.
Upstream: https://github.com/gradio-app/gradio/issues/11722

`apply()` installs a guarded monkeypatch on ``get_type`` that treats a boolean
schema as ``"boolean"``. It is a superset of the upstream behaviour: when
upstream ships the fix, the wrapper is a harmless no-op.
"""

from __future__ import annotations


def apply() -> None:
    """Idempotently patch gradio_client.utils.get_type to accept bool schemas."""
    import gradio_client.utils as _u

    _original = _u.get_type

    def get_type(schema):
        if isinstance(schema, bool):
            return "boolean"
        return _original(schema)

    if getattr(_original, "_xz_compat", False):
        return  # already applied
    get_type._xz_compat = True  # type: ignore[attr-defined]
    _u.get_type = get_type