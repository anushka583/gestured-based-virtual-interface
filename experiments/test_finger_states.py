import cv2
import mediapipe as mp

# ----------------------------
# MediaPipe Setup
# ----------------------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

# Finger tip landmark indices
FINGER_TIPS = [8, 12, 16, 20]


# ----------------------------
# Finger State Logic
# ----------------------------
def get_finger_states(hand_landmarks, hand_label):

    states = {}

    # Thumb detection (depends on hand orientation)
    thumb_tip = hand_landmarks.landmark[4]
    thumb_ip = hand_landmarks.landmark[3]

    if hand_label == "Right":
        states["Thumb"] = thumb_tip.x < thumb_ip.x
    else:
        states["Thumb"] = thumb_tip.x > thumb_ip.x

    # Other fingers
    fingers = ["Index", "Middle", "Ring", "Pinky"]

    for i, name in enumerate(fingers):

        tip = hand_landmarks.landmark[FINGER_TIPS[i]]
        pip = hand_landmarks.landmark[FINGER_TIPS[i] - 2]

        states[name] = tip.y < pip.y

    return states


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

        for hand_landmarks, handedness in zip(
            results.multi_hand_landmarks,
            results.multi_handedness
        ):

            label = handedness.classification[0].label

            # Draw landmarks
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            # Detect finger states
            finger_states = get_finger_states(hand_landmarks, label)

            # Display states
            y = 40

            for finger, state in finger_states.items():

                text = f"{finger}: {'UP' if state else 'DOWN'}"

                cv2.putText(
                    frame,
                    text,
                    (20, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0) if state else (0, 0, 255),
                    2
                )

                y += 40

            # Display hand label
            cv2.putText(
                frame,
                f"Hand: {label}",
                (20, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2
            )

    # Title
    cv2.putText(
        frame,
        "Finger State Detection Experiment",
        (20, frame.shape[0] - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.imshow("Finger States", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break


# ----------------------------
# Cleanup
# ----------------------------
cap.release()
cv2.destroyAllWindows()