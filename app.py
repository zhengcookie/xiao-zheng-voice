"""Xiao Zheng Voice — Gradio Web UI 入口。

第一版骨架：三个 Tab（上传音频 / 训练模型 / 合成语音）与工作空间状态栏。
各 Tab 的具体功能由后续票据逐步填充。

启动：
    python app.py
"""

from __future__ import annotations

import gradio as gr

from src import __version__
from src import uploader
from src.workspace import (
    MODELS_DIR,
    OUTPUTS_DIR,
    PROCESSED_DIR,
    UPLOADS_DIR,
    WORKSPACE_DIR,
    init_workspace,
    workspace_summary,
)

APP_TITLE = "🎙️ Xiao Zheng Voice — 声音克隆工具"
APP_DESCRIPTION = (
    "基于开源语音克隆技术，克隆身边人的声音。"
    "**仅供学习与个人使用，请勿用于商业用途。**"
)

TAB_UPLOAD = "🎤 上传音频"
TAB_TRAIN = "🏋️ 训练模型"
TAB_SYNTHESIZE = "🔊 合成语音"


def _workspace_overview() -> str:
    """渲染工作空间目录概览（Markdown 表格）。"""
    rows = [
        ("uploads", UPLOADS_DIR, "用户上传的原始音频"),
        ("processed", PROCESSED_DIR, "预处理后的音频"),
        ("models", MODELS_DIR, "训练好的模型"),
        ("outputs", OUTPUTS_DIR, "合成的音频输出"),
    ]
    lines = [
        f"**工作空间根目录**：`{WORKSPACE_DIR}`",
        "",
        "| 子目录 | 路径 | 用途 |",
        "| --- | --- | --- |",
    ]
    for name, path, purpose in rows:
        lines.append(f"| `{name}/` | `{path}` | {purpose} |")
    return "\n".join(lines)


def build_app() -> gr.Blocks:
    """构建 Gradio 应用（骨架）。"""
    init_workspace()

    with gr.Blocks(title=APP_TITLE, theme=gr.themes.Soft()) as demo:
        gr.Markdown(f"# {APP_TITLE}")
        gr.Markdown(APP_DESCRIPTION)

        with gr.Tabs():
            # ---- Tab 1: 上传音频 ----
            with gr.Tab(TAB_UPLOAD):
                gr.Markdown(
                    "### 上传目标人物的语音样本\n"
                    "支持拖拽上传 WAV / MP3 / FLAC，建议总时长 3–10 分钟的清晰语音。"
                )

                upload_box = gr.File(
                    label="语音样本（可拖拽 / 多选）",
                    file_count="multiple",
                    file_types=[".wav", ".mp3", ".flac"],
                    type="filepath",
                )
                status_box = gr.Textbox(label="上传状态", interactive=False)

                with gr.Row():
                    upload_btn = gr.Button("⬆️ 上传", variant="primary")
                    refresh_btn = gr.Button("🔄 重新扫描")

                files_table = gr.Dataframe(
                    headers=uploader.TABLE_HEADERS,
                    value=uploader.list_upload_rows(),
                    interactive=False,
                    row_count=8,
                )

                preview_label = gr.Dropdown(
                    label="选择文件预览波形",
                    choices=uploader.list_upload_names(),
                    interactive=True,
                )
                preview_player = gr.Audio(
                    label="波形预览",
                    type="filepath",
                    interactive=False,
                    show_download_button=True,
                )

                gr.Markdown(_workspace_overview())

                def _merge_rows(new_rows: list[list]) -> list[list]:
                    """把新上传行合并进磁盘现有行，按文件名去重。"""
                    merged = uploader.list_upload_rows()
                    seen = {r[0] for r in merged}
                    for r in new_rows:
                        if r[0] not in seen:
                            merged.append(r)
                            seen.add(r[0])
                    return merged

                def _do_upload(files):
                    new_rows, msg = uploader.process_uploaded_files(files)
                    rows = _merge_rows(new_rows)
                    names = uploader.list_upload_names()
                    preview = uploader.find_upload(names[-1]) if names else None
                    return (
                        rows,
                        msg or (f"已见 {len(rows)} 个文件" if rows else "未选择文件。"),
                        gr.Dropdown(choices=names, value=names[-1] if names else None),
                        preview,
                    )

                def _do_refresh():
                    rows = uploader.list_upload_rows()
                    names = uploader.list_upload_names()
                    status = f"已扫描到 {len(rows)} 个文件。" if rows else "上传目录为空。"
                    return rows, status, gr.Dropdown(choices=names), None

                def _do_preview(name):
                    return uploader.find_upload(name)

                upload_btn.click(
                    _do_upload,
                    inputs=[upload_box],
                    outputs=[files_table, status_box, preview_label, preview_player],
                )
                refresh_btn.click(
                    _do_refresh,
                    outputs=[files_table, status_box, preview_label, preview_player],
                )
                preview_label.change(
                    _do_preview, inputs=[preview_label], outputs=[preview_player]
                )

            # ---- Tab 2: 训练模型 ----
            with gr.Tab(TAB_TRAIN):
                gr.Markdown(
                    "### 用上传的音频训练声音模型\n"
                    "训练在后台运行，可实时查看进度与日志，并支持中途取消。"
                )
                gr.Markdown(
                    "> ⏳ 训练启动、进度轮询与日志输出将在后续版本中提供。"
                )

            # ---- Tab 3: 合成语音 ----
            with gr.Tab(TAB_SYNTHESIZE):
                gr.Markdown(
                    "### 输入文本，用克隆的声音朗读\n"
                    "选择已训练的模型，输入文本即可生成语音并下载。"
                )
                gr.Markdown(
                    "> ⏳ 模型选择、语音合成与播放下载将在后续版本中提供。"
                )

        gr.Markdown("---")
        gr.Markdown(f"{workspace_summary()}　·　v{__version__}")

    return demo


def main() -> None:
    """初始化工作空间并启动服务。"""
    demo = build_app()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )


if __name__ == "__main__":
    main()
