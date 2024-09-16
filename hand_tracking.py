import cv2
import mediapipe as mp
import os
import numpy as np
import threading
from time import sleep
from pynput.keyboard import Controller, Key

# Constantes de cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (0, 0, 255)
BLUE = (255, 0, 0)
GREEN = (0, 255, 0)
LIGHT_BLUE = (255, 255, 0)

# Inicializa o módulo de mãos do MediaPipe
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands()

# Inicializa a câmera
camera = cv2.VideoCapture(0)

# Variáveis para controle de resolução
resolution_x = 1280
resolution_y = 720

# Variáveis para controle de programas
text_editor = False
chrome = False
calculator = False

# Variáveis do teclado virtual
keyboard_keys = [['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A','S','D','F','G','H','J','K','L'],
            ['Z','X','C','V','B','N','M', ',','.',' ']]
offset = 50
counter = 0
text = '>'
keyboard = Controller()

# Variáveis do quadro branco
whiteboard = np.ones((resolution_y, resolution_x, 3), np.uint8) * 255
brush_color = (255, 0, 0)
brush_thickness = 7
x_board, y_board = 0, 0

# Configura a resolução da câmera
camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolution_x)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution_y)

# Função para encontrar as coordenadas das mãos
def find_hands_coordinates(img, inverted_side = False):
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

# Função para verificar quais dedos estão levantados
def fingers_raised(hand):
    fingers = []
    coordinates = hand['coordinates']
    
    # Verifica se o dedo polegar está levantado
    if hand['side'] == 'Left': 
        if coordinates[4][0] > coordinates[3][0]:
            fingers.append(True)
        else:
            fingers.append(False)
    else:
        if coordinates[4][0] < coordinates[3][0]:
            fingers.append(True)
        else:
            fingers.append(False)
    
    # Verifica se os outros dedos estão levantados
    for fingertip in [8, 12, 16, 20]:
        if coordinates[fingertip][1] < coordinates[fingertip - 2][1]:
            fingers.append(True)
        else:
            fingers.append(False)
            
    return fingers

# Função para abrir programas
def open_program(command):
    os.system(command)

# Função para desenhar as teclas do teclado virtual
def print_keys(img, position, word, size = 50, rectangle_color = WHITE):
    cv2.rectangle(img, position, (position[0] + size, position[1] + size), rectangle_color,cv2.FILLED)
    cv2.rectangle(img, position, (position[0] + size, position[1] + size), BLUE, 1)
    cv2.putText(img, word, (position[0] + 15, position[1] + 30), cv2.FONT_HERSHEY_COMPLEX, 1, BLACK, 2)
    return img

while True: 
    success, img = camera.read()
    img = cv2.flip(img, 1)

    img, all_hands = find_hands_coordinates(img)

    if len(all_hands) == 1:
        fingers = fingers_raised(all_hands[0])
        # Comandos para escrever
        if all_hands[0]['side'] == 'Left':
            indicator_x, indicator_y, indicator_z = all_hands[0]['coordinates'][8]
            cv2.putText(img, f'Camera distance: {indicator_z}', (850, 50), cv2.FONT_HERSHEY_COMPLEX, 1, BLACK, 2)
            for row_index, keyboard_row in enumerate(keyboard_keys):
                for index, word in enumerate(keyboard_row):
                    if sum(fingers) <= 1:
                        word = word.lower()
                    img = print_keys(img, (offset + index * 80, offset + row_index * 80), word)
                    if offset + index * 80 < indicator_x < 100 + index * 80 and offset + row_index * 80 < indicator_y < 100 + row_index * 80:
                        img = print_keys(img, (offset + index * 80, offset + row_index * 80), word, rectangle_color = GREEN)
                        if indicator_z < -85:
                            counter = 1
                            write = word
                            img = print_keys(img, (offset + index * 80, offset + row_index * 80), word, rectangle_color = LIGHT_BLUE)
            if counter:
                counter += 1
                if counter == 3:
                    text += write
                    counter = 0

                    # Permite escrever em outros aplicativos do computador
                    keyboard.press(write)

            # Comando para apagar o texto
            if fingers == [False, False, False, False, True] and len(text) > 1:
                text = text[:-1]
                keyboard.press(Key.backspace)
                sleep(0.15)

            # Desenha o texto na tela
            cv2.rectangle(img, (offset, 450), (830, 500), WHITE, cv2.FILLED)
            cv2.rectangle(img, (offset, 450), (830, 500), BLUE, 1)
            cv2.putText(img, text[-40:], (offset, 480), cv2.FONT_HERSHEY_COMPLEX, 1, BLACK, 2)
            cv2.circle(img, (indicator_x, indicator_y), 7, BLUE, cv2.FILLED)

        # Comandos para abrir e fechar programas
        if all_hands[0]['side'] == 'Right':
            if fingers == [False, True, False, False, False] and text_editor == False:
                text_editor = True
                threading.Thread(target = open_program, args = ('flatpak run org.gnome.TextEditor',)).start()
            if fingers == [False, True, True, False, False] and chrome == False:
                chrome = True
                threading.Thread(target = open_program, args = ('google-chrome-stable',)).start()
            if fingers == [False, True, True, True, False] and calculator == False:
                calculator = True
                threading.Thread(target = open_program, args = ('flatpak run org.gnome.Calculator',)).start()
            if fingers == [False, False, False, False, False] and text_editor == True:
                text_editor = False
                threading.Thread(target = open_program, args = ('flatpak kill org.gnome.TextEditor',)).start()
            if fingers == [False, False, False, False, False] and chrome == True:
                chrome = False
                threading.Thread(target = open_program, args = ('pkill chrome',)).start()
            if fingers == [False, False, False, False, False] and calculator == True:
                calculator = False
                threading.Thread(target = open_program, args = ('flatpak kill org.gnome.Calculator',)).start()
            if fingers == [False, True, False, False, True]:
                break
            print(fingers)

    if len(all_hands) == 2:
        fingers_left_hand = fingers_raised(all_hands[0])
        fingers_right_hand = fingers_raised(all_hands[1])

        # Utiliza o dedo indicador como pincel
        indicator_x, indicator_y, indicator_z = all_hands[0]['coordinates'][8]

        if sum(fingers_right_hand) == 1:
            brush_color = BLUE
        elif sum(fingers_right_hand) == 2:
            brush_color = GREEN
        elif sum(fingers_right_hand) == 3:
            brush_color = RED
        elif sum(fingers_right_hand) == 4:
            brush_color = BLACK
        elif sum(fingers_right_hand) == 5:
            brush_color = WHITE
        else:
            whiteboard = np.ones((resolution_y, resolution_x, 3), np.uint8) * 255

        brush_thickness = int(abs(indicator_z)) // 3 + 5
        cv2.circle(img, (indicator_x, indicator_y), brush_thickness, brush_color, cv2.FILLED)

        if fingers_left_hand == [False, True, False, False, False]:
            if x_board == 0 and y_board == 0:
                x_board, y_board = indicator_x, indicator_y

            cv2.line(whiteboard, (x_board, y_board), (indicator_x, indicator_y), brush_color, brush_thickness)
            x_board, y_board = indicator_x, indicator_y
        else:
            x_board, y_board = 0, 0

        img = cv2.addWeighted(img, 1, whiteboard, 0.2, 0)

    # Desenha a imagem na tela
    cv2.imshow('Image', img)

    # Desenha o quadro branco na tela
    cv2.imshow('Whiteboard', whiteboard)

    key = cv2.waitKey(1)
    if key == 27:
        break

# Cria um arquivo de texto com o conteúdo escrito
with open('text.txt', 'w') as archive:
    archive.write(text)

# Salva a imagem do quadro branco
cv2.imwrite('whiteboard.png', whiteboard)

camera.release()
cv2.destroyAllWindows()