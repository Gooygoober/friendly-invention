# aurora_beats.py
# Aurora Beats — real-time audio-reactive visuals
# Python 3.12 / PyQt6 / moderngl / pyaudio

import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QSplashScreen,
    QLabel, QVBoxLayout, QWidget, QSlider, QLabel as QtLabel
)
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPainter, QLinearGradient, QBrush
import pyaudio
import moderngl
from noise import pnoise2

print("Imports successful - QOpenGLWidget loaded from QtOpenGLWidgets")

# Audio constants
CHUNK = 1024
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100

# Visual params (tweakable live)
PARTICLE_COUNT = 800
FLOW_STRENGTH = 0.8
LINE_OPACITY = 0.6

class VisualizerWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.ctx = None
        self.program = None
        self.vao = None
        self.particles_pos = None
        self.particles_vel = None
        self.time = 0.0

        # Audio
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                                  input=True, frames_per_buffer=CHUNK)
        self.bass = 0.0
        self.mids = 0.0
        self.highs = 0.0

        # Smoothing
        self.bass_smooth = 0.0
        self.mids_smooth = 0.0
        self.highs_smooth = 0.0

        # Timer for audio update
        self.audio_timer = QTimer(self)
        self.audio_timer.timeout.connect(self.update_audio)
        self.audio_timer.start(16)  # ~60 fps

    def update_audio(self):
        try:
            data = self.stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.float32)
            spectrum = np.abs(np.fft.rfft(audio_data))[:CHUNK//2]
            freq_bins = np.linspace(0, RATE/2, len(spectrum))

            bass_mask = (freq_bins < 200)
            mids_mask = (freq_bins >= 200) & (freq_bins < 2000)
            highs_mask = (freq_bins >= 2000)

            self.bass = np.mean(spectrum[bass_mask]) if np.any(bass_mask) else 0
            self.mids = np.mean(spectrum[mids_mask]) if np.any(mids_mask) else 0
            self.highs = np.mean(spectrum[highs_mask]) if np.any(highs_mask) else 0

            alpha = 0.15
            self.bass_smooth = alpha * self.bass + (1 - alpha) * self.bass_smooth
            self.mids_smooth = alpha * self.mids + (1 - alpha) * self.mids_smooth
            self.highs_smooth = alpha * self.highs + (1 - alpha) * self.highs_smooth

            print(f"Audio: Bass {self.bass_smooth:.3f} | Mids {self.mids_smooth:.3f} | Highs {self.highs_smooth:.3f}")

            self.update()  # trigger paintGL
        except IOError:
            pass

    def initializeGL(self):
        print("initializeGL called")
        try:
            self.ctx = moderngl.create_context()
            print("moderngl context created successfully")
        except Exception as e:
            print("Context creation failed:", e)
            self.ctx = None

        print("OpenGL vendor:", self.ctx.info["GL_VENDOR"] if self.ctx else "None")
        if self.ctx:
            print("OpenGL renderer:", self.ctx.info.get("GL_RENDERER", "Unknown"))
            print("OpenGL version:", self.ctx.info.get("GL_VERSION", "Unknown"))
            self.ctx.enable(moderngl.BLEND)
            self.ctx.blend_func = (self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA)

            vertex_shader = """
                #version 330
                in vec2 in_pos;
                in vec4 in_color;
                out vec4 v_color;
                void main() {
                    gl_Position = vec4(in_pos, 0.0, 1.0);
                    v_color = in_color;
                }
                """
            fragment_shader = """
                #version 330
                in vec4 v_color;
                out vec4 out_color;
                void main() {
                    out_color = v_color;
                }
                """
            self.program = self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)

            # Init particles
            self.particles_pos = np.random.uniform(-1, 1, (PARTICLE_COUNT, 2)).astype('f4')
            self.particles_vel = np.zeros((PARTICLE_COUNT, 2), dtype='f4')

            # Proper VBO: pos (2f), color (4f)
            pos_data = self.particles_pos.astype('f4')
            col_data = np.ones((PARTICLE_COUNT, 4), dtype='f4') * [1.0, 1.0, 1.0, 0.8]  # initial white
            vertices = np.hstack([pos_data, col_data]).ravel()
            vbo = self.ctx.buffer(vertices.tobytes())
            self.vao = self.ctx.vertex_array(
                self.program,
                [(vbo, '2f 4f', 'in_pos', 'in_color')]
            )
        else:
            print("Skipping GL initialization due to missing context")

    def paintGL(self):
        print("paintGL called, time:", self.time)
        if not self.ctx or not getattr(self, 'vao', None):
            return
        self.ctx.clear(0.1 + self.time*0.01 % 0.4, 0.2, 0.8, 1.0)  # changing blue-ish for visibility

        self.time += 0.016

        # Flow field influence
        for i in range(PARTICLE_COUNT):
            x, y = self.particles_pos[i]
            nx = x * 3.0 + self.time * 0.2
            ny = y * 3.0 + self.time * 0.1
            angle = pnoise2(nx, ny, octaves=2) * np.pi * 2
            force = np.array([np.cos(angle), np.sin(angle)]) * FLOW_STRENGTH * self.bass_smooth * 0.005
            self.particles_vel[i] += force
            self.particles_vel[i] *= 0.98
            self.particles_pos[i] += self.particles_vel[i]
            self.particles_pos[i] = np.mod(self.particles_pos[i] + 1, 2) - 1

        # Audio-reactive colors
        colors = np.zeros((PARTICLE_COUNT, 4), dtype='f4')
        colors[:, 0] = 0.2 + self.highs_smooth * 2.0  # R
        colors[:, 1] = 0.4 + self.mids_smooth * 1.5   # G
        colors[:, 2] = 0.8 + self.bass_smooth * 1.2   # B
        colors[:, 3] = 0.7 + self.highs_smooth * 0.3   # A

        # Update full buffer (pos + color)
        pos_data = self.particles_pos.astype('f4')
        vertices = np.hstack([pos_data, colors]).ravel()
        self.vao.buffers[0].write(vertices.tobytes())

        self.vao.render(moderngl.POINTS)

    def closeEvent(self, event):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        super().closeEvent(event)


class ControlOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.hide_timer = QTimer(self)
        self.hide_timer.setInterval(5000)
        self.hide_timer.timeout.connect(self.fade_out)
        self.opacity_anim = None
        self.set_opacity(0.0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        flow_label = QtLabel("Flow Strength")
        flow_label.setStyleSheet("color: white;")
        self.flow_slider = QSlider(Qt.Orientation.Horizontal)
        self.flow_slider.setRange(0, 200)
        self.flow_slider.setValue(int(FLOW_STRENGTH * 100))
        self.flow_slider.valueChanged.connect(self.update_flow)

        particle_label = QtLabel("Particle Count")
        particle_label.setStyleSheet("color: white;")
        self.particle_slider = QSlider(Qt.Orientation.Horizontal)
        self.particle_slider.setRange(100, 2000)
        self.particle_slider.setValue(PARTICLE_COUNT)

        layout.addWidget(flow_label)
        layout.addWidget(self.flow_slider)
        layout.addWidget(particle_label)
        layout.addWidget(self.particle_slider)
        layout.addStretch()

        self.setStyleSheet("""
            QWidget { background: rgba(20, 20, 40, 120); border-radius: 12px; color: white; }
            QSlider::groove:horizontal { background: rgba(255,255,255,80); height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal { background: white; width: 14px; border-radius: 7px; }
        """)

    def update_flow(self, val):
        global FLOW_STRENGTH
        FLOW_STRENGTH = val / 100.0

    def mouseMoveEvent(self, event):
        self.fade_in()
        self.hide_timer.start()

    def fade_in(self):
        if self.opacity_anim and self.opacity_anim.state() == QPropertyAnimation.State.Running:
            self.opacity_anim.stop()
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(400)
        self.opacity_anim.setStartValue(self.windowOpacity())
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.opacity_anim.start()
        self.show()

    def fade_out(self):
        if self.opacity_anim and self.opacity_anim.state() == QPropertyAnimation.State.Running:
            self.opacity_anim.stop()
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(800)
        self.opacity_anim.setStartValue(self.windowOpacity())
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self.opacity_anim.finished.connect(self.hide)
        self.opacity_anim.start()

    def set_opacity(self, op):
        self.setWindowOpacity(op)


class AuroraWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # commented for debug
        # self.showFullScreen()  # commented for debug

        self.visualizer = VisualizerWidget(self)
        self.setCentralWidget(self.visualizer)

        self.overlay = ControlOverlay(self.visualizer)
        self.overlay.resize(400, 600)
        self.overlay.move(100, 100)  # visible position for debug
        self.overlay.show()

        self.setMouseTracking(True)
        self.setWindowTitle("Aurora Beats Debug")
        self.resize(800, 600)
        self.show()
        print("AuroraWindow created and shown")


def show_splash():
    print("Delayed show_splash - app is ready")
    splash = QSplashScreen()
    splash.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
    splash.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    label = QLabel("Aurora Beats", splash)
    font = QFont("Arial", 72, QFont.Weight.Bold)
    font.setItalic(True)
    label.setFont(font)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def paint_event(event):
        painter = QPainter(label)
        gradient = QLinearGradient(0, 0, label.width(), label.height())
        gradient.setColorAt(0, QColor(100, 200, 255))
        gradient.setColorAt(1, QColor(255, 100, 200))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(label.rect())
        painter.end()

    label.paintEvent = paint_event
    label.setStyleSheet("background: transparent; color: transparent;")

    screen = QApplication.primaryScreen().geometry()
    splash.setGeometry(screen)
    splash.show()
    splash.raise_()

    anim = QPropertyAnimation(splash, b"windowOpacity")
    anim.setDuration(1800)
    anim.setStartValue(1.0)
    anim.setEndValue(0.0)
    anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def on_fade_finish():
        splash.close()
        window = AuroraWindow()

    anim.finished.connect(on_fade_finish)
    QTimer.singleShot(2200, anim.start)


if __name__ == "__main__":
    print("Aurora Beats starting - imports")

    # Set attribute BEFORE QApplication instance
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
    print("Forced desktop OpenGL attribute (set early)")

    app = QApplication(sys.argv)
    print("App created")
    print("Qt platform:", app.platformName())
    print("Primary screen geometry:", QApplication.primaryScreen().geometry())

    QTimer.singleShot(0, show_splash)
    print("Entering app.exec()")
    sys.exit(app.exec())