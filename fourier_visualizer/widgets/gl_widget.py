# fourier_visualizer/widgets/gl_widget.py

import time

import numpy as np
from OpenGL.GL import *
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtOpenGLWidgets import QOpenGLWidget


class GLWidget(QOpenGLWidget):
    fps_updated = pyqtSignal(float)  # Define a new signal for FPS updates

    def __init__(self, parent=None):
        super().__init__(parent)
        self.term_data = None
        self.margin = 50  # Margin in pixels
        self.background_color = (0.0, 0.0, 0.0, 1.0)  # Black background
        self.drawing_color = (0.0, 1.0, 0.0)  # Green lines
        self.speed = 0.1
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.start_time = time.time()
        self.current_time = 0
        self.scale_factor = 1.0
        self.drawing_center = (0, 0)
        self.is_animating = True
        self.follow_mode = False
        self.zoom_level = 1.0
        self.last_frame_time = None
        self.trail_points = []  # List to store trail points
        self.max_trail_length = 100  # Maximum number of points in the trail
        self.trail_color = (1.0, 1.0, 1.0)  # White color for the trail
        self.drawing_tip_color = (1.0, 1.0, 1.0)  # White color for the drawing tip

    def initializeGL(self):
        glClearColor(*self.background_color)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.animation_timer.start()

    def set_follow_mode(self, enabled):
        self.follow_mode = enabled
        self.update()

    def set_zoom_level(self, zoom_level):
        self.zoom_level = zoom_level
        self.update()

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.update_projection()
        self.update()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if self.term_data is None:
            return

        # Update trail with current tip position
        self.update_trail()

        # Draw the Fourier drawing first
        self.draw_fourier_drawing()

        # Draw the trail before drawing the tip
        self.draw_trail()

        # Draw the rotating vectors (arrows)
        self.draw_rotating_vectors()

        # Calculate FPS
        current_time = time.time()
        if self.last_frame_time is not None:
            delta_time = current_time - self.last_frame_time
            if delta_time > 0:
                fps = 1.0 / delta_time
                self.fps_updated.emit(fps)  # Emit the FPS value
        self.last_frame_time = current_time

    def update_trail(self):
        # Get current tip position
        tip_x, tip_y = self.get_current_tip_position()
        # Add to trail
        self.trail_points.insert(0, (tip_x, tip_y))
        # Limit trail length
        if len(self.trail_points) > self.max_trail_length:
            self.trail_points.pop()

    def draw_trail(self):
        if not self.trail_points:
            return

        glPushMatrix()
        if self.follow_mode:
            tip_x, tip_y = self.trail_points[0]
            translate_x = self.width() / 2 - tip_x * self.zoom_level
            translate_y = self.height() / 2 - tip_y * self.zoom_level
            glTranslatef(translate_x, translate_y, 0.0)
            glScalef(self.zoom_level, self.zoom_level, 1.0)

        # Enable blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glLineWidth(2.0)
        glBegin(GL_LINE_STRIP)
        num_points = len(self.trail_points)
        for i, (x, y) in enumerate(self.trail_points):
            # Calculate opacity from 0.9 (90%) to 0.0
            alpha = 0.9 * (1.0 - (i / (num_points - 1))) if num_points > 1 else 0.9
            glColor4f(*self.trail_color, alpha)
            glVertex2f(x, y)
        glEnd()

        # Disable blending after drawing the trail
        glDisable(GL_BLEND)
        glPopMatrix()

    def update_projection(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        width = self.width()
        height = self.height()
        glOrtho(0, width, height, 0, -1, 1)  # Top-left corner is (0,0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def scale_and_translate(self, x_values, y_values):
        # Get the bounding box of the drawing
        min_x, max_x = np.min(x_values), np.max(x_values)
        min_y, max_y = np.min(y_values), np.max(y_values)

        # Calculate scaling factors
        drawable_width = self.width() - 2 * self.margin
        drawable_height = self.height() - 2 * self.margin

        drawing_width = max_x - min_x
        drawing_height = max_y - min_y

        scale_x = drawable_width / drawing_width if drawing_width != 0 else 1
        scale_y = drawable_height / drawing_height if drawing_height != 0 else 1

        scale = min(scale_x, scale_y)
        self.scale_factor = scale  # Save scale factor for vectors

        # Calculate the center of the drawing
        center_x = self.width() / 2
        center_y = self.height() / 2
        self.drawing_center = (center_x, center_y)

        # Apply scaling and translation
        x_values *= scale
        y_values *= scale

        x_values += center_x
        y_values += center_y

        return x_values, y_values

    def compute_scaling(self):
        # Compute the path once to determine scaling
        t_values = np.linspace(0, 1, 1000)  # Use 1,000 points for performance
        self.t_values = t_values  # Store t_values for trail calculation
        fourier_values = np.vectorize(lambda t: self.fourier_series_function(t))(
            t_values
        )
        self.path_x = fourier_values.real
        self.path_y = fourier_values.imag
        self.scaled_x, self.scaled_y = self.scale_and_translate(
            self.path_x, self.path_y
        )

    def draw_fourier_drawing(self):
        glPushMatrix()
        if self.follow_mode:
            tip_x, tip_y = self.get_current_tip_position()
            translate_x = self.width() / 2 - tip_x * self.zoom_level
            translate_y = self.height() / 2 - tip_y * self.zoom_level
            glTranslatef(translate_x, translate_y, 0.0)
            glScalef(self.zoom_level, self.zoom_level, 1.0)

        glColor3f(*self.drawing_color)
        glLineWidth(1.0)
        glBegin(GL_LINE_STRIP)
        for x, y in zip(self.scaled_x, self.scaled_y):
            glVertex2f(x, y)
        glEnd()
        glPopMatrix()

    def get_current_tip_position(self):
        x_pos, y_pos = self.drawing_center

        # Compute the current tip position based on the rotating vectors
        terms = sorted(self.term_data, key=lambda term: abs(term["k"]))

        for term in terms:
            k = term["k"]
            c = term["c"]
            angle = 2 * np.pi * k * self.current_time
            vector = c * np.exp(1j * angle)
            scaled_vector_x, scaled_vector_y = self.scale_vector(
                vector.real, vector.imag
            )
            x_pos += scaled_vector_x
            y_pos += scaled_vector_y

        return x_pos, y_pos

    def draw_rotating_vectors(self):
        glPushMatrix()
        if self.follow_mode:
            # Apply the same translation and scaling as in draw_fourier_drawing
            tip_x, tip_y = self.get_current_tip_position()
            translate_x = self.width() / 2 - tip_x * self.zoom_level
            translate_y = self.height() / 2 - tip_y * self.zoom_level
            glTranslatef(translate_x, translate_y, 0.0)
            glScalef(self.zoom_level, self.zoom_level, 1.0)
            glLineWidth(1.0)

        glColor3f(1.0, 1.0, 1.0)  # White color for vectors

        # Use the center of the Fourier drawing as the starting position
        x_pos, y_pos = self.drawing_center

        # Sort terms by increasing absolute value of k (frequency)
        terms = [term for term in self.term_data if term["k"] != 0]
        terms.sort(key=lambda term: abs(term["k"]))

        for term in terms:
            k = term["k"]
            c = term["c"]
            freq = 2 * np.pi * k
            angle = freq * self.current_time
            vector = c * np.exp(1j * angle)
            vector_x = vector.real
            vector_y = vector.imag

            # Scale the vector
            scaled_vector_x, scaled_vector_y = self.scale_vector(vector_x, vector_y)

            end_x = x_pos + scaled_vector_x
            end_y = y_pos + scaled_vector_y

            # Calculate magnitude for line width and arrow size
            magnitude = np.hypot(scaled_vector_x, scaled_vector_y)
            line_width = min(2, max(0.2, magnitude / 90))
            arrow_size = min(20, max(0.4, magnitude / 20))

            glLineWidth(line_width)
            glBegin(GL_LINES)
            glVertex2f(x_pos, y_pos)
            glVertex2f(end_x, end_y)
            glEnd()

            # Draw arrowhead
            self.draw_arrowhead(x_pos, y_pos, end_x, end_y, arrow_size)

            # Update position for next vector
            x_pos = end_x
            y_pos = end_y

        # Draw the drawing tip as a small white circle
        glPointSize(5.0)
        glColor3f(*self.drawing_tip_color)
        glBegin(GL_POINTS)
        glVertex2f(x_pos, y_pos)
        glEnd()
        glPopMatrix()

    def scale_vector(self, x, y):
        # Use the same scale factor as in scale_and_translate
        x_scaled = x * self.scale_factor
        y_scaled = y * self.scale_factor
        return x_scaled, y_scaled

    def draw_arrowhead(self, x_start, y_start, x_end, y_end, size):
        dx = x_end - x_start
        dy = y_end - y_start
        angle = np.arctan2(dy, dx)

        left_angle = angle + np.pi / 6  # 30 degrees
        right_angle = angle - np.pi / 6

        left_x = x_end - size * np.cos(left_angle)
        left_y = y_end - size * np.sin(left_angle)
        right_x = x_end - size * np.cos(right_angle)
        right_y = y_end - size * np.sin(right_angle)

        glBegin(GL_TRIANGLES)
        glVertex2f(x_end, y_end)
        glVertex2f(left_x, left_y)
        glVertex2f(right_x, right_y)
        glEnd()

    def update_animation(self):
        if self.is_animating:
            self.current_time = (time.time() - self.start_time) * self.speed
            self.update()

    def set_term_data(self, term_data, fourier_series_function):
        self.term_data = term_data
        self.fourier_series_function = fourier_series_function
        self.compute_scaling()
        self.update()

    def set_speed(self, speed):
        self.speed = speed

    def start_animation(self):
        self.is_animating = True
        self.start_time = time.time() - self.current_time / self.speed

    def stop_animation(self):
        self.is_animating = False
