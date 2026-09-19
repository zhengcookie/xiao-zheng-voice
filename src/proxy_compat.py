"""Sanitize proxy settings that break gradio's httpx client at import time.

`gradio.processing_utils` builds ``httpx.Client(trust_env=True)`` while being
imported, so httpx expands every ``NO_PROXY`` entry into an ``all://<entry>``
URL pattern. Local proxy tools (Clash / Mihomo / Clash Verge and friends)
commonly export:

    NO_PROXY=localhost,127.0.0.1,::1,[::1]

and httpx mis-parses the IPv6 literals as a port:

    httpx.InvalidURL: Invalid port: ':1]'    # httpx >= 0.28, from "[::1]"
    httpx.InvalidURL: Invalid port: ':1'     # httpx <  0.28, from "::1"

That exception aborts ``import gradio`` outright, so the app never starts.

``apply()`` drops only the ``NO_PROXY`` entries the *installed* httpx cannot
parse. Valid proxies (``HTTP_PROXY`` / ``HTTPS_PROXY`` / ``ALL_PROXY``) are left
untouched, so model downloads through a proxy still work.

IMPORTANT: call this before ``import gradio`` / ``import httpx`` — httpx binds
``from urllib.request import getproxies`` at its own import time, so a later
patch would have no effect.
"""

from __future__ import annotations


def apply() -> None:
    """Idempotently wrap ``urllib.request.getproxies`` to drop bad NO_PROXY entries."""
    import urllib.request as _ur

    original = _ur.getproxies
    if getattr(original, "_xz_sanitized", False):
        return  # already applied

    def getproxies():
        proxies = dict(original())
        no_proxy = proxies.get("no")
        if no_proxy:
            proxies["no"] = ",".join(_keep_parseable(no_proxy))
        return proxies

    getproxies._xz_sanitized = True  # type: ignore[attr-defined]
    _ur.getproxies = getproxies


def _keep_parseable(value: str) -> list[str]:
    kept: list[str] = []
    for entry in value.split(","):
        entry = entry.strip()
        if entry and _parseable(entry):
            kept.append(entry)
    return kept


def _parseable(entry: str) -> bool:
    """True when httpx can build its ``all://[*]<entry>`` pattern without raising.

    httpx turns each NO_PROXY entry into a ``URLPattern`` key, sometimes with a
    ``*`` prefix (e.g. ``[::1]`` becomes ``all://*[::1]``). IPv6 literals are the
    entries that mis-split into a bogus port, so reject them up front and then
    double-check the real pattern shapes when the installed httpx exposes
    ``URLPattern``.
    """
    # IPv6 literals: bracketed "[::1]" and bare "::1" both break httpx's parser.
    if "[" in entry or "]" in entry or entry.count(":") > 1:
        return False

    try:
        from httpx._utils import URLPattern
    except Exception:  # noqa: BLE001 - cannot validate; keep the non-IPv6 entry
        return True

    for pattern in (f"all://{entry}", f"all://*{entry}"):
        try:
            URLPattern(pattern)
        except Exception:  # noqa: BLE001
            return False
    return True