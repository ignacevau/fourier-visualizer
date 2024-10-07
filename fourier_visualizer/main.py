# fourier_visualizer/main.py

import json
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
        self.gl_widget: GLWidget = gl_widget
        self.init_ui()

    def init_ui(self):
        # Initialize controls with current settings from gl_widget
        # fmt: off
        self.checkBoxShowFourierPreview.setChecked(self.gl_widget.show_fourier_preview)
        self.checkBoxShowTrail.setChecked(self.gl_widget.show_drawing_tip_trail)
        self.fourier_preview_color = QColor(*[int(c * 255) for c in self.gl_widget.fourier_preview_color[:3]])
        self.trail_color = QColor(*[int(c * 255) for c in self.gl_widget.drawing_tip_trail_color[:3]])
        self.background_color = QColor(*[int(c * 255) for c in self.gl_widget.background_color[:3]])
        self.arrow_color = QColor(*[int(c * 255) for c in self.gl_widget.arrow_color[:3]])

        # Set initial opacity value
        self.sliderFourierOpacity.setValue(int(self.gl_widget.fourier_preview_opacity * 100))
        self.labelFourierOpacityValue.setText(f"{int(self.gl_widget.fourier_preview_opacity * 100)}%")

        # Set initial trail width
        self.spinBoxTrailWidth.setValue(self.gl_widget.drawing_tip_trail_width)

        # Set anti-aliasing passes
        self.spinBoxAntiAliasingPasses.setValue(self.gl_widget.num_anti_aliasing_passes)

        # Initialize arrow settings
        self.doubleSpinBoxArrowHeadMaxSize.setValue(self.gl_widget.arrow_head_max_size)
        self.doubleSpinBoxArrowLineMaxWidth.setValue(self.gl_widget.arrow_line_max_width)

        self.doubleSpinBoxArrowHeadBaseSize.setValue(self.gl_widget.arrow_head_base_size)
        self.doubleSpinBoxArrowHeadScalingFactor.setValue(self.gl_widget.arrow_head_scaling_factor)
        self.doubleSpinBoxArrowLineBaseWidth.setValue(self.gl_widget.arrow_line_base_width)
        self.doubleSpinBoxArrowLineScalingFactor.setValue(self.gl_widget.arrow_line_scaling_factor)
        self.comboBoxArrowCapType.setCurrentIndex(self.gl_widget.arrow_cap_type_index)

        # Connect signals to slots
        self.checkBoxShowFourierPreview.toggled.connect(self.update_show_fourier_preview)
        self.buttonFourierColor.clicked.connect(self.select_fourier_color)
        self.sliderFourierOpacity.valueChanged.connect(self.update_fourier_opacity)
        self.checkBoxShowTrail.toggled.connect(self.update_show_trail)
        self.buttonTrailColor.clicked.connect(self.select_trail_color)
        self.spinBoxTrailWidth.valueChanged.connect(self.update_trail_width)
        self.spinBoxAntiAliasingPasses.valueChanged.connect(self.update_anti_aliasing_passes)
        self.buttonBackgroundColor.clicked.connect(self.select_background_color)
        self.buttonArrowColor.clicked.connect(self.select_arrow_color)

        # Arrow signals
        self.doubleSpinBoxArrowHeadMaxSize.valueChanged.connect(self.update_arrow_head_max_size)
        self.doubleSpinBoxArrowLineMaxWidth.valueChanged.connect(self.update_arrow_line_max_width)
        
        self.doubleSpinBoxArrowHeadBaseSize.valueChanged.connect(self.update_arrow_head_base_size)
        self.doubleSpinBoxArrowHeadScalingFactor.valueChanged.connect(self.update_arrow_head_scaling_factor)
        self.doubleSpinBoxArrowLineBaseWidth.valueChanged.connect(self.update_arrow_line_base_width)
        self.doubleSpinBoxArrowLineScalingFactor.valueChanged.connect(self.update_arrow_line_scaling_factor)
        self.comboBoxArrowCapType.currentIndexChanged.connect(self.update_arrow_cap_type)
        # fmt: on

        # Dialog buttons
        self.buttonApply.clicked.connect(self.apply_settings)
        self.buttonOK.clicked.connect(self.ok_pressed)
        self.buttonCancel.clicked.connect(self.cancel_pressed)

        # Connect Save and Load buttons
        self.buttonSaveConfig.clicked.connect(self.save_config)
        self.buttonLoadConfig.clicked.connect(self.load_config)

    def save_config(self):
        # Ensure configurations directory exists
        config_dir = os.path.join(os.path.dirname(__file__), "configurations")
        os.makedirs(config_dir, exist_ok=True)
        # Open a file dialog to select the file to save
        default_file = os.path.join(config_dir, "config.json")
        config_file, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", default_file, "JSON Files (*.json)"
        )
        if config_file:
            # Collect settings into a dictionary
            settings = {
                "show_fourier_preview": self.checkBoxShowFourierPreview.isChecked(),
                "fourier_preview_color": self.fourier_preview_color.name(),
                "fourier_preview_opacity": self.sliderFourierOpacity.value(),
                "show_drawing_tip_trail": self.checkBoxShowTrail.isChecked(),
                "drawing_tip_trail_color": self.trail_color.name(),
                "drawing_tip_trail_width": self.spinBoxTrailWidth.value(),
                "num_anti_aliasing_passes": self.spinBoxAntiAliasingPasses.value(),
                "background_color": self.background_color.name(),
                "arrow_color": self.arrow_color.name(),
                "arrow_head_max_size": self.doubleSpinBoxArrowHeadMaxSize.value(),
                "arrow_line_max_width": self.doubleSpinBoxArrowLineMaxWidth.value(),
                "arrow_head_base_size": self.doubleSpinBoxArrowHeadBaseSize.value(),
                "arrow_head_scaling_factor": self.doubleSpinBoxArrowHeadScalingFactor.value(),
                "arrow_line_base_width": self.doubleSpinBoxArrowLineBaseWidth.value(),
                "arrow_line_scaling_factor": self.doubleSpinBoxArrowLineScalingFactor.value(),
            }
            # Save settings to JSON file
            try:
                with open(config_file, "w") as f:
                    json.dump(settings, f, indent=4)
                QMessageBox.information(
                    self, "Success", "Configuration saved successfully."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to save configuration: {str(e)}"
                )

    def load_config(self):
        config_dir = os.path.join(os.path.dirname(__file__), "configurations")
        os.makedirs(config_dir, exist_ok=True)
        config_file, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", config_dir, "JSON Files (*.json)"
        )
        if config_file:
            try:
                with open(config_file, "r") as f:
                    settings = json.load(f)
                # Update controls and gl_widget with loaded settings
                # fmt: off
                self.checkBoxShowFourierPreview.setChecked(settings.get("show_fourier_preview", True))
                fourier_preview_color_name = settings.get("fourier_preview_color", "#1AEBEB")
                self.fourier_preview_color = QColor(fourier_preview_color_name)
                self.sliderFourierOpacity.setValue(settings.get("fourier_preview_opacity", 25))
                self.labelFourierOpacityValue.setText(f"{settings.get('fourier_preview_opacity', 25)}%")
                self.checkBoxShowTrail.setChecked(settings.get("show_drawing_tip_trail", True))
                trail_color_name = settings.get("drawing_tip_trail_color", "#1AEBEB")
                self.trail_color = QColor(trail_color_name)
                self.spinBoxTrailWidth.setValue(settings.get("drawing_tip_trail_width", 2.0))
                self.spinBoxAntiAliasingPasses.setValue(settings.get("num_anti_aliasing_passes", 1))
                background_color_name = settings.get("background_color", "#000000")
                self.background_color = QColor(background_color_name)
                arrow_color_name = settings.get("arrow_color", "#FFFFFF")
                self.arrow_color = QColor(arrow_color_name)
                # Arrow settings
                self.doubleSpinBoxArrowHeadMaxSize.setValue(settings.get("arrow_head_max_size", 20.0))
                self.doubleSpinBoxArrowLineMaxWidth.setValue(settings.get("arrow_line_max_width", 1.5))

                self.doubleSpinBoxArrowHeadBaseSize.setValue(settings.get("arrow_head_base_size", 20.0))
                self.doubleSpinBoxArrowHeadScalingFactor.setValue(settings.get("arrow_head_scaling_factor", 0.5))
                self.doubleSpinBoxArrowLineBaseWidth.setValue(settings.get("arrow_line_base_width", 1.5))
                self.doubleSpinBoxArrowLineScalingFactor.setValue(settings.get("arrow_line_scaling_factor", 0.5))
                # fmt: on
                # Apply the settings to gl_widget
                self.apply_settings()
                QMessageBox.information(
                    self, "Success", "Configuration loaded successfully."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to load configuration: {str(e)}"
                )

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

    def select_arrow_color(self):
        color = QColorDialog.getColor(self.arrow_color, self)
        if color.isValid():
            self.arrow_color = color
            rgb = color.getRgbF()[:3]
            self.gl_widget.arrow_color = (*rgb, 1.0)
            self.gl_widget.update()

    # Methods for arrow settings
    def update_arrow_head_max_size(self, value):
        self.gl_widget.arrow_head_max_size = value
        self.gl_widget.update()

    def update_arrow_line_max_width(self, value):
        self.gl_widget.arrow_line_max_width = value
        self.gl_widget.update()

    def update_arrow_head_base_size(self, value):
        self.gl_widget.arrow_head_base_size = value
        self.gl_widget.update()

    def update_arrow_head_scaling_factor(self, value):
        self.gl_widget.arrow_head_scaling_factor = value
        self.gl_widget.update()

    def update_arrow_line_base_width(self, value):
        self.gl_widget.arrow_line_base_width = value
        self.gl_widget.update()

    def update_arrow_line_scaling_factor(self, value):
        self.gl_widget.arrow_line_scaling_factor = value
        self.gl_widget.update()

    def update_arrow_cap_type(self, index):
        self.gl_widget.arrow_cap_type_index = index
        self.gl_widget.update()

    def apply_settings(self):
        # fmt:off
        # Update gl_widget settings from the dialog controls
        self.gl_widget.show_fourier_preview = self.checkBoxShowFourierPreview.isChecked()
        self.gl_widget.show_drawing_tip_trail = self.checkBoxShowTrail.isChecked()
        self.gl_widget.fourier_preview_opacity = self.sliderFourierOpacity.value() / 100.0
        self.gl_widget.drawing_tip_trail_width = self.spinBoxTrailWidth.value()
        self.gl_widget.num_anti_aliasing_passes = self.spinBoxAntiAliasingPasses.value()

        # Update colors
        self.gl_widget.fourier_preview_color = (*[c / 255.0 for c in self.fourier_preview_color.getRgb()[:3]],self.gl_widget.fourier_preview_opacity,)
        self.gl_widget.drawing_tip_trail_color = (*[c / 255.0 for c in self.trail_color.getRgb()[:3]],)
        self.gl_widget.background_color = (*[c / 255.0 for c in self.background_color.getRgb()[:3]],1.0,)
        self.gl_widget.arrow_color = (*[c / 255.0 for c in self.arrow_color.getRgb()[:3]],1.0,)

        # Apply arrow settings
        self.gl_widget.arrow_head_max_size = self.doubleSpinBoxArrowHeadMaxSize.value()
        self.gl_widget.arrow_line_max_width = self.doubleSpinBoxArrowLineMaxWidth.value()

        self.gl_widget.arrow_head_base_size = self.doubleSpinBoxArrowHeadBaseSize.value()
        self.gl_widget.arrow_head_scaling_factor = self.doubleSpinBoxArrowHeadScalingFactor.value()
        self.gl_widget.arrow_line_base_width = self.doubleSpinBoxArrowLineBaseWidth.value()
        self.gl_widget.arrow_line_scaling_factor = self.doubleSpinBoxArrowLineScalingFactor.value()
        self.gl_widget.arrow_cap_type_index = self.comboBoxArrowCapType.currentIndex()
        # fmt:on

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
        self.buttonResetView.clicked.connect(self.reset_view)
        self.buttonOpenSettings.clicked.connect(self.open_settings_dialog)

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

    def reset_view(self):
        # Reset speed
        default_speed = 50
        self.spinBoxSpeed.setValue(default_speed)
        self.gl_widget.set_speed(default_speed)
        # Reset follow toggle
        self.checkBoxFollow.setChecked(False)
        self.gl_widget.set_follow_mode(False)
        # Reset trail length
        default_trail_length = 100
        self.spinBoxTrailLength.setValue(default_trail_length)
        self.gl_widget.max_trail_length = default_trail_length
        # Reset zoom
        default_zoom = 1
        self.spinBoxZoom.setValue(default_zoom)
        self.gl_widget.set_zoom_level(default_zoom)

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
