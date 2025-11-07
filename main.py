import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import QTimer, Qt
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class SvgFolderHandler(FileSystemEventHandler):
    """Watchdog handler to update SVG list dynamically."""
    def __init__(self, animator):
        self.animator = animator

    def on_created(self, event):
        if event.src_path.lower().endswith(".svg"):
            self.animator.refresh_svg_files()

    def on_deleted(self, event):
        if event.src_path.lower().endswith(".svg"):
            self.animator.refresh_svg_files()

class SvgAnimator(QWidget):
    def __init__(self, svg_folder, fps=24):
        super().__init__()
        self.fps = fps
        self.svg_folder = svg_folder
        self.current_index = 0

        self.svg_files = []
        self.refresh_svg_files()  # Initial load

        # Set up the SVG display widget
        self.svg_widget = QSvgWidget(self.svg_files[self.current_index] if self.svg_files else None, self)
        self.svg_widget.setGeometry(0, 0, 800, 600)
        self.resize(800, 600)

        # Timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)
        self.timer.start(int(1000 / self.fps))

        # Watch the folder
        self.observer = Observer()
        self.handler = SvgFolderHandler(self)
        self.observer.schedule(self.handler, self.svg_folder, recursive=False)
        self.observer.start()

    def refresh_svg_files(self):
        files = sorted([os.path.join(self.svg_folder, f) 
                        for f in os.listdir(self.svg_folder) if f.lower().endswith(".svg")])
        if files != self.svg_files:
            self.svg_files = files
            # Adjust current index to avoid out-of-range errors
            if self.current_index >= len(self.svg_files):
                self.current_index = 0

    def next_frame(self):
        if not self.svg_files:
            return
        self.current_index = (self.current_index + 1) % len(self.svg_files)
        self.svg_widget.load(self.svg_files[self.current_index])

    def closeEvent(self, event):
        self.observer.stop()
        self.observer.join()
        event.accept()

def select_folder():
    app = QApplication(sys.argv)
    folder = QFileDialog.getExistingDirectory(None, "Select folder containing SVGs")
    if not folder:
        print("No folder selected. Exiting.")
        sys.exit()
    animator = SvgAnimator(folder, fps=24)
    animator.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    select_folder()
