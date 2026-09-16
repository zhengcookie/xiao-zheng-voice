"""骨架冒烟测试：不启动服务器，验证应用可构建、Tab 齐全、工作空间就绪。

用法：
    python scripts/smoke_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# 允许从项目根目录导入 src / app
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Windows 控制台默认 GBK，无法输出 emoji，这里强制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    failures: list[str] = []

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
    found_tabs = {
        comp.get("props", {}).get("label", "")
        for comp in components
        if comp.get("type") == "tab"
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
