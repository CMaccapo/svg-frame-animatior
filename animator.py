import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QSizePolicy
)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFontMetrics
from watchdog.observers import Observer
from folder_watcher import SvgFolderHandler
from config import WINDOW_WIDTH, WINDOW_HEIGHT

class SvgAnimator(QWidget):
    def __init__(self, svg_folder, fps=24):
        super().__init__()
        self.fps = fps
        self.svg_folder = svg_folder
        self.current_index = 0
        self.is_running = True

        self.svg_files = []

        # --- Main layout ---
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # SVG display widget
        self.svg_widget = QSvgWidget(None, self)
        self.svg_widget.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.main_layout.addWidget(self.svg_widget)

        # Status label (overlay in bottom-right corner)
        self.status_label = QLabel(self)
        self.status_label.setStyleSheet(
            "background-color: rgba(0, 0, 0, 120); color: white; padding: 4px; border-radius: 3px;"
        )
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.status_label.raise_()  # Make sure it’s above the SVG widget

        # Control panel layout
        self.controls_layout = QHBoxLayout()

        # Start/Pause button
        self.start_stop_btn = QPushButton("Pause")
        self.start_stop_btn.clicked.connect(self.toggle_animation)
        self.controls_layout.addWidget(self.start_stop_btn)

        # Step Back button
        self.prev_btn = QPushButton("⏮")
        self.prev_btn.clicked.connect(self.previous_frame)
        self.controls_layout.addWidget(self.prev_btn)

        # Step Forward button
        self.next_btn = QPushButton("⏭")
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
                self._update_svg()

    # --- Frame advancing helpers ---
    def _advance_frame(self, step):
        if not self.svg_files:
            return
        self.current_index = (self.current_index + step) % len(self.svg_files)
        self._update_svg()

    # Timer-driven animation
    def next_frame_timer(self):
        if self.is_running:
            self._advance_frame(1)

    # Manual stepping
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

    # --- Update SVG and status label ---
    def _update_svg(self):
        if not self.svg_files:
            self.svg_widget.load(None)
            self.status_label.setText("")
            return
        current_file = os.path.basename(self.svg_files[self.current_index])
        self.svg_widget.load(self.svg_files[self.current_index])
        full_text = f"({self.current_index + 1}/{len(self.svg_files)}) {current_file}"
        
        # Elide text if too long
        max_width = self.svg_widget.width() - 20  # padding from edges
        metrics = QFontMetrics(self.status_label.font())
        elided_text = metrics.elidedText(full_text, Qt.ElideLeft, max_width)
        self.status_label.setText(elided_text)
        self.status_label.adjustSize()

    # --- Window close handling ---
    def closeEvent(self, event):
        self.observer.stop()
        self.observer.join()
        event.accept()

    # --- Resize SVG and overlay status ---
    def resizeEvent(self, event):
        # Resize SVG
        self.svg_widget.resize(self.width(), self.height() - 50)

        # Recalculate elided text based on new width
        self._update_svg()

        # Position status label in bottom-right corner
        label_width = self.status_label.width()
        label_height = self.status_label.height()
        self.status_label.move(
            max(0, self.svg_widget.width() - label_width - 10),
            max(0, self.svg_widget.height() - label_height - 10)
        )

        super().resizeEvent(event)
