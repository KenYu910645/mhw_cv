import win32con
import win32gui
import win32api
import numpy as np
import pyautogui
import pydirectinput # This one is slower than pyautogui, but only this one can control keyboard
import threading
import pprint
import math 
import random
import time
import matplotlib.pyplot as plt
from PIL import ImageGrab
import cv2
import sys

# Configuration
DEBUG = True
ALLOW_CONT = True #  # True #False # True

GAME_TITLE = 'monster hunter: world(421471)' # windows title must cantain these characters
RESIZE_SCALE = 0.5
KEEP_ALIVE = 1 # sec
GOAL_TOR = 1 # 0.5 # 1
# Color range
NUM_HSV_LO = (30, 0, 0)
NUM_HSV_UP = (45, 255, 255)

def enum_cb(hwnd, results):
    global winlist
    winlist.append((hwnd, win32gui.GetWindowText(hwnd)))
    
def get_screens(screen_name):
    # wait for the program to start initially.
    win32gui.EnumWindows(enum_cb, winlist)

    screens = [(hwnd, title) for hwnd, title in winlist if screen_name in title.lower()]
    while len(screens) == 0:
        screens = [(hwnd, title) for hwnd, title in winlist if screen_name in title.lower()]
        win32gui.EnumWindows(enum_cb, winlist)
    return screens

def list_all_windows_name():
    win32gui.EnumWindows(enum_cb, winlist)
    names = []
    for hwnd, title in winlist:
        names.append(title.lower())
    return names

def sign(num):
    if num >= 0: return 1
    else: return -1

def key_control():
    global is_run, KEY_CMD, is_died
    while is_run:
        # print(is_died)
        if not is_died: 
            pydirectinput.keyDown('f')
        
        if KEY_CMD[0] != ' ':
            pydirectinput.keyDown(KEY_CMD[0])
            if KEY_CMD[0] == 'a':
                pydirectinput.keyUp('d')
            else:
                pydirectinput.keyUp('a')
        else:
            pydirectinput.keyUp("a")
            pydirectinput.keyUp("d")
        
        if KEY_CMD[1] != ' ':
            pydirectinput.keyDown(KEY_CMD[1])
            if KEY_CMD[1] == 'w':
                pydirectinput.keyUp('s')
            else:
                pydirectinput.keyUp('w')
        else:
            pydirectinput.keyUp("w")
            pydirectinput.keyUp("s")
        
        if not is_died: 
            pydirectinput.keyUp('f')

def remove_isolated_pixels(image):
    (num_stats, labels, stats, _) = cv2.connectedComponentsWithStats(image, 8, cv2.CV_32S)
    new_image = image.copy()
    for label in range(num_stats):
        if stats[label,cv2.CC_STAT_AREA] == 1:
            new_image[labels == label] = 0
    return new_image

if __name__ == '__main__':
    try:
    # if True:
        winlist = []
        names = list_all_windows_name()
        # print(names)
        screen = None
        for name in names:
            if GAME_TITLE in name:
                screen = name
                print("Windows name: " + screen)
        screens = get_screens(screen)
        
        # MHW state
        is_run = True
        is_died = False
        KEY_CMD = [' ', ' ']# "  " # 'a', 'w', 'd'
        WIN_TIME = 0
        GOAL_REST_TIME = 1 # sec
        t_rest = None
        
        # Init threads
        if ALLOW_CONT:
            t_key = threading.Thread(target = key_control)
            t_key.start()
        # mutex = threading.Lock()

        # Load number image 
        IMG_11 = cv2.imread("eleven.png" ,cv2.IMREAD_GRAYSCALE)#,cv2.IMREAD_UNCHANGED)# ,cv2.IMREAD_GRAYSCALE)
        IMG_10 = cv2.imread("ten.png" ,cv2.IMREAD_GRAYSCALE)
        IMG_4 = cv2.imread("four.png" ,cv2.IMREAD_GRAYSCALE)
        IMG_3 = cv2.imread("three.png" ,cv2.IMREAD_GRAYSCALE)
        IMG_DICT = {'3' : IMG_3, '4' : IMG_4, '10' : IMG_10, '11' : IMG_11}
        P_LOC = (0,0)
        WORKING_LIST = [(30, 24, 'mine_10', 2),
                (30, 52, 'neck_point', -1), 
                (27, 57, 'mine_neck', 2),
                (26, 65, 'mid_11', -1),
                (16.5, 55, 'upper_vein', -1), 
                (10.5, 64, 'mine_bridge_left', 2),
                (16.5, 55, 'upper_vein', -1),
                (23, 48, 'mine_bridge_right', 2),
                (16.5, 55, 'upper_vein', -1),
                (26, 65, 'mid_11', -1),
                (19, 75, 'trail_11', 2),
                (41, 87, 'bone_11', 2),
                (26, 65, 'mid_11', -1),
                (30, 52, 'neck_point', -1),
                (52, 38, 'super_mine', 1),
                (59, 27, 'trail_10', 2),
                (61, 22, 'bone_10', 2),
                (69, 11, 'mine_cats', 2),
                (71, 8, 'trail_cats', 2),
                (69, -2, 'upper_vein', -1),
                (73, -6, 'lower_vein', -1),
                (70, -10, 'super_bone', 1),
                (73, -6, 'lower_vein', -1),
                (69, -2, 'upper_vein', -1),
                (69, -1, 'mid_cats', -1), 
                (58, 7, 'bone_tree', 2),
                (51, 18, 'mid_10', -1)]

        THE_WAY_BACK = [(-25.5, 68, 'mid_home', -1),
                        (-27, 58, 'upper_vein', -1),
                        (-29, 52, 'lower_vein', -1),
                        (3, 24, 'entry_point', -1),
                        (28, 9, 'mid_4', -1),
                        (51, 18 ,'mid_10', -1)]
        GOAL_IDX = 0
        GOAL = WORKING_LIST
        
        # 
        N_DIC = {
                '3' : {
                    'x1' : (0,0),
                    'x2' : (0,0),
                    'cent' : (0,0),
                    'conf' : 0.0,
                    'global_loc' : (-42.5,83)},
                '4' : {
                    'x1' : (0,0),
                    'x2' : (0,0),
                    'cent' : (0,0),
                    'conf' : 0.0,
                    'global_loc' : (0,0)},
                '10' : {
                    'x1' : (0,0),
                    'x2' : (0,0),
                    'cent' : (0,0),
                    'conf' : 0.0,
                    'global_loc' : (68, 38)},
                '11' : {
                    'x1' : (0,0),
                    'x2' : (0,0),
                    'cent' : (0,0),
                    'conf' : 0.0,
                    'global_loc' : (19, 103)}}

        while is_run:
            t_start = time.time()
            
            # Convert to array
            img_window = np.array(ImageGrab.grab(bbox=win32gui.GetWindowRect(screens[0][0])))
            
            # Resize
            (imgH, imgW, _) = img_window.shape
            img_mhw = cv2.resize(img_window, (int(imgW*RESIZE_SCALE), int(imgH*RESIZE_SCALE)), interpolation=cv2.INTER_AREA)
            (h, w, _) = img_mhw.shape

            # Get mini map
            img_map = img_mhw[370:512, 52:200]
            img_hsv = cv2.cvtColor(img_mhw[370:512, 52:200],cv2.COLOR_RGB2HSV)

            # Mask 
            green_mask = cv2.inRange(img_hsv, NUM_HSV_LO, NUM_HSV_UP)
            remove_isolated_pixels(green_mask)
            # print(kernel)
            # green_mask = cv2.erode(green_mask, kernel, iterations = 1)
            # green_mask = cv2.cvtColor(img_mhw[370:512, 52:200],cv2.COLOR_RGB2GRAY)
            # green_mask = img_hsv[:,:,0]
            
            # img = cv.imread('wiki.jpg',0)
            # equ = cv2.equalizeHist(green_mask)
            # green_mask = np.hstack((green_mask,equ)) #stacking images side-by-side
            # cv.imwrite('res.png',green_mask)

            # 
            CENTER_P = (74, 71)
            CONFIENT_THRES = 0.75
            for ref in N_DIC:
                # Matching
                res = cv2.matchTemplate(green_mask, IMG_DICT[ref], cv2.TM_CCOEFF_NORMED )# cv2.TM_CCOEFF)#  )
                
                # Get geometry
                max_cof = np.amax(res)
                if max_cof > CONFIENT_THRES:
                    loc = np.where(res == np.amax(res))
                    for pt in zip(*loc[::-1]):
                        N_DIC[ref]['x1'] = pt
                        N_DIC[ref]['x2'] = (pt[0] + IMG_DICT[ref].shape[1],
                                            pt[1] + IMG_DICT[ref].shape[0])
                        N_DIC[ref]['cent'] = (pt[0] + IMG_DICT[ref].shape[1]/2,
                                              pt[1] + IMG_DICT[ref].shape[0]/2)
                        N_DIC[ref]['conf'] = max_cof
                    # Draw rectangle and text
                    img_map = cv2.putText(img_map, ref, N_DIC[ref]['x1'],
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1, cv2.LINE_AA)
                    img_map = cv2.putText(img_map, str(N_DIC[ref]['conf']), N_DIC[ref]['x2'],
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1, cv2.LINE_AA)
                    cv2.rectangle(img_map, N_DIC[ref]['x1'], N_DIC[ref]['x2'], (255, 0, 255), 1)

                    # Get player location
                    px = N_DIC[ref]['global_loc'][0] - (N_DIC[ref]['cent'][0] - CENTER_P[0])
                    py = N_DIC[ref]['global_loc'][1] - (N_DIC[ref]['cent'][1] - CENTER_P[1])
                    P_LOC = (px, py)
            # print(N_DIC)
            print("Player Location : " + str(P_LOC))

            # Check player's death or not
            DEATH_LOC = (-23, 73)
            DEATH_TOR = 2
            if (not is_died) and abs(P_LOC[0] - DEATH_LOC[0]) < DEATH_TOR and abs(P_LOC[1] - DEATH_LOC[1]) < DEATH_TOR:
                print("DEATH")
                GOAL = THE_WAY_BACK
                GOAL_IDX = 0
                is_died = True
            print("Death: " + str(is_died))

            # CUR_GOAL
            print("Current Goal : " + str(GOAL[GOAL_IDX]))

            dx = GOAL[GOAL_IDX][0] - P_LOC[0]
            dy = GOAL[GOAL_IDX][1] - P_LOC[1]
            print("(dx, dy) =  " + str((dx, dy)))

            # Reach goal, change to next one 
            if abs(dx) <= GOAL_TOR and abs(dy) <= GOAL_TOR:
                # Relex a while at goal 
                if t_rest != None:
                    if time.time() - t_rest > GOAL[GOAL_IDX][-1]:
                        t_rest = None
                        # go back to mining zone
                        if is_died and GOAL_IDX == len(GOAL)-1:
                            is_died = False
                            GOAL = WORKING_LIST
                            GOAL_IDX = 0
                        else:
                            GOAL_IDX = (GOAL_IDX+1)%len(GOAL)
                else:
                    t_rest = time.time()
            else:
                t_rest = None
                

            # Control keyboard
            # if mutex.acquire(blocking = False):# Critical Section
            if abs(dx) > GOAL_TOR:
                if dx > 0:
                    KEY_CMD[0] = "d"
                else:
                    KEY_CMD[0] = "a"
            else:
                KEY_CMD[0] = " "
            
            if abs(dy) > GOAL_TOR:
                if dy > 0:
                    KEY_CMD[1] = "s"
                else:
                    KEY_CMD[1] = "w"
            else:
                KEY_CMD[1] = " "
            print(KEY_CMD)
            # mutex.release()

            print("loop took {} seconds".format(time.time() - t_start))
            cv2.imshow('green_mask', green_mask)

            # Show image
            cv2.imshow('window',cv2.cvtColor(img_map, cv2.COLOR_BGR2RGB))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                is_run = False
    except (Exception, KeyboardInterrupt) as e:
        is_run = False
        print("Catched Exception!")
        print(e)