import cv2
import mediapipe as mp
import os
import threading

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands()

camera = cv2.VideoCapture(0)

resolution_x = 1280
resolution_y = 720

text_editor = False
chrome = False
calculator = False

camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolution_x)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution_y)

def find_hands_coordinates(img, inverted_side=False):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    result = hands.process(img_rgb)
    all_hands = []

    if result.multi_hand_landmarks:
        for hand_side, hand_markings in zip(result.multi_handedness, result.multi_hand_landmarks):
            info_hand = {}
            coordinates = []
            for marking in hand_markings.landmark:
                coord_x, coord_y, coord_z = int(marking.x * resolution_x), int(marking.y * resolution_y), int(marking.z * resolution_x)
                coordinates.append((coord_x, coord_y, coord_z))

            info_hand['coordinates'] = coordinates

            if inverted_side:
                if hand_side.classification[0].label == 'Left':
                    info_hand['side'] = 'Right'
                else:
                    info_hand['side'] = 'Left'
            else:
                info_hand['side'] = hand_side.classification[0].label

            all_hands.append(info_hand)

            mp_draw.draw_landmarks(img, hand_markings, mp_hands.HAND_CONNECTIONS)

    return img, all_hands

def fingers_raised(hand):
    fingers = []

    if hand[4][0] > hand[3][0] if hand[4][0] > hand[2][0] else hand[4][0] < hand[3][0]:
        fingers.append(True)
    else:
        fingers.append(False)

    for fingertip in [8, 12, 16, 20]:
        if hand[fingertip][1] < hand[fingertip - 2][1]:
            fingers.append(True)
        else:
            fingers.append(False)
    return fingers

def open_program(command):
    os.system(command)

while True: 
    success, img = camera.read()
    img = cv2.flip(img, 1)

    img, all_hands = find_hands_coordinates(img)

    if len(all_hands) > 0:
        for hand in all_hands:
            fingers = fingers_raised(hand['coordinates'])
            if fingers == [False, True, False, False, False] and text_editor == False:
                text_editor = True
                threading.Thread(target=open_program, args=('flatpak run org.gnome.TextEditor',)).start()
            if fingers == [False, True, True, False, False] and chrome == False:
                chrome = True
                threading.Thread(target=open_program, args=('google-chrome-stable',)).start()
            if fingers == [False, True, True, True, False] and calculator == False:
                calculator = True
                threading.Thread(target=open_program, args=('flatpak run org.gnome.Calculator',)).start()
            if fingers == [False, False, False, False, False] and text_editor == True:
                text_editor = False
                threading.Thread(target=open_program, args=('flatpak kill org.gnome.TextEditor',)).start()
            if fingers == [False, False, False, False, False] and chrome == True:
                chrome = False
                threading.Thread(target=open_program, args=('pkill chrome',)).start()
            if fingers == [False, False, False, False, False] and calculator == True:
                calculator = False
                threading.Thread(target=open_program, args=('flatpak kill org.gnome.Calculator',)).start()
            if fingers == [False, True, False, False, True]:
                break
            print(fingers)
    
    cv2.imshow('Image', img)

    key = cv2.waitKey(1)

    if key == 27:
        break

camera.release()
cv2.destroyAllWindows()
