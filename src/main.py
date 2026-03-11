import sys
import cv2
import time
import numpy as np

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap

from hand_tracking import HandTracker
from gesture_logic import PinchDetector, detect_screenshot_gesture
from action_controller import (
    CursorController,
    take_screenshot,
    next_app,
    previous_app,
    volume_up,
    volume_down,
    close_app
)


class GestureApp(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AirUI")
        self.setGeometry(100, 100, 960, 720)

        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 960, 720)

        # Core modules
        self.tracker = HandTracker()
        self.cursor = CursorController()
        self.pinch = PinchDetector(threshold=0.02)

        # Drawing system
        self.canvas = None
        self.prev_draw_point = None
        self.draw_color = (255, 0, 255)

        self.brush_thickness = 6
        self.eraser_thickness = 40

        # Cursor smoothing
        self.prev_cursor_x = 0
        self.prev_cursor_y = 0
        self.smoothing_alpha = 0.25

        # Swipe detection
        self.swipe_points = []
        self.swipe_cooldown = 0

        # Cooldowns
        self.click_cooldown = 0
        self.screenshot_cooldown = 0

        # Control box
        self.control_margin = 100

        # FPS tracking
        self.prev_time = time.time()
        self.fps = 0

        # Mode
        self.mode = "CONTROL"

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):

        frame, result = self.tracker.get_frame()

        if frame is None:
            return

        h, w, _ = frame.shape

        if self.canvas is None:
            self.canvas = np.zeros_like(frame)

        # Cooldowns
        if self.click_cooldown > 0:
            self.click_cooldown -= 1

        if self.screenshot_cooldown > 0:
            self.screenshot_cooldown -= 1

        if self.swipe_cooldown > 0:
            self.swipe_cooldown -= 1

        # --------------------------------------------------
        # Hand detection
        # --------------------------------------------------

        if result and result.multi_hand_landmarks:

            for hand_landmarks in result.multi_hand_landmarks:

                index_tip = hand_landmarks.landmark[8]
                middle_tip = hand_landmarks.landmark[12]
                ring_tip = hand_landmarks.landmark[16]
                pinky_tip = hand_landmarks.landmark[20]
                thumb_tip = hand_landmarks.landmark[4]

                # ---------------------------------------
                # Boundary mapping
                # ---------------------------------------

                cam_x = int(index_tip.x * w)
                cam_y = int(index_tip.y * h)

                margin = self.control_margin

                cam_x = np.clip(cam_x, margin, w - margin)
                cam_y = np.clip(cam_y, margin, h - margin)

                norm_x = (cam_x - margin) / (w - 2 * margin)
                norm_y = (cam_y - margin) / (h - 2 * margin)

                screen_x = int(norm_x * self.cursor.screen_width)
                screen_y = int(norm_y * self.cursor.screen_height)

                screen_x = np.clip(screen_x, 10, self.cursor.screen_width - 10)
                screen_y = np.clip(screen_y, 10, self.cursor.screen_height - 10)

                # ---------------------------------------
                # Cursor smoothing
                # ---------------------------------------

                smooth_x = int(
                    self.smoothing_alpha * screen_x +
                    (1 - self.smoothing_alpha) * self.prev_cursor_x
                )

                smooth_y = int(
                    self.smoothing_alpha * screen_y +
                    (1 - self.smoothing_alpha) * self.prev_cursor_y
                )

                self.prev_cursor_x = smooth_x
                self.prev_cursor_y = smooth_y

                self.cursor.move_to(smooth_x, smooth_y)

                # ---------------------------------------
                # Finger states
                # ---------------------------------------

                index_up = index_tip.y < hand_landmarks.landmark[6].y
                middle_up = middle_tip.y < hand_landmarks.landmark[10].y
                ring_up = ring_tip.y < hand_landmarks.landmark[14].y
                pinky_up = pinky_tip.y < hand_landmarks.landmark[18].y

                fist = (not index_up and not middle_up and not ring_up and not pinky_up and abs(thumb_tip.x-index_tip.x) < 0.05)

                # ---------------------------------------
                # Mode switching
                # ---------------------------------------

                if index_up and middle_up:
                    self.mode = "DRAW"

                elif index_up and not middle_up:
                    self.mode = "CONTROL"

                # ---------------------------------------
                # Screenshot gesture
                # ---------------------------------------

                if detect_screenshot_gesture(hand_landmarks) and self.screenshot_cooldown == 0:
                    take_screenshot()
                    self.screenshot_cooldown = 30

                # ---------------------------------------
                # Close app gesture
                # ---------------------------------------

                if fist and self.swipe_cooldown == 0 and self.mode == "CONTROL":
                    close_app()
                    self.swipe_cooldown = 40

                # ---------------------------------------
                # Swipe detection
                # ---------------------------------------

                self.swipe_points.append((cam_x, cam_y))

                if len(self.swipe_points) > 10:
                    self.swipe_points.pop(0)

                if len(self.swipe_points) == 10 and self.swipe_cooldown == 0 and self.mode == "CONTROL":

                    start_x, start_y = self.swipe_points[0]
                    end_x, end_y = self.swipe_points[-1]

                    movement_x = end_x - start_x
                    movement_y = end_y - start_y

                    if abs(movement_x) > abs(movement_y):

                        if movement_x > 150:
                            next_app()
                            self.swipe_cooldown = 20
                            self.swipe_points = []

                        elif movement_x < -150:
                            previous_app()
                            self.swipe_cooldown = 20
                            self.swipe_points = []

                    else:

                        if movement_y < -150:
                            volume_up()
                            self.swipe_cooldown = 20
                            self.swipe_points = []

                        elif movement_y > 150:
                            volume_down()
                            self.swipe_cooldown = 20
                            self.swipe_points = []

                # ---------------------------------------
                # Draw mode
                # ---------------------------------------

                if index_up and middle_up and not ring_up and not pinky_up:
                    self.mode = "DRAW"

                    x = int(index_tip.x * w)
                    y = int(index_tip.y * h)

                    if y < 60:

                        block_width = w // 4

                        if x < block_width:
                            self.draw_color = (255, 0, 0)

                        elif x < 2 * block_width:
                            self.draw_color = (0, 255, 0)

                        elif x < 3 * block_width:
                            self.draw_color = (0, 0, 255)

                        else:
                            self.draw_color = (0, 0, 0)

                    else:

                        if self.prev_draw_point is None:
                            self.prev_draw_point = (x, y)

                        if self.draw_color == (0, 0, 0):

                            cv2.circle(
                                self.canvas,
                                (x, y),
                                self.eraser_thickness,
                                (0, 0, 0),
                                -1
                            )

                        else:

                            cv2.line(
                                self.canvas,
                                self.prev_draw_point,
                                (x, y),
                                self.draw_color,
                                self.brush_thickness
                            )

                        self.prev_draw_point = (x, y)

                else:
                    self.prev_draw_point = None

                # ---------------------------------------
                # Click gesture
                # ---------------------------------------

                if self.mode == "CONTROL":

                    if self.pinch.detect(hand_landmarks) and self.click_cooldown == 0:
                        self.cursor.click()
                        self.click_cooldown = 15

                self.tracker.draw_landmarks(frame, hand_landmarks)

        # --------------------------------------------------
        # Overlay canvas
        # --------------------------------------------------

        frame = cv2.add(frame, self.canvas)

        # --------------------------------------------------
        # Control box
        # --------------------------------------------------

        margin = self.control_margin

        cv2.rectangle(
            frame,
            (margin, margin),
            (w - margin, h - margin),
            (255, 255, 0),
            2
        )

        # --------------------------------------------------
        # Color palette
        # --------------------------------------------------

        block_width = w // 4

        cv2.rectangle(frame, (0, 0), (block_width, 60), (255, 0, 0), -1)
        cv2.rectangle(frame, (block_width, 0), (2 * block_width, 60), (0, 255, 0), -1)
        cv2.rectangle(frame, (2 * block_width, 0), (3 * block_width, 60), (0, 0, 255), -1)
        cv2.rectangle(frame, (3 * block_width, 0), (w, 60), (0, 0, 0), -1)

        # --------------------------------------------------
        # FPS display
        # --------------------------------------------------

        curr_time = time.time()
        diff = curr_time - self.prev_time

        if diff > 0:
            self.fps = 1 / diff

        self.prev_time = curr_time

        cv2.putText(
            frame,
            f"FPS: {int(self.fps)}",
            (10, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"MODE: {self.mode}",
            (10, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        # --------------------------------------------------
        # Convert frame for PyQt
        # --------------------------------------------------

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape

        qt_img = QImage(rgb.data, w, h, QImage.Format_RGB888)

        self.label.setPixmap(QPixmap.fromImage(qt_img))

    def closeEvent(self, event):

        self.tracker.release()
        event.accept()


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = GestureApp()
    window.show()

    sys.exit(app.exec_())