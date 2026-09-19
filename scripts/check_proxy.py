"""Diagnose the httpx.InvalidURL proxy crash at `import gradio`.

Gradio builds an httpx.Client(trust_env=True) at import time, so a malformed
proxy setting makes the import fail with:
    httpx.InvalidURL: Invalid port: ':1]'

This prints every proxy source so we can see the offending value.

Usage:
    .venv\\Scripts\\python scripts\\check_proxy.py
"""

import os
import urllib.request


def main() -> int:
    print("== proxy environment variables ==")
    found = False
    for key, value in sorted(os.environ.items()):
        if "proxy" in key.lower():
            found = True
            print(f"  {key} = {value!r}")
    if not found:
        print("  (none set)")

    print("\n== urllib.request.getproxies()  (what httpx reads) ==")
    try:
        print(" ", urllib.request.getproxies())
    except Exception as exc:  # noqa: BLE001
        print("  raised:", type(exc).__name__, exc)

    print("\n== Windows registry proxy (HKCU Internet Settings) ==")
    try:
        import winreg

        path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            for name in ("ProxyEnable", "ProxyServer", "ProxyOverride"):
                try:
                    print(f"  {name} = {winreg.QueryValueEx(key, name)[0]!r}")
                except FileNotFoundError:
                    print(f"  {name} = (absent)")
    except Exception as exc:  # noqa: BLE001
        print("  (could not read registry:", type(exc).__name__, exc, ")")

    print("\n== httpx client construction (the failing call) ==")
    try:
        import httpx

        print("  httpx version:", httpx.__version__)
        client = httpx.Client()
        client.close()
        print("  OK: httpx.Client() constructed")
        return 0
    except Exception as exc:  # noqa: BLE001
        print("  RED:", type(exc).__name__, exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())