"""骨架冒烟测试：不启动服务器，验证应用可构建、Tab 齐全、工作空间就绪。

用法：
    python scripts/smoke_test.py
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# 允许从项目根目录导入 src / app
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Windows 控制台默认 GBK，无法输出 emoji，这里强制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 🔴 必须在任何 `import gradio` / `import httpx` 之前执行：这两个垫片都是顺序
# 敏感的（NO_PROXY 净化要在梯度库导入前，schema 垫片要在 gradio_client 使用前）。
# 之前这里漏了这一步，导致本脚本在装了 gradio 的真机上直接死于导入期。详见
# src/bootstrap.py。
from src import bootstrap  # noqa: E402

bootstrap.prepare()


def check_import_order() -> list[str]:
    """回归守卫：凡导入 gradio / gradio_client 的入口，必须先 ``bootstrap.prepare()``。

    这个顺序错误不会被任何纯逻辑单测发现，只会在装了 gradio 的真机上以
    ``httpx.InvalidURL: Invalid port: ':1]'``（NO_PROXY 里的 IPv6）或
    ``TypeError: argument of type 'bool' is not iterable``（gradio_client schema）
    的形式炸掉。本仓库的 ``smoke_test.py`` / ``repro_api_info.py`` 就因为漏了
    这一步静默坏掉过一整轮：用户拿到的每一条"验证命令"都会先死于导入，
    永远看不到绿灯。

    判定方式：静态解析 AST，比较"最早的 gradio/gradio_client 导入行"与
    "最早的 ``bootstrap.prepare()`` 调用行"。规范写法见 src/bootstrap.py。
    """
    problems: list[str] = []
    candidates = [PROJECT_ROOT / "app.py"]
    candidates += sorted((PROJECT_ROOT / "scripts").glob("*.py"))

    for path in candidates:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            problems.append(f"{path.name} 语法错误：{exc}")
            continue

        gradio_line: int | None = None
        prepare_line: int | None = None

        def _earliest(current: int | None, candidate: int) -> int:
            return candidate if current is None else min(current, candidate)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(a.name.split(".")[0] in ("gradio", "gradio_client") for a in node.names):
                    gradio_line = _earliest(gradio_line, node.lineno)
            elif isinstance(node, ast.ImportFrom):
                if (node.module or "").split(".")[0] in ("gradio", "gradio_client"):
                    gradio_line = _earliest(gradio_line, node.lineno)
            elif isinstance(node, ast.Call):
                func = node.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "prepare"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "bootstrap"
                ):
                    prepare_line = _earliest(prepare_line, node.lineno)

        if gradio_line is None:
            continue
        if prepare_line is None or prepare_line > gradio_line:
            where = prepare_line if prepare_line is not None else "缺失"
            problems.append(
                f"{path.relative_to(PROJECT_ROOT)}：第 {gradio_line} 行导入 gradio/gradio_client，"
                f"但 bootstrap.prepare() 在第 {where} 行（必须更早）"
            )
    return problems


def main() -> int:
    failures: list[str] = []

    # --- 0. 导入顺序守卫（回归：proxy_compat 必须先于 import gradio）---
    order_problems = check_import_order()
    failures.extend(order_problems)
    if order_problems:
        print(f"❌ 导入顺序守卫失败（{len(order_problems)} 处）")
    else:
        print("✅ 导入顺序守卫 OK（所有 gradio 入口均先应用 NO_PROXY 垫片）")

    # --- 1. 工作空间初始化 ---
    from src.workspace import WORKSPACE_SUBDIRS, init_workspace

    dirs = init_workspace()
    for key in ("root", "uploads", "processed", "models", "outputs"):
        if key not in dirs:
            failures.append(f"init_workspace() 缺少键：{key}")
    for directory in WORKSPACE_SUBDIRS:
        if not directory.is_dir():
            failures.append(f"目录未创建：{directory}")
    print(f"✅ 工作空间就绪：{dirs['root']}")

    # --- 2. 工具函数 ---
    from src.utils import format_duration, format_size, validate_audio_format

    checks = [
        (format_size(1536) == "1.5 KB", "format_size(1536)"),
        (format_duration(95) == "1:35", "format_duration(95)"),
        (validate_audio_format("a.wav")[0] is True, "validate .wav 应通过"),
        (validate_audio_format("a.txt")[0] is False, "validate .txt 应拒绝"),
    ]
    for ok, label in checks:
        if not ok:
            failures.append(f"工具函数断言失败：{label}")
    print(f"✅ 工具函数 OK（{len(checks)} 项断言）")

    # --- 2b. 代理兼容（httpx 在 NO_PROXY 含 IPv6 时导入崩溃的防护）---
    from src.proxy_compat import _parseable

    proxy_checks = [
        (_parseable("localhost"), "localhost 应保留"),
        (_parseable("127.0.0.1"), "127.0.0.1 应保留"),
        (not _parseable("[::1]"), "[::1] 应剔除"),
        (not _parseable("::1"), "::1 应剔除"),
    ]
    for ok, label in proxy_checks:
        if not ok:
            failures.append(f"代理兼容断言失败：{label}")
    print(f"✅ 代理兼容 OK（{len(proxy_checks)} 项断言）")

    # --- 3. Gradio 应用构建 ---
    try:
        import gradio as gr  # noqa: F401
    except ModuleNotFoundError:
        print("⚠️  未安装 gradio，跳过应用构建检查")
        print("    安装：python -m pip install -r requirements.txt")
        return 1 if failures else 0

    from app import TAB_SYNTHESIZE, TAB_TRAIN, TAB_UPLOAD, build_app

    demo = build_app()
    expected_tabs = {TAB_UPLOAD, TAB_TRAIN, TAB_SYNTHESIZE}
    components = demo.config.get("components", [])
    # gradio 4.44 的 Tab 组件 type 是 "tabitem"（<=4.43 才是 "tab"），两种都认。
    found_tabs = {
        comp.get("props", {}).get("label", "")
        for comp in components
        if comp.get("type") in ("tab", "tabitem")
    }
    missing = expected_tabs - found_tabs
    if missing:
        failures.append(f"缺少 Tab：{missing}")
    print(f"✅ 应用构建成功，Tab：{sorted(found_tabs)}")

    # --- 3b. Gradio API info 生成（回归：gradio_client bool-schema bug #11722）---
    try:
        demo.get_api_info()
        print("✅ get_api_info() 生成成功（File/Audio schema 兼容）")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"get_api_info() 失败：{exc!r}")

    # --- 结果 ---
    print()
    if failures:
        print("❌ 冒烟测试失败：")
        for item in failures:
            print(f"   - {item}")
        return 1

    print("✅ 冒烟测试全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
