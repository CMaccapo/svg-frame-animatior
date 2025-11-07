import sys
from PyQt5.QtWidgets import QApplication, QFileDialog
from .animator import SvgAnimator
from .config import DEFAULT_FPS

def select_folder():
    app = QApplication(sys.argv)
    folder = QFileDialog.getExistingDirectory(None, "Select folder containing SVGs")
    if not folder:
        print("No folder selected. Exiting.")
        sys.exit()
    animator = SvgAnimator(folder, fps=DEFAULT_FPS)
    animator.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    select_folder()
