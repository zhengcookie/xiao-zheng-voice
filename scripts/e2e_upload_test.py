"""票据 #6 的端到端验证：真起一个服务，用 gradio_client 驱动上传 Tab 的交互。

冒烟测试（``smoke_test.py``）只证明"应用能构建"；本脚本补上缺失的那一层——
**真的发 HTTP 请求、真的上传文件、真的读回列表**，逐条对照 #6 的验收标准。

覆盖：
  1. 上传 .wav → 列表出现该文件，含 名称/时长/大小/格式/状态
  2. 上传 .txt → 被拒绝，状态栏出现「仅支持 WAV / MP3 / FLAC」
  3. 下拉框选文件 → 预览端点返回可播放的真实文件路径
  4. 上传 <3s 的短音频 → 状态标记「过短(<3s)」

用法::

    .venv\\Scripts\\python scripts\\e2e_upload_test.py

脚本自己在一个**空闲端口**起服务（不碰 7860，那是用户自己开的实例），
跑完自动关掉。子进程是全新解释器，因此顺带回归验证了 ``bootstrap.prepare()``
的导入顺序（漏掉它会在子进程启动期就炸）。

测试只动 ``workspace/uploads/``：跑完会删掉自己新建的文件，保留用户原有的上传。
"""

from __future__ import annotations

import argparse
import math
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Windows 控制台默认 GBK，无法输出 emoji/中文，这里强制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 临时产物放仓库内（已 gitignore）。系统 %TEMP% 在受限沙箱里不可写。
TMP_ROOT = PROJECT_ROOT / ".tmp" / "e2e"

# 🔴 顺序敏感：必须在 import gradio / gradio_client 之前。详见 src/bootstrap.py。
from src import bootstrap  # noqa: E402

bootstrap.prepare()

from src.workspace import UPLOADS_DIR  # noqa: E402

LONG_NAME = "e2e_long.wav"
SHORT_NAME = "e2e_short.wav"
BAD_NAME = "e2e_bad.txt"


# --------------------------------------------------------------------------- #
# 服务端模式（由父进程以子进程方式拉起）
# --------------------------------------------------------------------------- #
def _serve(port: int) -> None:
    from app import build_app

    build_app().launch(
        server_name="127.0.0.1",
        server_port=port,
        share=False,
        quiet=True,
        show_api=True,
    )


# --------------------------------------------------------------------------- #
# 辅助
# --------------------------------------------------------------------------- #
def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _write_wav(path: Path, seconds: float, rate: int = 16000) -> None:
    """用标准库 wave 生成一段真实可解析的正弦波音频。"""
    frames = int(seconds * rate)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        buf = bytearray()
        for i in range(frames):
            value = int(8000 * math.sin(2 * math.pi * 440 * i / rate))
            buf += value.to_bytes(2, "little", signed=True)
        wf.writeframes(bytes(buf))


def _wait_ready(url: str, timeout: float = 180.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            time.sleep(1.0)
    return False


def _snapshot_uploads() -> set[str]:
    if not UPLOADS_DIR.is_dir():
        return set()
    return {p.name for p in UPLOADS_DIR.iterdir() if p.is_file()}


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def run_checks(base_url: str) -> list[str]:
    from gradio_client import Client, handle_file

    failures: list[str] = []

    def check(ok: bool, label: str, detail: str = "") -> None:
        print(f"{'✅' if ok else '❌'} {label}")
        if not ok:
            failures.append(label + (f" — {detail}" if detail else ""))

    client = Client(base_url, verbose=False)

    # ---- 1 + 2 + 4：一次性上传 [长音频, 短音频, 非法格式] ----
    print("\n--- 1/2/4. 上传 5s .wav + 1.5s .wav + .txt ---")
    # 不用 tempfile.mkdtemp：它建的是 0o700 目录，在受限沙箱里后续写入会被拒。
    tmpdir = TMP_ROOT / "work"
    if tmpdir.exists():
        shutil.rmtree(tmpdir, ignore_errors=True)
    tmpdir.mkdir(parents=True, exist_ok=True)
    long_wav = tmpdir / LONG_NAME
    short_wav = tmpdir / SHORT_NAME
    bad_txt = tmpdir / BAD_NAME
    _write_wav(long_wav, 5.0)
    _write_wav(short_wav, 1.5)
    bad_txt.write_text("not audio", encoding="utf-8")

    table_html, status, dropdown_value, preview = client.predict(
        [handle_file(str(long_wav)), handle_file(str(short_wav)), handle_file(str(bad_txt))],
        api_name="/_do_upload",
    )

    check(LONG_NAME in table_html, "长音频进入列表", table_html[:200])
    check(SHORT_NAME in table_html, "短音频进入列表", table_html[:200])
    check(BAD_NAME not in table_html, "非法文件未进入列表", table_html[:200])

    # 表格列：名称/时长/大小/格式/状态
    check("0:05" in table_html, "时长列渲染正确（0:05）", table_html[:400])
    check("WAV" in table_html, "格式列渲染正确（WAV）", table_html[:400])
    check("<th" in table_html and "状态" in table_html, "表头包含状态列", table_html[:200])

    check("仅支持" in status, "状态栏给出格式拒绝提示", status)
    check("✖" in status and BAD_NAME in status, "拒绝提示指明是哪个文件", status)
    for token in ("FLAC", "MP3", "WAV", "TXT"):
        check(token in status, f"拒绝提示列出 {token}", status)
    check("过短" in status, "短音频触发时长告警", status)
    check("过短(<3s)" in table_html, "短音频行状态标记「过短(<3s)」", table_html[:600])
    check("已上传 2 个文件" in status, "成功计数只算合法文件（2 个）", status)

    # ---- 3：下拉框选中 → 预览 ----
    print("\n--- 3. 预览端点返回真实文件 ---")
    saved_long = UPLOADS_DIR / LONG_NAME
    check(saved_long.is_file(), f"文件已持久化到 {saved_long}", str(saved_long))

    preview_path = client.predict(LONG_NAME, api_name="/_do_preview")
    check(
        bool(preview_path) and Path(str(preview_path)).is_file(),
        "预览端点返回存在的文件路径",
        repr(preview_path),
    )
    if preview_path and Path(str(preview_path)).is_file():
        check(
            Path(str(preview_path)).read_bytes() == saved_long.read_bytes(),
            "预览返回的就是磁盘上那个文件（内容一致）",
        )

    # 上传响应里的预览/下拉框应指向**本次刚上传**的那个文件，而不是名字排序最大的
    saved_short = UPLOADS_DIR / SHORT_NAME
    preview_name = Path(str(preview)).name if preview else ""
    same_content = (
        bool(preview)
        and Path(str(preview)).is_file()
        and saved_short.is_file()
        and Path(str(preview)).read_bytes() == saved_short.read_bytes()
    )
    check(
        preview_name == SHORT_NAME or same_content,
        f"上传响应预览的是本次刚上传的文件（{SHORT_NAME}）",
        f"name={preview_name!r}, content_match={same_content}",
    )
    # gradio 4.x 返回组件更新时是 dict（{'choices':..., 'value':..., '__type__':'update'}）
    dropdown_selected = (
        dropdown_value.get("value") if isinstance(dropdown_value, dict) else dropdown_value
    )
    check(
        str(dropdown_selected) == SHORT_NAME,
        f"下拉框选中本次刚上传的文件（{SHORT_NAME}）",
        repr(dropdown_value),
    )

    # ---- 2b：只传非法格式 ----
    print("\n--- 2b. 仅上传 .txt ---")
    before = _snapshot_uploads()
    table_html2, status2, _dd2, _pv2 = client.predict(
        [handle_file(str(bad_txt))], api_name="/_do_upload"
    )
    check(
        "仅支持" in status2 and "收到 TXT" in status2,
        "仅非法格式时给出明确提示",
        status2,
    )
    check(
        _snapshot_uploads() == before,
        "非法格式没有污染 workspace/uploads/",
        f"{before} -> {_snapshot_uploads()}",
    )

    # ---- 重新扫描 ----
    print("\n--- 附带：重新扫描与磁盘同步 ---")
    table_html3, status3, _dd3, _pv3 = client.predict(api_name="/_do_refresh")
    check(LONG_NAME in table_html3, "重新扫描能看到磁盘上的文件", table_html3[:200])
    check("已扫描到" in status3 or "上传目录为空" in status3, "重新扫描给出状态", status3)

    shutil.rmtree(tmpdir, ignore_errors=True)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--port", type=int, default=0, help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.serve:
        _serve(args.port)
        return 0

    before_uploads = _snapshot_uploads()
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    print(f"启动子进程服务：{base_url}")
    print(f"（用户的 7860 实例不受影响；现有上传 {len(before_uploads)} 个）\n")

    log_dir = TMP_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"server_{int(time.time())}.log"
    log_file = log_path.open("w", encoding="utf-8", errors="replace")
    proc = subprocess.Popen(
        [sys.executable, "-u", str(Path(__file__).resolve()), "--serve", "--port", str(port)],
        cwd=str(PROJECT_ROOT),
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

    failures: list[str] = []
    try:
        if not _wait_ready(base_url + "/"):
            failures.append("服务未能在超时内就绪")
            print("❌ 服务未就绪；子进程日志：")
        else:
            print("✅ 子进程服务已就绪（顺带回归了 bootstrap.prepare() 的导入顺序）")
            failures.extend(run_checks(base_url))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
        log_file.close()

        # 清掉本次测试新建的上传文件，保留用户原有的上传
        created = sorted(_snapshot_uploads() - before_uploads)
        for name in created:
            try:
                os.remove(UPLOADS_DIR / name)
            except OSError:
                pass
        if created:
            print(f"\n（已清理本次测试写入的 {len(created)} 个文件：{', '.join(created)}）")

        tail = log_path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
        if tail:
            print("\n--- 子进程日志（尾部） ---")
            for line in tail[-15:]:
                print("   ", line)

    print()
    if failures:
        print(f"❌ E2E 失败（{len(failures)} 项）：")
        for item in failures:
            print(f"   - {item}")
        return 1

    print("✅ E2E 全部通过：#6 的四项交互在真实 HTTP 链路下均符合验收标准")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
