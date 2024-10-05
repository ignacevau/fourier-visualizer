# fourier_visualizer/main.py

import os
import sys

from PyQt6 import uic
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox

from .core.fourier_transform import compute_fourier_series, fourier_series_function
from .utils.svg_loader import load_svg
from .widgets.gl_widget import GLWidget


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "main_window.ui")
        uic.loadUi(ui_path, self)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Fourier Visualizer")
        self.actionOpenSVG.triggered.connect(self.open_svg)
        self.actionLoadExample.triggered.connect(self.load_example)
        self.buttonTransform.clicked.connect(self.transform_svg)
        self.spinBoxSpeed.valueChanged.connect(self.update_speed)
        self.buttonPlay.clicked.connect(self.start_animation)
        self.buttonStop.clicked.connect(self.stop_animation)
        # Connect the checkbox and spinbox signals
        self.checkBoxFollow.stateChanged.connect(self.toggle_follow_mode)
        self.spinBoxZoom.valueChanged.connect(self.update_zoom_level)
        # Connect the trail length spinbox signal
        self.spinBoxTrailLength.valueChanged.connect(self.update_trail_length)

        self.svg_function = None
        self.term_data = None

        # Replace the placeholder widget with our GLWidget
        self.gl_widget = GLWidget(self)
        self.verticalLayout.replaceWidget(self.openGLWidget, self.gl_widget)
        self.openGLWidget.deleteLater()
        self.openGLWidget = self.gl_widget

        # Connect the fps_updated signal to the update_fps_label slot
        self.gl_widget.fps_updated.connect(self.update_fps_label)

        # Set initial speed
        self.gl_widget.set_speed(self.spinBoxSpeed.value())

        # Maximize the window
        self.showMaximized()

    @pyqtSlot(float)
    def update_fps_label(self, fps):
        self.labelFPS.setText(f"FPS: {fps:.1f}")

    def update_trail_length(self, value):
        self.gl_widget.max_trail_length = value

    def open_svg(self):
        svg_file, _ = QFileDialog.getOpenFileName(
            self, "Open SVG File", "", "SVG Files (*.svg)"
        )
        if svg_file:
            try:
                self.svg_function = load_svg(svg_file)
                self.statusbar.showMessage(f"Loaded SVG: {os.path.basename(svg_file)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def toggle_follow_mode(self, state):
        is_checked = self.checkBoxFollow.isChecked()
        self.spinBoxZoom.setEnabled(is_checked)
        self.gl_widget.set_follow_mode(is_checked)

    def update_zoom_level(self, value):
        self.gl_widget.set_zoom_level(value)

    def load_example(self):
        example_dir = os.path.join(os.path.dirname(__file__), "examples")
        svg_file, _ = QFileDialog.getOpenFileName(
            self, "Open Example SVG", example_dir, "SVG Files (*.svg)"
        )
        if svg_file:
            try:
                self.svg_function = load_svg(svg_file)
                self.statusbar.showMessage(
                    f"Loaded Example SVG: {os.path.basename(svg_file)}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def transform_svg(self):
        if self.svg_function is None:
            QMessageBox.warning(self, "Warning", "Please load an SVG file first.")
            return

        depth = self.spinBoxDepth.value()
        self.statusbar.showMessage(f"Computing Fourier series with depth {depth}...")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        try:
            self.term_data = compute_fourier_series(self.svg_function, depth)
            self.gl_widget.set_term_data(
                self.term_data, lambda t: fourier_series_function(t, self.term_data)
            )
            self.statusbar.showMessage(f"Fourier series computed with depth {depth}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            QApplication.restoreOverrideCursor()

    def update_speed(self, value):
        self.gl_widget.set_speed(value)

    def start_animation(self):
        self.gl_widget.start_animation()

    def stop_animation(self):
        self.gl_widget.stop_animation()


def main():
    app = QApplication(sys.argv)
    window = MainApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
