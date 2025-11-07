import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QMessageBox
)
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from PyQt5.QtCore import QTimer, Qt, QByteArray
from PyQt5.QtGui import QImage, QPainter
from watchdog.observers import Observer
from PIL import Image  # <-- NEW (requires Pillow)
from .folder_watcher import SvgFolderHandler


class SvgAnimator(QWidget):
    def __init__(self, svg_folder, fps=24):
        super().__init__()
        self.setWindowTitle("SVG Player")
        self.fps = fps
        self.svg_folder = svg_folder
        self.current_index = 0
        self.is_running = True

        self.svg_files = []

        # --- Main layout ---
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # SVG display widget
        self.svg_widget = QSvgWidget(self)

        # A layout to center the SVG in the window
        self.svg_container = QHBoxLayout()
        self.svg_container.addStretch(1)
        self.svg_container.addWidget(self.svg_widget, alignment=Qt.AlignCenter)
        self.svg_container.addStretch(1)
        self.main_layout.addLayout(self.svg_container)

        # Control panel layout
        self.controls_layout = QHBoxLayout()

        # Start/Pause button
        self.start_stop_btn = QPushButton("Pause")
        self.start_stop_btn.clicked.connect(self.toggle_animation)
        self.controls_layout.addWidget(self.start_stop_btn)

        # Step Back button
        self.prev_btn = QPushButton("<")
        self.prev_btn.clicked.connect(self.previous_frame)
        self.controls_layout.addWidget(self.prev_btn)

        # Step Forward button
        self.next_btn = QPushButton(">")
        self.next_btn.clicked.connect(self.next_frame_manual)
        self.controls_layout.addWidget(self.next_btn)

        # FPS slider
        self.fps_label = QLabel(f"FPS: {self.fps}")
        self.controls_layout.addWidget(self.fps_label)
        self.fps_slider = QSlider(Qt.Horizontal)
        self.fps_slider.setMinimum(1)
        self.fps_slider.setMaximum(120)
        self.fps_slider.setValue(self.fps)
        self.fps_slider.valueChanged.connect(self.update_fps)
        self.controls_layout.addWidget(self.fps_slider)

        # --- NEW: Export as GIF button ---
        self.export_btn = QPushButton("Export as GIF")
        self.export_btn.clicked.connect(self.export_gif)
        self.controls_layout.addWidget(self.export_btn)

        self.main_layout.addLayout(self.controls_layout)

        # Timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame_timer)
        self.timer.start(int(1000 / self.fps))

        # Folder watcher
        self.observer = Observer()
        self.handler = SvgFolderHandler(self)
        self.observer.schedule(self.handler, self.svg_folder, recursive=False)
        self.observer.start()

        # Load SVG files after widget is ready
        self.refresh_svg_files()

    # --- SVG management ---
    def refresh_svg_files(self):
        files = sorted([
            os.path.join(self.svg_folder, f)
            for f in os.listdir(self.svg_folder) if f.lower().endswith(".svg")
        ])
        if files != self.svg_files:
            self.svg_files = files
            if self.current_index >= len(self.svg_files):
                self.current_index = 0
            if self.svg_files:
                first_renderer = QSvgRenderer(self.svg_files[0])
                if first_renderer.isValid():
                    size = first_renderer.defaultSize()
                    self.svg_widget.setFixedSize(size)
                self._update_svg()

    # --- Export as GIF ---
    def export_gif(self):
        if not self.svg_files:
            QMessageBox.warning(self, "No Frames", "No SVG frames to export.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save GIF", "", "GIF Files (*.gif)"
        )
        if not save_path:
            return

        images = []
        delay = int(1000 / self.fps)  # duration per frame in ms

        for svg_file in self.svg_files:
            renderer = QSvgRenderer(svg_file)
            size = renderer.defaultSize()
            image = QImage(size, QImage.Format_ARGB32)
            image.fill(Qt.transparent)

            painter = QPainter(image)
            renderer.render(painter)
            painter.end()

            # Convert QImage → PIL Image
            buffer = image.bits().asstring(image.byteCount())
            pil_image = Image.frombuffer(
                "RGBA", (image.width(), image.height()), buffer, "raw", "BGRA", 0, 1
            ).convert("RGBA")
            images.append(pil_image)

        try:
            images[0].save(
                save_path,
                save_all=True,
                append_images=images[1:],
                duration=delay,
                loop=0,
                disposal=2,
                transparency=0,
            )
            QMessageBox.information(self, "Export Complete", f"GIF saved to:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error exporting GIF:\n{e}")

    # --- Frame advancing helpers ---
    def _advance_frame(self, step):
        if not self.svg_files:
            return
        self.current_index = (self.current_index + step) % len(self.svg_files)
        self._update_svg()

    def next_frame_timer(self):
        if self.is_running:
            self._advance_frame(1)

    def next_frame_manual(self):
        self._advance_frame(1)

    def previous_frame(self):
        self._advance_frame(-1)

    # --- GUI controls ---
    def toggle_animation(self):
        self.is_running = not self.is_running
        self.start_stop_btn.setText("Pause" if self.is_running else "Start")

    def update_fps(self, value):
        self.fps = max(1, value)
        self.fps_label.setText(f"FPS: {self.fps}")
        self.timer.setInterval(int(1000 / self.fps))

    # --- Update SVG ---
    def _update_svg(self):
        if not self.svg_files:
            self.svg_widget.load(b'')
            self.setWindowTitle("SVG Animator - No frames")
            return

        current_file = os.path.basename(self.svg_files[self.current_index])
        self.svg_widget.load(self.svg_files[self.current_index])
        self.setWindowTitle(
            f"SVG Animator - ({self.current_index + 1}/{len(self.svg_files)}) {current_file}"
        )

    def closeEvent(self, event):
        self.observer.stop()
        self.observer.join()
        event.accept()
