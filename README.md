Aurora Beats
============

A real-time audio-reactive visualizer built in Python.

Inspired by the hypnotic, low-latency flow of classic tools like G-Force, but rebuilt from scratch to be cleaner, more immediate, and eventually extended with live-ish AI-generated backgrounds that warp and distort to the music's pulse, BPM, and feel.

Current state (Feb 2026)
------------------------
- Splash screen with fading stylized title
- Fullscreen (or windowed debug) OpenGL visualizer using PyQt6 + moderngl
- Real-time microphone audio analysis (FFT, bass/mids/highs, smoothing)
- Particle system with Perlin flow-field advection, audio-driven velocity and color
- Fading control overlay (mouse-move reveal) with sliders for flow strength & particle count
- Debug prints for audio levels, GL context info, and paint loop
- Runs on Python 3.12 (3.13 wheels were unreliable for PyQt6/moderngl)

What works right now
--------------------
- Window opens (800×600 debug mode; fullscreen commented out)
- Background color changes subtly per frame (proof of paint loop)
- Particles (white dots) should drift slowly even without sound
- Audio values print to console and influence motion/color when mic picks up sound
- Overlay appears on mouse move, fades after idle

Known current issues / limitations
----------------------------------
- Particles may be tiny or hard to see (point size not set high enough)
- No lines, sprites, or advanced flow visualization yet
- No AI background generation/warping layer (next phase)
- Fullscreen + frameless mode can flicker or fail to stay visible on some Windows setups
- Point size and blending need tuning for visual impact
- No preset saving/loading, genre/BPM detection, or MIDI/OSC control yet

Requirements
------------
Python 3.12 (recommended; 3.13 had wheel issues)
Dependencies (installed via pip):
  PyQt6
  pyaudio
  numpy
  scipy
  moderngl
  noise
  librosa (optional for future BPM/genre)

Setup
-----
1. Create and activate venv:
   python3.12 -m venv venv
   source venv/Scripts/activate   (Git Bash)
   # or .\venv\Scripts\activate   (PowerShell)

2. Install packages:
   pip install --upgrade pip
   pip install PyQt6 pyaudio numpy scipy moderngl noise librosa

3. Run:
   python aurora_beats.py

Troubleshooting
---------------
- No window / flicker → Check NVIDIA Control Panel → set python.exe to high-performance GPU
- Black screen → Look for GL vendor/renderer prints (should be NVIDIA/AMD, not SwiftShader)
- No audio reaction → Windows Settings → Privacy → Microphone → allow Python
- "AA_UseDesktopOpenGL" warning → Ensure attribute set before QApplication creation

Next milestones (in rough order)
--------------------------------
- Make particles larger, more colorful, and clearly reactive
- Add lines, radial bursts, sprite warping
- Implement dynamic point size, line thickness via sliders
- Re-enable stable fullscreen + frameless mode
- Add periodic local Stable Diffusion background generation (diffusers lib)
- Audio-driven distortion shader on AI background (displace, hue cycle, bloom)
- BPM/genre proxy detection → influence prompt/style
- Preset save/load (JSON)
- Stream output (OBS virtual cam or ffmpeg)

License
-------
Personal / experimental project — use, modify, enjoy as you see fit. No formal license yet.

Joe (@below_joe29570)
De Pere, Wisconsin
February 2026
