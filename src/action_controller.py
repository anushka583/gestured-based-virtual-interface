import pyautogui
import time
import os

class CursorController:
    def __init__(self, smoothing=5):
        self.screen_width, self.screen_height = pyautogui.size()
        self.prev_x = 0
        self.prev_y = 0
        self.smoothing = smoothing

    def move_cursor(self, index_finger):
        screen_x = int(index_finger.x * self.screen_width)
        screen_y = int(index_finger.y * self.screen_height)

        curr_x = self.prev_x + (screen_x - self.prev_x) / self.smoothing
        curr_y = self.prev_y + (screen_y - self.prev_y) / self.smoothing

        pyautogui.moveTo(curr_x, curr_y)

        self.prev_x = curr_x
        self.prev_y = curr_y

    def move_to(self, x, y):
        pyautogui.moveTo(x, y)


    def click(self):
        pyautogui.click()

def take_screenshot():
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")
    timestamp=int(time.time())
    filename=f"screenshots/screenshot_{timestamp}.png"
    screenshot=pyautogui.screenshot()
    screenshot.save(filename)

    print("Screenshot saved:", filename)

def next_app():
    pyautogui.hotkey('alt', 'tab')

def previous_app():
    pyautogui.hotkey('alt', 'shift', 'tab')

def close_app():
    pyautogui.hotkey('alt', 'f4')

def volume_up():
    pyautogui.press('volumeup')

def volume_down():
    pyautogui.press('volumedown')