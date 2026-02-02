# Copilot / AI Agent Instructions for Aurora Beats 🔧

## Purpose
Help contributors and AI agents be productive immediately: run the app, find and fix bugs, and make focused visual/audio changes.

## Big picture 🧭
- Small desktop app that renders audio-reactive visuals with PyQt6 + moderngl and reads live audio via PyAudio.
- Main entry: `aurora_beats.py` — constructs QApplication, shows a splash, then `AuroraWindow` with `VisualizerWidget` that manages OpenGL and live audio.
- Auxiliary smoke test: `test_qt.py` verifies PyQt6 setup without OpenGL/audio.

## Key files & patterns 📁
- `aurora_beats.py` — all core logic (UI, rendering, audio processing).
  - Global tweakable constants: `PARTICLE_COUNT`, `FLOW_STRENGTH`, `LINE_OPACITY` are mutated by UI sliders at runtime.
  - Audio pipeline: reads frames in chunks (CHUNK=1024), computes FFT, smooths bass/mid/high values and uses them to drive particle velocity and colors.
- `test_qt.py` — minimal GUI smoke test (safe for CI when used with a virtual display).

## How to run & debug ▶️
- Recommended Python: 3.12 (top of `aurora_beats.py` hints this).
- Install packages (Windows tip for PyAudio):
  - pip: `pip install PyQt6 numpy moderngl noise` and for PyAudio use `pipwin install pyaudio` or install wheel compiled for your Python version.
- Run locally: `python aurora_beats.py` (requires an input audio device). Use `python test_qt.py` to check PyQt only.
- When OpenGL context creation fails: check GPU drivers and ensure `QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)` is called before `QApplication()` (this project already does this).

## Project-specific conventions & gotchas ⚠️
- UI mutates global module-level constants (e.g., `FLOW_STRENGTH`) rather than using a settings object — search for globals when changing behavior.
- Rendering update cadence is managed by `QTimer` + `update()` calls; avoid blocking the main thread with heavy Python loops.
- The app expects a live audio input device. For offline/CI runs, mock or stub `pyaudio.PyAudio().open()` or run only `test_qt.py`.

## Critical bug (must fix) ✅
- Currently `initializeGL`, `paintGL`, and `closeEvent` are defined at module scope instead of as methods on `VisualizerWidget` (bad indentation). This prevents expected GL lifecycle hooks from running and will raise attribute errors at runtime. Example fix: indent these function definitions into the `VisualizerWidget` class so they become instance methods (see below).

Example patch (conceptual):
```py
class VisualizerWidget(QOpenGLWidget):
    def initializeGL(self):
        # ... (existing initializeGL body) ...

    def paintGL(self):
        # ... (existing paintGL body) ...

    def closeEvent(self, event):
        # ... (existing closeEvent body) ...
```

## Recent fix (2026-02-01) ✅
- The indentation bug was fixed: `initializeGL`, `paintGL`, and `closeEvent` were moved into `VisualizerWidget` as methods and safety checks were added for missing GL context.
- To validate locally:
  - `python -m py_compile aurora_beats.py` (syntax check)
  - `python -c "from PyQt6.QtWidgets import QApplication; print('PyQt import OK')"` (quick import check)
  - `python test_qt.py` and `python aurora_beats.py` (visual/manual verification; `aurora_beats.py` requires an audio input device)

## Tests & CI tips 🧪
- `test_qt.py` is a lightweight smoke test suitable for CI with a virtual frame buffer (Linux: xvfb-run python test_qt.py).
- GUI-heavy tests are fragile; prefer unit tests for audio processing and non-UI logic if added.

## Editing guidelines for AI agents 🤖
- Be explicit: reference the exact file and line ranges when proposing fixes (e.g., "move `initializeGL` into `VisualizerWidget` class in `aurora_beats.py`").
- Provide a minimal, runnable change and a short test command: e.g., "After fix, run `python test_qt.py` then `python aurora_beats.py` to validate startup." 
- Avoid large refactors without tests; propose them as separate PRs with clear risk descriptions.

---

If any of these sections are unclear or you'd like more examples (e.g., a ready-to-apply patch for the indentation bug or a `requirements.txt`), say which part to expand and I'll update the instructions. ✅