import os
import time
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication
import sys

# --- Settings ---
FPS = 24
DELAY = 1 / FPS

# --- Folder picker ---
root = tk.Tk()
root.withdraw()
folder = filedialog.askdirectory(title="Select folder containing SVGs")

if not folder:
    print("No folder selected. Exiting.")
    sys.exit()

# --- Prepare Qt app for SVG rendering ---
app = QApplication([])

# --- Load and render SVGs ---
svg_files = sorted([f for f in os.listdir(folder) if f.lower().endswith(".svg")])
if not svg_files:
    raise FileNotFoundError("No SVG files found in the selected folder.")

frames = []
for svg_file in svg_files:
    svg_path = os.path.join(folder, svg_file)
    renderer = QSvgRenderer(svg_path)

    # Define output image size
    size = renderer.defaultSize()
    image = QImage(size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)

    painter = QPainter(image)
    renderer.render(painter)
    painter.end()

    # Convert QImage → PIL Image for displaying
    buffer = image.bits().asstring(image.width() * image.height() * 4)
    frame = Image.frombytes("RGBA", (image.width(), image.height()), buffer)
    frames.append(frame)

# --- Display looping animation ---
plt.ion()
fig, ax = plt.subplots()

try:
    while True:  # Loop indefinitely
        for frame in frames:
            ax.clear()
            ax.imshow(frame)
            ax.axis("off")
            plt.pause(DELAY)
except KeyboardInterrupt:
    print("Animation stopped.")
    plt.ioff()
    plt.close()
