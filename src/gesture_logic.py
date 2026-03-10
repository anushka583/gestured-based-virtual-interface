import math

class PinchDetector:
    def __init__(self, threshold=0.018):
        self.threshold = threshold
        self.was_pinched = False

    def detect(self, hand_landmarks):
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]

        distance = math.sqrt(
            (thumb_tip.x - index_tip.x) ** 2 +
            (thumb_tip.y - index_tip.y) ** 2
        )

        is_pinched = distance < self.threshold

        # Trigger only on edge transition
        if is_pinched and not self.was_pinched:
            self.was_pinched = True
            return True

        if not is_pinched:
            self.was_pinched = False

        return False

def detect_screenshot_gesture(hand_landmarks, threshold=0.05):
    thumb_tip=hand_landmarks.landmark[4]
    pinky_tip=hand_landmarks.landmark[20]
    distance=math.sqrt(
        (thumb_tip.x-pinky_tip.x)**2+(thumb_tip.y-pinky_tip.y)**2
    )
    if distance < threshold:
        return True
    return False