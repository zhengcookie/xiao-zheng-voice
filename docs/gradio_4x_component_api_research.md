# Gradio 4.x Component API Research — Voice Cloning Web UI

> **Target version**: Gradio ≥ 4.0 (tested against 4.44.1 docs)  
> **Project**: `D:\answer skils\xiao zheng voice`  
> **Date**: 2025-07-15

---

## Table of Contents

1. [File Component — Multi-file Upload](#1-file-component)
2. [Audio Component — Playback-Only Player](#2-audio-component)
3. [Progress / Timer — Real-time Updates](#3-progress--timer)
4. [Textbox — Scrolling Log Output](#4-textbox-for-logs)
5. [Dropdown — Dynamic Choices](#5-dropdown)
6. [Blocks Layout — Tabs, Columns, Accordion](#6-blocks-layout)
7. [State Management — Sharing State Between Components](#7-state-management)
8. [Full Reference App](#8-full-reference-app)

---

## 1. File Component

### Key Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_count` | `"single"` \| `"directory"` \| `"multiple"` | Allow one, a directory, or multiple files |
| `file_types` | `list[str]` \| None | Accepted extensions, e.g. `[".wav", ".mp3", ".flac"]` |
| `type` | `"filepath"` \| `"binary"` | What the component passes to your function |
| `label` | str | Label above the component |
| `height` | int \| None | Fixed height (px); enables scrollable list for many files |
| `max_file_size` | int \| str \| None | Max size per file (bytes or human-readable, e.g. `"50mb"`) |
| `every` | float \| Timer \| None | Re-calculate `value` at interval |

### Code Example — Voice Sample Upload

```python
import gradio as gr

with gr.Blocks() as demo:
    gr.Markdown("## 🎤 Upload Voice Samples")

    file_upload = gr.File(
        label="Voice Samples",
        file_count="multiple",              # allow many files
        file_types=[".wav", ".mp3", ".flac"],# filter by audio format
        type="filepath",                     # receive temp file paths
        height=200,                          # scrollable list
    )

    # Optional: server-side size validation in your handler
    def validate_files(files):
        MAX_SIZE = 50 * 1024 * 1024  # 50 MB
        valid, rejected = [], []
        for f in files:
            import os
            if os.path.getsize(f) > MAX_SIZE:
                rejected.append(os.path.basename(f))
            else:
                valid.append(f)
        msg = f"✅ {len(valid)} files accepted"
        if rejected:
            msg += f"\n⚠️ Rejected (>50 MB): {', '.join(rejected)}"
        return msg

    status = gr.Textbox(label="Upload Status", interactive=False)
    file_upload.change(validate_files, inputs=file_upload, outputs=status)

demo.launch()
```

### Gotchas & Limitations

- **No built-in per-file size limit in the browser**: `max_file_size` is a **server-side** validation parameter (added in Gradio ≥ 4.22). For older 4.x, you must validate in your handler.
- **Drag-and-drop** works out of the box — the File component renders a dropzone.
- **`file_types`** uses browser `<input accept>` syntax. Use extensions with leading dot.
- **Directory mode** (`file_count="directory"`) picks an entire folder — useful for batch voice ingestion.
- When `type="filepath"`, files are uploaded to a temp directory managed by Gradio. **Copy them** to your workspace if you need persistence across restarts.

---

## 2. Audio Component

### Key Parameters for Playback-Only

| Parameter | Type | Description |
|-----------|------|-------------|
| `interactive` | bool \| None | `False` → playback only (no record/upload/edit) |
| `source` | `"upload"` \| `"microphone"` \| `"upload"` | Where audio comes from (ignored when `interactive=False`) |
| `type` | `"numpy"` \| `"filepath"` | What gets passed to your function |
| `format` | `"wav"` \| `"mp3"` \| None | Output format when returning audio |
| `autoplay` | bool | Auto-play when component receives a value |
| `show_download_button` | bool | Show download icon |
| `waveform_options` | dict \| None | Waveform appearance settings |
| `show_waveform` | bool | Force waveform display (default True) |
| `loop` | bool | Loop playback |
| `visible` | bool | Show/hide component |

### `waveform_options` dict

```python
waveform_options = {
    "waveform_color": "#FF6B6B",         # waveform bar color
    "waveform_progress_color": "#4ECDC4", # played-portion color
    "skip_length": 5,                     # seconds per skip button
    "trim_region_color": "#95E1D3",       # trim region color
}
```

### Code Example — Read-Only Audio Player with Waveform

```python
import gradio as gr
import numpy as np

with gr.Blocks() as demo:
    gr.Markdown("## 🔊 Voice Playback")

    # --- Interactive recorder (for reference) ---
    mic_input = gr.Audio(
        label="Record or Upload",
        source=["upload", "microphone"],
        type="filepath",
    )

    # --- Read-only player (output / playback only) ---
    player = gr.Audio(
        label="Cloned Voice Output",
        type="filepath",           # receives a file path
        interactive=False,         # ← KEY: no record/upload/edit
        show_download_button=True, # user can download result
        autoplay=False,            # don't auto-play (browser blocks it anyway)
        show_waveform=True,        # waveform visualization
        waveform_options=waveform_options,
        loop=False,
        format="wav",              # or "mp3" for smaller files
    )

    # Example: function that "produces" cloned audio
    def clone_voice(audio_path):
        # ... your voice cloning logic here ...
        output_path = "workspace/output/cloned_sample.wav"
        return output_path

    clone_btn = gr.Button("Clone Voice", variant="primary")
    clone_btn.click(clone_voice, inputs=mic_input, outputs=player)

demo.launch()
```

### Gotchas & Limitations

- **`interactive=False`** is the key to a pure playback component. When used as an **output only**, Gradio infers this automatically.
- **Browser autoplay policy**: `autoplay=True` only works if the user has interacted with the page first. Don't rely on it.
- **`show_waveform=True`** (default) renders a waveform bar using the Wavesurfer.js library. The old browser-native `<audio>` fallback can be forced with `show_waveform=False`.
- **Streaming**: For real-time TTS streaming, use `live=True` with `source="microphone"` — the audio chunks are combined client-side.
- **Sample rate**: When `type="numpy"`, your function receives `(sample_rate, numpy_array)`. When outputting numpy, specify `format` to control the encoding.

---

## 3. Progress / Timer

Gradio 4.x introduced **`gr.Timer`** — a special invisible component that ticks at a regular interval. This replaces the old polling patterns.

### `gr.Timer` Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `interval` | float \| None | Seconds between ticks (can be updated dynamically) |
| `active` | bool | Whether the timer is currently running |
| `every` | float \| None | Same as interval (alias) |

### Code Example A — Training Progress with `gr.Timer`

```python
import gradio as gr
import time, threading

# Shared mutable state for training progress
training_state = {
    "progress": 0,
    "status": "idle",
    "logs": "",
}

def start_training():
    """Start training in a background thread."""
    def _train():
        training_state["status"] = "training"
        training_state["logs"] = ""
        for step in range(1, 101):
            time.sleep(0.1)  # simulate work
            training_state["progress"] = step
            training_state["logs"] += f"[Step {step}/100] Loss: {1.0 - step/100:.4f}\n"
        training_state["status"] = "completed"

    threading.Thread(target=_train, daemon=True).start()
    return gr.update(interactive=False), gr.update(interactive=True)

def poll_progress():
    """Called by gr.Timer every 0.5s to fetch latest progress."""
    return (
        training_state["progress"],
        training_state["status"],
        training_state["logs"],
    )

def stop_training():
    training_state["status"] = "stopped"
    return gr.update(interactive=True)

with gr.Blocks() as demo:
    gr.Markdown("## 🏋️ Voice Model Training")

    with gr.Row():
        start_btn = gr.Button("Start Training", variant="primary")
        stop_btn = gr.Button("Stop", interactive=False)

    progress_bar = gr.Slider(0, 100, value=0, label="Progress", interactive=False)
    status_text = gr.Textbox(label="Status", interactive=False)
    log_box = gr.Textbox(
        label="Training Logs",
        lines=15,
        max_lines=30,
        interactive=False,
        autoscroll=True,      # ← auto-scroll to bottom on new content
        show_copy_button=True,
    )

    # The Timer component — ticks every 0.5s
    timer = gr.Timer(0.5)

    start_btn.click(
        start_training,
        outputs=[start_btn, stop_btn],
    )

    timer.tick(
        poll_progress,
        outputs=[progress_bar, status_text, log_box],
    )

    stop_btn.click(
        stop_training,
        outputs=[stop_btn],
    )

demo.launch()
```

### Code Example B — Dynamic Timer Interval (Slow Down When Done)

```python
import gradio as gr

def check_status():
    """Return (progress_value, new_interval)."""
    if training_state["progress"] >= 100:
        return 100, None          # None stops the timer
    elif training_state["progress"] > 80:
        return training_state["progress"], 2.0  # slow down polling
    else:
        return training_state["progress"], 0.5  # fast polling

timer = gr.Timer(0.5)
timer.tick(check_status, outputs=[progress_bar, timer])  # timer updates itself!
```

### Alternative: Built-in `gr.Progress` (for single-call progress)

```python
def train_with_progress(progress=gr.Progress(track_tqdm=True)):
    for step in progress.tqdm(range(100), desc="Training"):
        time.sleep(0.1)
    return "Done!"
```

### Gotchas & Limitations

- **`gr.Timer`** is new in Gradio 4.x (added ~4.30). It runs on the **client side** — the `tick` callback executes on the server. This is more reliable than `every=` polling on components.
- **Timer cannot be started/stopped programmatically** from a callback in early 4.x versions. The `active` parameter controls initial state. Dynamic interval changes (returning a new float to the timer output) work.
- **`gr.Progress(track_tqdm=True)`** only works when your function is the direct handler — not for background threads. Use `gr.Timer` for background training.
- **Thread safety**: Use a thread-safe queue or `threading.Lock` for shared state between your training thread and the Timer callback.
- **`every=` parameter** on any component (like `Textbox(every=2)`) is a simpler alternative but polls on the component value itself, not a custom function.

---

## 4. Textbox for Logs

### Key Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `lines` | int | Initial visible height |
| `max_lines` | int \| None | Max lines before scroll |
| `autoscroll` | bool | Auto-scroll to bottom when value changes (Gradio ≥ 4.x) |
| `interactive` | bool | `False` → read-only |
| `show_copy_button` | bool | Show copy button in toolbar |
| `label` | str | Component label |
| `type` | `"text"` \| `"password"` \| `"email"` | Input type |

### Code Example — Auto-scrolling Log Display

```python
import gradio as gr

log_display = gr.Textbox(
    label="📋 Training Logs",
    lines=20,               # show ~20 lines
    max_lines=40,           # allow scroll up to 40
    interactive=False,      # read-only
    autoscroll=True,        # ← KEY: scroll to bottom on update
    show_copy_button=True,  # user can copy all logs
    every=1,                # optional: re-poll value every 1s
)

# Append new log lines
def append_log(new_line, current_logs):
    timestamped = f"[{time.strftime('%H:%M:%S')}] {new_line}"
    updated = (current_logs + "\n" + timestamped).strip()
    return updated
```

### Gotchas & Limitations

- **`autoscroll=True`** only scrolls to bottom when the **value changes from the server side**. If the user scrolls up manually, the browser will respect their position (won't force-scroll them down on every update).
- **No streaming insert**: You must return the **full log text** each time. For very long logs (10K+ lines), consider truncating or using a `gr.Dataframe` / `gr.Code` component instead.
- **`show_copy_button`** adds a toolbar button — great for users to export logs.
- **Alternative**: Use `gr.Code(language="log")` for syntax-highlighted, monospace log output with line numbers.

---

## 5. Dropdown — Dynamic Choices

### Key Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `choices` | `list[str \| int \| float]` | Available options |
| `value` | str \| int \| float \| None | Initially selected value |
| `multiselect` | bool | Allow multiple selections |
| `allow_custom_value` | bool | Allow typing custom values |
| `filterable` | bool | Show search/filter input (default True) |
| `type` | `"value"` \| `"index"` | Return value or index |
| `max_choices` | int \| None | Limit selections in multiselect |
| `visible` | bool | Show/hide component |

### Code Example — Dynamic Model List

```python
import gradio as gr
import os, glob

# Initial choices
def get_model_list():
    models_dir = "workspace/models"
    if not os.path.isdir(models_dir):
        return ["(no models found)"]
    models = sorted(glob.glob(os.path.join(models_dir, "*.pt")))
    return [os.path.basename(m) for m in models] or ["(no models found)"]

with gr.Blocks() as demo:
    gr.Markdown("## 🧠 Voice Model Selection")

    model_dropdown = gr.Dropdown(
        choices=get_model_list(),
        label="Select Model",
        interactive=True,
        filterable=True,           # search-as-you-type
        value=get_model_list()[0] if get_model_list() else None,
    )

    # Button to refresh the list after training
    refresh_btn = gr.Button("🔄 Refresh Model List")

    def refresh_models():
        new_choices = get_model_list()
        # In Gradio 4.x, return gr.Dropdown with updated choices
        return gr.Dropdown(
            choices=new_choices,
            value=new_choices[0] if new_choices else None,
        )

    refresh_btn.click(refresh_models, outputs=model_dropdown)

    # Alternative: update from any event handler
    def after_training_complete(state):
        """After training, update the dropdown."""
        new_choices = get_model_list()
        return gr.Dropdown(choices=new_choices, value=new_choices[-1])

demo.launch()
```

### Dynamic Update Pattern (From Any Event)

```python
def update_dropdown_after_event():
    new_choices = ["model_v1.pt", "model_v2.pt", "model_v3.pt"]
    # Return a gr.update() dict or a new component instance
    return gr.Dropdown(choices=new_choices, value=new_choices[-1])

# Wire it up
some_button.click(update_dropdown_after_event, outputs=model_dropdown)
```

### Gotchas & Limitations

- **Gradio 4.x update pattern**: Return `gr.Dropdown(choices=..., value=...)` from your function. The older `gr.update()` dict syntax also works but the component-constructor syntax is preferred.
- **`filterable=True`** (default) adds a search box — essential for long lists of models.
- **Performance**: For 1000+ choices, Gradio virtualizes the list. But `filterable=True` is strongly recommended.
- **`allow_custom_value=True`** lets users type a value not in the list — useful for specifying a custom model name.
- **Race condition**: If a training job is adding models to disk while the user clicks "Refresh", you may get stale results. Consider using a lock.

---

## 6. Blocks Layout

### Tabs

```python
import gradio as gr

with gr.Blocks() as demo:
    with gr.Tabs():
        with gr.TabItem("🎤 Upload & Clone"):
            gr.Markdown("Upload voice and clone")
            audio_in = gr.Audio(source="upload", type="filepath")
            clone_btn = gr.Button("Clone")
            audio_out = gr.Audio(interactive=False)

        with gr.TabItem("🏋️ Train"):
            gr.Markdown("Train a new voice model")
            train_btn = gr.Button("Start Training")

        with gr.TabItem("⚙️ Settings"):
            gr.Markdown("Configuration")
            model_dir = gr.Textbox(label="Model Directory", value="workspace/models")

demo.launch()
```

### Columns & Rows

```python
with gr.Blocks() as demo:
    gr.Markdown("## Voice Cloning Dashboard")

    # Side-by-side layout
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### Input")
            audio_input = gr.Audio(label="Voice Sample", source=["upload", "microphone"])
            text_input = gr.Textbox(label="Text to Synthesize", lines=3)

        with gr.Column(scale=1):
            gr.Markdown("### Settings")
            model_select = gr.Dropdown(choices=["Model A", "Model B"], label="Model")
            speed_slider = gr.Slider(0.5, 2.0, value=1.0, label="Speed")
            pitch_slider = gr.Slider(-12, 12, value=0, label="Pitch (semitones)")

    # Full-width output
    gr.Markdown("### Output")
    audio_output = gr.Audio(label="Synthesized Voice", interactive=False)
```

### Accordion

```python
with gr.Blocks() as demo:
    gr.Markdown("## Advanced Options")

    # Collapsible section
    with gr.Accordion("🔧 Advanced Settings", open=False):
        with gr.Row():
            sample_rate = gr.Slider(8000, 48000, value=22050, label="Sample Rate")
            chunk_size = gr.Slider(256, 4096, value=512, label="Chunk Size")
        denoise = gr.Checkbox(label="Apply Denoising", value=True)
        normalize = gr.Checkbox(label="Normalize Audio", value=True)

    # Nested accordion
    with gr.Accordion("📊 Training Details", open=False):
        with gr.Accordion("Hyperparameters", open=True):
            lr = gr.Number(label="Learning Rate", value=0.0001)
            epochs = gr.Slider(10, 1000, value=100, label="Epochs")
```

### Complete Layout Example

```python
with gr.Blocks(title="Voice Cloning Studio", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎭 Voice Cloning Studio")

    with gr.Tabs():
        # ---- Tab 1: Inference ----
        with gr.TabItem("🔮 Clone Voice"):
            with gr.Row():
                with gr.Column(scale=2):
                    with gr.Accordion("📝 Input", open=True):
                        ref_audio = gr.Audio(label="Reference Voice", source="upload")
                        ref_text = gr.Textbox(label="Reference Text (optional)", lines=2)
                        target_text = gr.Textbox(label="Text to Speak", lines=3)

                    with gr.Accordion("⚙️ Parameters", open=False):
                        with gr.Row():
                            stability = gr.Slider(0.0, 1.0, value=0.5, label="Stability")
                            similarity = gr.Slider(0.0, 1.0, value=0.75, label="Similarity")

                        model_dropdown = gr.Dropdown(choices=["Fast", "Quality"], value="Quality")

                with gr.Column(scale=1):
                    clone_btn = gr.Button("🚀 Clone", variant="primary", size="lg")
                    result_audio = gr.Audio(label="Result", interactive=False)
                    log_output = gr.Textbox(
                        label="Logs", lines=10, interactive=False,
                        autoscroll=True, show_copy_button=True,
                    )

        # ---- Tab 2: Training ----
        with gr.TabItem("🏋️ Train Model"):
            with gr.Row():
                with gr.Column():
                    train_files = gr.File(
                        label="Training Audio",
                        file_count="multiple",
                        file_types=[".wav", ".mp3", ".flac"],
                    )
                    train_name = gr.Textbox(label="Model Name")
                    train_btn = gr.Button("Start Training", variant="primary")
                with gr.Column():
                    train_progress = gr.Slider(0, 100, value=0, label="Progress", interactive=False)
                    train_logs = gr.Textbox(label="Logs", lines=15, interactive=False, autoscroll=True)
                    timer = gr.Timer(0.5)

        # ---- Tab 3: Gallery ----
        with gr.TabItem("📁 Models"):
            model_list = gr.Dropdown(choices=[], label="Saved Models", filterable=True)
            refresh_btn = gr.Button("🔄 Refresh")

demo.launch()
```

### Gotchas & Limitations

- **`gr.Tabs`** and **`gr.TabItem`**: In Gradio 4.x, use `with gr.Tabs():` and `with gr.TabItem("Label"):`. Earlier 4.x used `gr.Tab()`. Both work in 4.44+.
- **`gr.Column(scale=N)`**: `scale` controls relative width inside a `gr.Row()`. Higher scale = wider.
- **`gr.Accordion(open=False)`**: Collapsed by default. Set `open=True` for expanded.
- **`gr.Row(equal_height=True)`**: Forces all columns to the same height.
- **Nested layouts**: Rows inside Columns inside Tabs work, but avoid >8 levels of nesting.
- **`gr.Sidebar`** (Gradio ≥ 4.30): New alternative to `gr.Column` for persistent side panels.

---

## 7. State Management

### `gr.State` — Per-Session State

```python
import gradio as gr

def build_app():
    # Session state — unique per user session
    training_state = gr.State(value={
        "status": "idle",
        "handle": None,
        "progress": 0,
        "model_path": None,
    })

    with gr.Blocks() as demo:
        gr.Markdown("## State Management Demo")

        start_btn = gr.Button("Start Training")
        status_display = gr.Textbox(label="Status", interactive=False)

        def start_training(state):
            """Start training, store handle in state."""
            import threading
            state["status"] = "training"

            def _train():
                import time
                for i in range(100):
                    time.sleep(0.05)
                    state["progress"] = i + 1
                state["status"] = "completed"
                state["model_path"] = "workspace/models/my_model.pt"

            handle = threading.Thread(target=_train, daemon=True)
            handle.start()
            state["handle"] = handle
            return state, f"Status: {state['status']}"

        def check_status(state):
            """Poll state to get current status."""
            return f"Status: {state['status']} | Progress: {state['progress']}%"

        start_btn.click(
            start_training,
            inputs=[training_state],
            outputs=[training_state, status_display],
        )

    return demo, training_state

demo, _ = build_app()
demo.launch()
```

### Pattern: Global State + `gr.State` for UI Binding

```python
import threading
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class GlobalTrainingState:
    """Thread-safe global state for the training process."""
    status: str = "idle"
    progress: float = 0.0
    logs: str = ""
    model_path: Optional[str] = None
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def update(self, **kwargs):
        with self._lock:
            for k, v in kwargs.items():
                setattr(self, k, v)

    def snapshot(self):
        """Return a copy for safe reading."""
        with self._lock:
            return {
                "status": self.status,
                "progress": self.progress,
                "logs": self.logs,
                "model_path": self.model_path,
            }

# Global instance (shared across all sessions)
global_state = GlobalTrainingState()

# Per-session gr.State for UI interaction flags
ui_state = gr.State(value={"training_active": False})
```

### Sharing State Between Components via Event Wiring

```python
# The dropdown's choices depend on what files exist
def refresh_models():
    import glob, os
    models = sorted(glob.glob("workspace/models/*.pt"))
    choices = [os.path.basename(m) for m in models]
    return gr.Dropdown(choices=choices, value=choices[0] if choices else None)

# The audio player depends on which model is selected
def load_model_audio(model_name, state):
    if model_name and state.get("model_path"):
        return state["model_path"]
    return None

# Wire components together
refresh_btn.click(refresh_outputs, outputs=[model_dropdown])
model_dropdown.change(
    load_model_audio,
    inputs=[model_dropdown, ui_state],
    outputs=[audio_player],
)
```

### Gotchas & Limitations

- **`gr.State`** is **per-session** — each browser tab gets its own copy. Great for user-specific data (like a training handle).
- **State is not persisted** across server restarts. If you need persistence, write to disk (e.g., `workspace/state.json`).
- **Mutable state**: You can store Python objects (dicts, dataclasses) in `gr.State`. The state object is passed **by reference**, so mutations are reflected in subsequent reads.
- **Global state** (module-level variables) is shared across sessions. Use locks for thread safety.
- **State cannot be read by `gr.Timer` directly** unless you pass it as an input. The Timer callback must explicitly receive state as an input component.
- **State serialization**: Complex objects (like model handles) are serialized between server and client. Keep the state payload small — store handles in a global dict and only pass IDs in `gr.State`.

---

## 8. Full Reference App

A complete `app.py` skeleton combining all the patterns above:

```python
"""
Voice Cloning Web UI — Gradio 4.x Reference App
File: D:\answer skils\xiao zheng voice\app.py
"""

import gradio as gr
import os
import time
import threading
import glob
from pathlib import Path

# --- Configuration ---
WORKSPACE = Path("workspace")
MODELS_DIR = WORKSPACE / "models"
OUTPUT_DIR = WORKSPACE / "output"
AUDIO_DIR = WORKSPACE / "audio"

for d in [MODELS_DIR, OUTPUT_DIR, AUDIO_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# --- Global Training State ---
class TrainingManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.status = "idle"
        self.progress = 0.0
        self.logs = ""
        self.model_path = None

    def update(self, **kw):
        with self.lock:
            for k, v in kw.items():
                setattr(self, k, v)

    def snapshot(self):
        with self.lock:
            return {k: getattr(self, k) for k in ["status", "progress", "logs", "model_path"]}

trainer = TrainingManager()


# --- Handlers ---
def get_model_choices():
    models = sorted(MODELS_DIR.glob("*.pt"))
    names = [m.name for m in models]
    return names or ["(no models)"]


def clone_voice(ref_audio, ref_text, target_text, model_name, stability, similarity):
    """Placeholder: your voice cloning logic here."""
    trainer.update(status="cloning", logs="Starting voice clone...")
    time.sleep(1)  # simulate
    output_path = str(OUTPUT_DIR / f"clone_{int(time.time())}.wav")
    # ... run model inference ...
    trainer.update(status="done", logs="Clone complete!")
    return output_path, f"[{time.strftime('%H:%M:%S')}] Cloned → {output_path}"


def start_training(audio_files, model_name):
    """Start a training job in a background thread."""
    if not audio_files:
        raise gr.Error("Please upload at least one audio file.")

    def _train():
        trainer.update(status="training", progress=0, logs="Preparing data...")
        total_steps = 100
        for step in range(1, total_steps + 1):
            time.sleep(0.1)
            trainer.update(
                progress=step,
                logs=trainer.logs + f"\n[Step {step}/{total_steps}] loss={1.0 - step/total_steps:.4f}",
            )
        trainer.update(status="completed", progress=100, model_path=f"{MODELS_DIR}/{model_name}.pt")
        # Save dummy model
        (MODELS_DIR / f"{model_name}.pt").touch()

    threading.Thread(target=_train, daemon=True).start()
    return gr.update(interactive=False), gr.update(interactive=True), ""


def poll_training():
    """Called by gr.Timer every 0.5s."""
    snap = trainer.snapshot()
    return snap["progress"], snap["status"], snap["logs"]


def refresh_models():
    choices = get_model_choices()
    return gr.Dropdown(choices=choices, value=choices[0])


# --- Build UI ---
with gr.Blocks(
    title="Voice Cloning Studio",
    theme=gr.themes.Soft(),
) as demo:
    gr.Markdown("# 🎭 Voice Cloning Studio")

    with gr.Tabs():
        # ===== Tab 1: Clone =====
        with gr.TabItem("🔮 Clone Voice"):
            with gr.Row():
                with gr.Column(scale=2):
                    with gr.Accordion("📝 Input", open=True):
                        ref_audio = gr.Audio(
                            label="Reference Voice",
                            source=["upload", "microphone"],
                            type="filepath",
                        )
                        ref_text = gr.Textbox(label="Reference Text (optional)", lines=2)
                        target_text = gr.Textbox(label="Text to Synthesize", lines=3)

                    with gr.Accordion("⚙️ Parameters", open=False):
                        with gr.Row():
                            stability = gr.Slider(0.0, 1.0, value=0.5, label="Stability")
                            similarity = gr.Slider(0.0, 1.0, value=0.75, label="Similarity Boost")

                        model_dropdown = gr.Dropdown(
                            choices=get_model_choices(),
                            label="Model",
                            filterable=True,
                        )
                        refresh_btn = gr.Button("🔄 Refresh Models", size="sm")

                with gr.Column(scale=1):
                    clone_btn = gr.Button("🚀 Clone Voice", variant="primary", size="lg")
                    result_audio = gr.Audio(
                        label="Cloned Result",
                        interactive=False,
                        show_download_button=True,
                        show_waveform=True,
                        waveform_options={
                            "waveform_color": "#4ECDC4",
                            "waveform_progress_color": "#FF6B6B",
                            "skip_length": 5,
                        },
                    )
                    log_output = gr.Textbox(
                        label="Logs",
                        lines=8,
                        interactive=False,
                        autoscroll=True,
                        show_copy_button=True,
                    )

        # ===== Tab 2: Train =====
        with gr.TabItem("🏋️ Train Model"):
            with gr.Row():
                with gr.Column():
                    train_files = gr.File(
                        label="Training Audio Samples",
                        file_count="multiple",
                        file_types=[".wav", ".mp3", ".flac"],
                        height=200,
                    )
                    train_name = gr.Textbox(label="New Model Name", placeholder="my_voice_v1")
                    with gr.Row():
                        train_btn = gr.Button("▶️ Start Training", variant="primary")
                        stop_btn = gr.Button("⏹ Stop", interactive=False)

                with gr.Column():
                    train_progress = gr.Slider(
                        0, 100, value=0, label="Progress", interactive=False
                    )
                    train_status = gr.Textbox(label="Status", interactive=False)
                    train_logs = gr.Textbox(
                        label="Training Logs",
                        lines=15,
                        interactive=False,
                        autoscroll=True,
                        show_copy_button=True,
                    )

            # Timer for polling training progress
            poll_timer = gr.Timer(0.5)

        # ===== Tab 3: Settings =====
        with gr.TabItem("⚙️ Settings"):
            with gr.Accordion("📂 Paths", open=True):
                gr.Textbox(value=str(MODELS_DIR), label="Models Directory", interactive=False)
                gr.Textbox(value=str(OUTPUT_DIR), label="Output Directory", interactive=False)

            with gr.Accordion("🎛️ Defaults", open=False):
                gr.Slider(0, 48000, value=22050, label="Default Sample Rate")
                gr.Checkbox(label="Auto-denoise input", value=True)
                gr.Checkbox(label="Normalize output", value=True)

    # --- Wire Events ---
    clone_btn.click(
        clone_voice,
        inputs=[ref_audio, ref_text, target_text, model_dropdown, stability, similarity],
        outputs=[result_audio, log_output],
    )

    refresh_btn.click(refresh_models, outputs=model_dropdown)

    train_btn.click(
        start_training,
        inputs=[train_files, train_name],
        outputs=[train_btn, stop_btn, train_logs],
    )

    poll_timer.tick(
        poll_training,
        outputs=[train_progress, train_status, train_logs],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,       # set True for public link
    )
```

---

## Quick Reference: Version-Specific Notes

| Feature | Min Gradio Version | Notes |
|---------|-------------------|-------|
| `gr.Timer` | ~4.30 | Client-side interval, `tick()` event |
| `gr.File(max_file_size=...)` | ~4.22 | Server-side size validation |
| `gr.Textbox(autoscroll=True)` | 4.x (stable) | Auto-scroll to bottom on value change |
| `gr.Dropdown(filterable=True)` | 4.x | Search-as-you-type (default True) |
| `gr.Audio(waveform_options=...)` | 4.x | Wavesurfer.js waveform customization |
| `gr.Audio(show_waveform=True)` | 4.x | Force waveform (default True) |
| `gr.Accordion` | 4.x | Collapsible section container |
| `gr.Sidebar` | ~4.30 | Persistent sidebar layout |
| `gr.themes.Soft()` | 4.x | Built-in themes |
| `gr.Audio(source=["upload", "microphone"])` | 4.x | Multi-source input |
| `gr.Textbox(show_copy_button=True)` | 4.x | Copy button in toolbar |
| `gr.File(show_download_button=True)` | 4.x | Download button |

---

## References

- [Gradio File Docs](https://www.gradio.app/docs/gradio/file)
- [Gradio Audio Docs](https://www.gradio.app/docs/gradio/audio)
- [Gradio Timer Docs](https://www.gradio.app/docs/gradio/timer)
- [Gradio Textbox Docs](https://www.gradio.app/docs/gradio/textbox)
- [Gradio Dropdown Docs](https://www.gradio.app/docs/gradio/dropdown)
- [Gradio State Docs](https://www.gradio.app/docs/gradio/state)
- [Gradio Blocks Guide](https://www.gradio.app/guides/blocks-and-event-listeners)
