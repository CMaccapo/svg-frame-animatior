import os
from watchdog.events import FileSystemEventHandler

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
