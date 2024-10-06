# fourier_visualizer/main.py

import os
import sys

from PyQt6 import uic
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QColorDialog,
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
)

from .core.fourier_transform import compute_fourier_series, fourier_series_function
from .utils.svg_loader import load_svg
from .widgets.gl_widget import GLWidget


class SettingsDialog(QDialog):
    def __init__(self, parent=None, gl_widget=None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "settings_dialog.ui")
        uic.loadUi(ui_path, self)
        self.gl_widget = gl_widget
        self.init_ui()

    def init_ui(self):
        # Initialize controls with current settings from gl_widget
        self.checkBoxShowFourierPreview.setChecked(self.gl_widget.show_fourier_preview)
        self.checkBoxShowTrail.setChecked(self.gl_widget.show_drawing_tip_trail)
        self.fourier_preview_color = QColor(
            *[int(c * 255) for c in self.gl_widget.fourier_preview_color[:3]]
        )
        self.trail_color = QColor(
            *[int(c * 255) for c in self.gl_widget.drawing_tip_trail_color[:3]]
        )
        self.background_color = QColor(
            *[int(c * 255) for c in self.gl_widget.background_color[:3]]
        )
        # Set initial opacity value
        self.sliderFourierOpacity.setValue(
            int(self.gl_widget.fourier_preview_opacity * 100)
        )
        self.labelFourierOpacityValue.setText(
            f"{int(self.gl_widget.fourier_preview_opacity * 100)}%"
        )
        # Set initial trail width
        self.spinBoxTrailWidth.setValue(self.gl_widget.drawing_tip_trail_width)
        # Set anti-aliasing passes
        self.spinBoxAntiAliasingPasses.setValue(self.gl_widget.num_anti_aliasing_passes)
        # Set arrow head sizes
        self.doubleSpinBoxArrowHeadMinSize.setValue(self.gl_widget.arrow_head_min_size)
        self.doubleSpinBoxArrowHeadMaxSize.setValue(self.gl_widget.arrow_head_max_size)
        # Set arrow line widths
        self.doubleSpinBoxArrowLineMinWidth.setValue(
            self.gl_widget.arrow_line_min_width
        )
        self.doubleSpinBoxArrowLineMaxWidth.setValue(
            self.gl_widget.arrow_line_max_width
        )

        # Connect signals to slots
        self.checkBoxShowFourierPreview.toggled.connect(
            self.update_show_fourier_preview
        )
        self.buttonFourierColor.clicked.connect(self.select_fourier_color)
        self.sliderFourierOpacity.valueChanged.connect(self.update_fourier_opacity)
        self.checkBoxShowTrail.toggled.connect(self.update_show_trail)
        self.buttonTrailColor.clicked.connect(self.select_trail_color)
        self.spinBoxTrailWidth.valueChanged.connect(self.update_trail_width)
        self.spinBoxAntiAliasingPasses.valueChanged.connect(
            self.update_anti_aliasing_passes
        )
        self.buttonBackgroundColor.clicked.connect(self.select_background_color)
        self.doubleSpinBoxArrowHeadMinSize.valueChanged.connect(
            self.update_arrow_head_min_size
        )
        self.doubleSpinBoxArrowHeadMaxSize.valueChanged.connect(
            self.update_arrow_head_max_size
        )
        self.doubleSpinBoxArrowLineMinWidth.valueChanged.connect(
            self.update_arrow_line_min_width
        )
        self.doubleSpinBoxArrowLineMaxWidth.valueChanged.connect(
            self.update_arrow_line_max_width
        )

        # Dialog buttons
        self.buttonApply.clicked.connect(self.apply_settings)
        self.buttonOK.clicked.connect(self.ok_pressed)
        self.buttonCancel.clicked.connect(self.cancel_pressed)

    def update_show_fourier_preview(self, checked):
        self.gl_widget.show_fourier_preview = checked
        self.gl_widget.update()

    def select_fourier_color(self):
        color = QColorDialog.getColor(self.fourier_preview_color, self)
        if color.isValid():
            self.fourier_preview_color = color
            rgb = color.getRgbF()[:3]
            self.gl_widget.fourier_preview_color = (
                *rgb,
                self.gl_widget.fourier_preview_opacity,
            )
            self.gl_widget.update()

    def update_fourier_opacity(self, value):
        opacity = value / 100.0
        self.labelFourierOpacityValue.setText(f"{value}%")
        self.gl_widget.fourier_preview_opacity = opacity
        rgb = self.gl_widget.fourier_preview_color[:3]
        self.gl_widget.fourier_preview_color = (*rgb, opacity)
        self.gl_widget.update()

    def update_show_trail(self, checked):
        self.gl_widget.show_drawing_tip_trail = checked
        self.gl_widget.update()

    def select_trail_color(self):
        color = QColorDialog.getColor(self.trail_color, self)
        if color.isValid():
            self.trail_color = color
            rgb = color.getRgbF()[:3]
            self.gl_widget.drawing_tip_trail_color = rgb
            self.gl_widget.update()

    def update_trail_width(self, value):
        self.gl_widget.drawing_tip_trail_width = value
        self.gl_widget.update()

    def update_anti_aliasing_passes(self, value):
        self.gl_widget.num_anti_aliasing_passes = value
        self.gl_widget.update()

    def select_background_color(self):
        color = QColorDialog.getColor(self.background_color, self)
        if color.isValid():
            self.background_color = color
            rgb = color.getRgbF()[:3]
            self.gl_widget.background_color = (*rgb, 1.0)
            self.gl_widget.update()

    def update_arrow_head_min_size(self, value):
        self.gl_widget.arrow_head_min_size = value
        self.gl_widget.update()

    def update_arrow_head_max_size(self, value):
        self.gl_widget.arrow_head_max_size = value
        self.gl_widget.update()

    def update_arrow_line_min_width(self, value):
        self.gl_widget.arrow_line_min_width = value
        self.gl_widget.update()

    def update_arrow_line_max_width(self, value):
        self.gl_widget.arrow_line_max_width = value
        self.gl_widget.update()

    def apply_settings(self):
        self.gl_widget.update()

    def ok_pressed(self):
        self.apply_settings()
        self.accept()

    def cancel_pressed(self):
        self.reject()


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
        self.actionExit.triggered.connect(self.close)
        self.actionOpenSettings.triggered.connect(self.open_settings_dialog)
        self.actionAbout.triggered.connect(self.show_about_dialog)
        self.buttonTransform.clicked.connect(self.transform_svg)
        self.spinBoxSpeed.valueChanged.connect(self.update_speed)
        self.buttonPlayStop.toggled.connect(self.toggle_animation)
        # Connect the checkbox and spinbox signals
        self.checkBoxFollow.stateChanged.connect(self.toggle_follow_mode)
        self.spinBoxZoom.valueChanged.connect(self.update_zoom_level)
        # Connect the trail length spinbox signal
        self.spinBoxTrailLength.valueChanged.connect(self.update_trail_length)

        self.svg_function = None
        self.term_data = None

        # Replace the placeholder widget with our GLWidget
        self.gl_widget = GLWidget(self)
        self.verticalLayoutMain.replaceWidget(self.openGLWidget, self.gl_widget)
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

    def toggle_animation(self, checked):
        if checked:
            self.buttonPlayStop.setText("Stop")
            self.gl_widget.start_animation()
        else:
            self.buttonPlayStop.setText("Play")
            self.gl_widget.stop_animation()

    def open_settings_dialog(self):
        dialog = SettingsDialog(self, self.gl_widget)
        dialog.exec()

    def show_about_dialog(self):
        QMessageBox.information(
            self,
            "About Fourier Visualizer",
            "Fourier Visualizer\nVersion 1.0\nDeveloped by Ignace Vauterin.",
        )


def main():
    app = QApplication(sys.argv)
    window = MainApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
