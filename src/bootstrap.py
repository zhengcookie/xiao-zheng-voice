"""所有入口的第一件事：一次性应用两个**顺序敏感**的兼容垫片。

这两个补丁必须在特定时机生效，漏掉任何一个都会在离真正原因很远的地方炸掉：

1. ``proxy_compat`` —— 必须在 ``import gradio`` / ``import httpx`` **之前**。
   gradio 在导入期构造 ``httpx.Client(trust_env=True)``，本机代理工具导出的
   ``NO_PROXY=localhost,127.0.0.1,::1,[::1]`` 会让 httpx 抛
   ``InvalidURL: Invalid port: ':1]'``，整个导入直接失败。httpx 在自身导入时
   就绑定了 ``urllib.request.getproxies``，所以**事后打补丁无效**。

2. ``gradio_compat`` —— 必须在 ``gradio_client.utils.get_type`` 被调用之前。
   ``gr.File`` / ``gr.Audio`` 的 schema 里 ``additionalProperties`` 是布尔值，
   而 ``get_type`` 无条件执行 ``if "const" in schema`` →
   ``TypeError: argument of type 'bool' is not iterable``。这不只影响服务端的
   ``get_api_info()``；**任何用 gradio_client 连过来的进程（含 E2E 测试脚本）
   同样会中招**。

所以 ``prepare()`` 一次做完两件事，调用方只需要记住一条规则：
**先 ``prepare()``，再干别的。**

用法::

    from src import bootstrap

    bootstrap.prepare()          # <- 必须是最早的实质动作

    import gradio as gr                     # 之后随便什么时候导入都行
    from gradio_client import Client

``scripts/smoke_test.py`` 里有一条 AST 守卫，会静态检查所有入口（``app.py`` +
``scripts/*.py``）确实在 gradio 导入之前调用了 ``prepare()``，防止这个顺序
纪律再次悄悄失守。
"""

from __future__ import annotations


def prepare() -> None:
    """应用 NO_PROXY 净化 + gradio_client schema 垫片（幂等，可重复调用）。"""
    from . import proxy_compat

    # 必须最先执行：httpx 在导入期就读取 getproxies()。
    proxy_compat.apply()

    # gradio_client 会 import httpx —— 走到这里时 NO_PROXY 已净化，安全。
    from . import gradio_compat

    gradio_compat.apply()
