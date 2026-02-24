import cv2
import mediapipe as mp
import pyautogui
import numpy as np

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

screen_width, screen_height = pyautogui.size()
prev_x, prev_y = 0, 0
smoothing_factor = 5
click_threshold = 0.03
click_cooldown = 0

cap = cv2.VideoCapture(0)


while True:
    success, frame = cap.read()
    # Crop upper portion 
    frame = frame[150:650, 200:800]
    if not success:
        print("Frame not captured")
        break
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            index_finger = hand_landmarks.landmark[8]
            
            cam_h, cam_w, _ = frame.shape
            x = int(index_finger.x * cam_w)
            y = int(index_finger.y * cam_h)

            screen_x = int(index_finger.x * screen_width)
            screen_y = int(index_finger.y * screen_height)
            curr_x = prev_x + (screen_x - prev_x) / smoothing_factor
            curr_y = prev_y + (screen_y - prev_y) / smoothing_factor

            pyautogui.moveTo(curr_x, curr_y)

            prev_x, prev_y = curr_x, curr_y

            # Get thumb and index finger tip
            thumb_tip = hand_landmarks.landmark[4]
            index_tip = hand_landmarks.landmark[8]

 
            distance = ((thumb_tip.x - index_tip.x) ** 2 + (thumb_tip.y - index_tip.y) ** 2) ** 0.5


            if distance < click_threshold and click_cooldown == 0:
                pyautogui.click()
                click_cooldown = 10


            if click_cooldown > 0:
                click_cooldown -= 1

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    cv2.imshow("Gesture Cursor", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()