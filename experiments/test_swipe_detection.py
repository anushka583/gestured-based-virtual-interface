import cv2
import mediapipe as mp
from collections import deque
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)
history_length = 10
positions = deque(maxlen=history_length)

swipe_threshold = 120
cooldown = 20
cooldown_counter = 0


def detect_swipe():

    if len(positions) < history_length:
        return None

    start_x, start_y = positions[0]
    end_x, end_y = positions[-1]

    dx = end_x - start_x
    dy = end_y - start_y

    if abs(dx) > abs(dy):

        if dx > swipe_threshold:
            return "SWIPE RIGHT"

        if dx < -swipe_threshold:
            return "SWIPE LEFT"

    else:

        if dy > swipe_threshold:
            return "SWIPE DOWN"

        if dy < -swipe_threshold:
            return "SWIPE UP"

    return None


# ----------------------------
# Main Loop
# ----------------------------
while True:

    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb)

    if results.multi_hand_landmarks:

        for hand_landmarks in results.multi_hand_landmarks:

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            h, w, _ = frame.shape

            index_tip = hand_landmarks.landmark[8]

            x = int(index_tip.x * w)
            y = int(index_tip.y * h)

            positions.append((x, y))

            cv2.circle(frame, (x, y), 8, (255, 0, 255), -1)

            if cooldown_counter == 0:

                swipe = detect_swipe()

                if swipe:

                    cv2.putText(
                        frame,
                        swipe,
                        (50, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        3
                    )

                    cooldown_counter = cooldown

    if cooldown_counter > 0:
        cooldown_counter -= 1

    cv2.putText(
        frame,
        "Swipe Gesture Experiment",
        (20, frame.shape[0]-20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255,255,255),
        2
    )

    cv2.imshow("Swipe Detection", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break


cap.release()
cv2.destroyAllWindows()