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
        # Default settings
        self.background_color = (0.0, 0.0, 0.0, 1.0)  # Black background
        self.show_fourier_preview = True
        self.fourier_preview_color = (0.1, 0.9, 0.9, 0.25)
        self.fourier_preview_opacity = 0.25
        self.show_drawing_tip_trail = True
        self.drawing_tip_trail_color = (0.1, 0.9, 0.9)
        self.drawing_tip_trail_width = 2.0
        self.num_anti_aliasing_passes = 1
        # Arrow settings
        self.arrow_color = (1.0, 1.0, 1.0, 1.0)
        self.arrow_head_max_size = 10.0
        self.arrow_line_max_width = 5.0

        self.arrow_head_base_size = 2.0
        self.arrow_head_scaling_factor = 1.0
        self.arrow_line_base_width = 1.0
        self.arrow_line_scaling_factor = 1.0
        self.arrow_cap_type_index = 0  # 0: Normal Arrow Head, 1: No Arrow Cap, 2: Dot

        self.user_speed = 0.1  # Default user speed
        self.adjusted_speed = self.user_speed  # Adjusted speed based on path length
        self.total_length = 1.0  # Default total length to avoid division by zero
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.start_time = time.time()
        self.current_time = 0
        self.scale_factor = 1.0
        self.drawing_center = (0, 0)
        self.is_animating = False
        self.follow_mode = False
        self.zoom_level = 1.0
        self.last_frame_time = None
        self.trail_points = []  # List to store trail points
        self.max_trail_length = 100  # Maximum number of points in the trail

    def initializeGL(self):
        glClearColor(*self.background_color)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_POINT_SMOOTH)
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
        glClearColor(*self.background_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if self.term_data is None:
            return

        # Update trail with current tip position
        if self.show_drawing_tip_trail:
            self.update_trail()

        # Draw the Fourier drawing first
        if self.show_fourier_preview:
            self.draw_fourier_drawing()

        # Draw the trail before drawing the tip
        if self.show_drawing_tip_trail:
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

        glLineWidth(self.drawing_tip_trail_width)
        glBegin(GL_LINE_STRIP)
        num_points = len(self.trail_points)
        for i, (x, y) in enumerate(self.trail_points):
            # Calculate opacity from 0.9 (90%) to 0.0
            alpha = 0.9 * (1.0 - (i / (num_points - 1))) if num_points > 1 else 0.9
            glColor4f(*self.drawing_tip_trail_color, alpha)
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
        t_values = np.linspace(0, 1, 1500)
        fourier_values = np.vectorize(lambda t: self.fourier_series_function(t))(
            t_values
        )
        self.path_x = fourier_values.real
        self.path_y = fourier_values.imag

        # Calculate cumulative path length
        dx = np.diff(self.path_x)
        dy = np.diff(self.path_y)
        segment_lengths = np.hypot(dx, dy)
        self.cumulative_lengths = np.concatenate(([0], np.cumsum(segment_lengths)))
        self.total_length = self.cumulative_lengths[-1]

        self.scaled_x, self.scaled_y = self.scale_and_translate(
            self.path_x, self.path_y
        )

        # Adjust speed based on path length
        self.adjust_speed_based_on_length()

    def adjust_speed_based_on_length(self):
        if self.total_length > 0.001:  # Avoid division by zero or tiny lengths
            self.adjusted_speed = self.user_speed / self.total_length
        else:
            self.adjusted_speed = self.user_speed  # Use user speed directly

    def draw_fourier_drawing(self):
        glPushMatrix()
        if self.follow_mode:
            tip_x, tip_y = self.get_current_tip_position()
            translate_x = self.width() / 2 - tip_x * self.zoom_level
            translate_y = self.height() / 2 - tip_y * self.zoom_level
            glTranslatef(translate_x, translate_y, 0.0)
            glScalef(self.zoom_level, self.zoom_level, 1.0)

        # Enable blending for opacity
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glColor4f(*self.fourier_preview_color)

        glLineWidth(1.0)
        glBegin(GL_LINE_STRIP)
        for x, y in zip(self.scaled_x, self.scaled_y):
            glVertex2f(x, y)
        glEnd()

        glDisable(GL_BLEND)

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

        # Enable blending
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        if self.follow_mode:
            # Apply the same translation and scaling as in draw_fourier_drawing
            tip_x, tip_y = self.get_current_tip_position()
            translate_x = self.width() / 2 - tip_x * self.zoom_level
            translate_y = self.height() / 2 - tip_y * self.zoom_level
            glTranslatef(translate_x, translate_y, 0.0)
            glScalef(self.zoom_level, self.zoom_level, 1.0)

        # Use the center of the Fourier drawing as the starting position
        x_pos, y_pos = self.drawing_center

        # Sort terms by increasing absolute value of k (frequency)
        terms = [term for term in self.term_data if term["k"] != 0]
        terms.sort(key=lambda term: abs(term["k"]))

        # Define number of passes for blending (more passes = smoother lines)
        num_passes = self.num_anti_aliasing_passes
        alpha_decrement = 1.0 / num_passes
        width_increment = 2.0 / num_passes

        for i, term in enumerate(terms):
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

            zoom_level = self.zoom_level if self.follow_mode else 1.0

            # Calculate magnitude for scaling
            magnitude = np.hypot(scaled_vector_x, scaled_vector_y)
            line_width = (
                self.arrow_line_base_width / zoom_level
                + self.arrow_line_scaling_factor * magnitude / 100
            )
            arrow_head_size = (
                self.arrow_head_base_size / zoom_level
                + self.arrow_head_scaling_factor * magnitude / 100
            )

            # Ensure line width and arrow size are within reasonable bounds
            line_width = min(self.arrow_line_max_width, line_width)
            arrow_head_size = min(self.arrow_head_max_size, arrow_head_size)

            # Adjust the line width and arrow size based on zoom level
            line_width *= zoom_level

            # Draw the vector line
            for pass_num in range(num_passes):
                # Adjust alpha and color for each pass
                alpha_value = 1.0 - pass_num * alpha_decrement
                glColor4f(
                    self.arrow_color[0],
                    self.arrow_color[1],
                    self.arrow_color[2],
                    alpha_value,
                )

                # Draw the vector with the calculated offset
                glLineWidth(line_width + pass_num * width_increment)
                glBegin(GL_LINES)
                glVertex2f(x_pos, y_pos)
                glVertex2f(end_x, end_y)
                glEnd()

            # Draw arrow cap based on type
            if self.arrow_cap_type_index == 0:
                # Normal Arrow Head
                self.draw_arrowhead(
                    x_pos,
                    y_pos,
                    end_x,
                    end_y,
                    arrow_head_size,
                    self.arrow_color,
                )
            elif self.arrow_cap_type_index == 1:
                # No Arrow Cap
                pass  # Do nothing
            elif self.arrow_cap_type_index == 2:
                # Dot
                self.draw_dot(
                    end_x,
                    end_y,
                    arrow_head_size * zoom_level,
                    self.arrow_color,
                )

            # Update position for next vector
            x_pos = end_x
            y_pos = end_y

        # Disable blending and restore the matrix
        glDisable(GL_BLEND)
        glPopMatrix()

    def scale_vector(self, x, y):
        # Use the same scale factor as in scale_and_translate
        x_scaled = x * self.scale_factor
        y_scaled = y * self.scale_factor
        return x_scaled, y_scaled

    def draw_arrowhead(
        self,
        x_start,
        y_start,
        x_end,
        y_end,
        size,
        color: tuple[float, float, float],
    ):
        dx = x_end - x_start
        dy = y_end - y_start
        angle = np.arctan2(dy, dx)

        left_angle = angle + np.pi / 6  # 30 degrees
        right_angle = angle - np.pi / 6

        left_x = x_end - size * np.cos(left_angle)
        left_y = y_end - size * np.sin(left_angle)
        right_x = x_end - size * np.cos(right_angle)
        right_y = y_end - size * np.sin(right_angle)

        # Shift the arrow head slightly to make a cleaner connection
        shift_factor = 0.10  # Shift by 10% of the arrow head
        shift_x = size * np.cos(angle) * shift_factor
        shift_y = size * np.sin(angle) * shift_factor

        glBegin(GL_TRIANGLES)
        glColor4f(*color)
        glVertex2f(x_end + shift_x, y_end + shift_y)
        glVertex2f(left_x + shift_x, left_y + shift_y)
        glVertex2f(right_x + shift_x, right_y + shift_y)
        glEnd()

    def draw_dot(self, x, y, size, color: tuple[float, float, float]):
        glPointSize(size)
        glBegin(GL_POINTS)
        glColor4f(*color)
        glVertex2f(x, y)
        glEnd()

    def update_animation(self):
        if self.is_animating:
            elapsed_time = time.time() - self.start_time

            # Ensure current_time stays within [0,1]
            self.current_time = (elapsed_time * self.adjusted_speed) % 1.0
            self.update()

    def set_term_data(self, term_data, fourier_series_function):
        self.term_data = term_data
        self.fourier_series_function = fourier_series_function
        self.compute_scaling()
        self.start_time = time.time()  # Reset animation time
        self.update()

    def set_speed(self, speed):
        self.user_speed = speed  # Store user-provided speed
        self.adjust_speed_based_on_length()

    def start_animation(self):
        self.is_animating = True
        self.start_time = time.time() - self.current_time / self.adjusted_speed

    def stop_animation(self):
        self.is_animating = False
