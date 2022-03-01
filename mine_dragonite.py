import threading
import time
# Computer vision
from PIL import ImageGrab
import cv2
import numpy as np
# keyboard listerner
from directkeys import PressKey,ReleaseKey
import pynput
# Screen monitor
import win32gui
# Logging
import logging
import sys
# Tkinter GUI
import tkinter as tk
import tkinter.messagebox
# 
from config import THE_WAY_BACK, WORKING_LIST
import copy
# Configuration
DEBUG = True
GAME_TITLE = 'monster hunter: world(421471)' # windows title must cantain these characters
KEEP_ALIVE = 120 # sec, If character can't get to next goal for a long time, throw a homeward ball and go back to camp
GOAL_TOR = 0.5 # If character location is within the GOAL_TOR radius, consider goal reached.
LOGGER_TIME = 1 # sec, logging frequency
MAIN_SLEEP = 10 #msec, main loop frequency
# Color range
NUM_HSV_LO = (30, 0, 0) # Green number on mini-map
NUM_HSV_UP = (45, 255, 255)
CONFIENT_THRES = 0.75 # If detection confident higher than CONFIENT_THRES, consider it as a number.
CENTER_P = (74, 71) # The location of player in mini-map(always centered)
# BONUS_MAX is to prevent jumpy/unstable detection.
BONUS_MAX = 0.2 # Match confident will received a bonus, if it's very near its previous detected location.
BONUS_COF = 0.02 # 0.2/10 <- 10 is the pixel range you wanna allow
# Death 
DEATH_LOC = (-23, 73) # If player near DEATH_LOC, consider player has been killed. 
DEATH_TOR = 2 # The radius of this death location.

WIN_LIST = []
def enum_cb(hwnd, results):
    global WIN_LIST
    WIN_LIST.append((hwnd, win32gui.GetWindowText(hwnd)))
    
def get_screens(screen_name):
    screens = None
    for hwnd, title in WIN_LIST:
        if screen_name in title.lower():
            screens = (hwnd, title)
    return screens

def list_all_windows_name():
    win32gui.EnumWindows(enum_cb, WIN_LIST)
    names = []
    for hwnd, title in WIN_LIST:
        names.append(title.lower())
    return names

def key_control():
    '''
    Control over 'a', 's', 'd', 'w', this thread control character movement
    '''
    global IS_RUN, KEY_CMD, IS_CTRL
    last_cmd = ['', '', '']
    while IS_RUN:
        if IS_CTRL:
            if last_cmd != KEY_CMD:
                # Release all key
                ReleaseKey('a')
                ReleaseKey('s')
                ReleaseKey('d')
                ReleaseKey('w')
            if KEY_CMD[0] != '':
                PressKey(KEY_CMD[0])
            if KEY_CMD[1] != '':
                PressKey(KEY_CMD[1])
        last_cmd = KEY_CMD
        time.sleep(0.1)

def f_control():
    '''
    control over key 'f'
    '''
    global KEY_CMD
    while IS_RUN:
        if IS_CTRL:
            if KEY_CMD[2] != '':
                PressKey(KEY_CMD[2])
                time.sleep(0.1)
                ReleaseKey(KEY_CMD[2])
                time.sleep(0.1)
                continue
        time.sleep(0.1)
        
def remove_isolated_pixels(image):
    (num_stats, labels, stats, _) = cv2.connectedComponentsWithStats(image, 8, cv2.CV_32S)
    new_image = image.copy()
    for label in range(num_stats):
        if stats[label,cv2.CC_STAT_AREA] == 1:
            new_image[labels == label] = 0
    return new_image

def p_pressed():
    '''
    Listening to key 'p'
    if 'p' is pressed toggle the ctrl state
    '''
    global IS_CTRL
    if IS_CTRL:
        logger.warning("************ USER PRESS P, SCRIPT PAUSE **************")
        IS_CTRL = False
        # Release all key
        ReleaseKey('a')
        ReleaseKey('s')
        ReleaseKey('d')
        ReleaseKey('w')
        text_msg3.set("Press 'p' to START mining\n Keep your camera facing RIGHT NORTH")
        label3.config(bg='red')
    else:
        logger.warning("************ USER PRESS P, RESUME MINEING **************")
        text_msg3.set("Press 'p' to STOP mining\n Keep your camera facing RIGHT NORTH")
        label3.config(bg='green')
        IS_CTRL = True

def xy2sm(p):
    sm_y = int(185.333 + int(p[0])*(126/27))
    sm_x = int(91.4615 + int(p[1])*(129/26))
    return (sm_y, sm_x)

def main():
    global IS_RUN, IS_CTRL, IS_DIED, KEY_CMD, N_DIC, P_LOC, GOAL_IDX, GOAL, GUI, T_REST, T_LAST_REACH_GOAL, T_LOGGER, SCREENS_MHW, MAIN_SLEEP,STATIC_MAP
    t_start = time.time()
    
    if SCREENS_MHW == None:
        # wait for the program to start initially.
        win32gui.EnumWindows(enum_cb, WIN_LIST)
        SCREENS_MHW = get_screens(GAME_TITLE)
        if SCREENS_MHW == None:
            logger.warning("Can't find MHW game. Please execute MHW!")
            text_msg1.set("Can't find MHW game. Please execute MHW!")
            label1.config(bg='red')
            MAIN_SLEEP = 1000
        else:
            # Get screen handle
            logger.info("Found MHW screen!")
            text_msg1.set("Found MHW screen!")
            label1.config(bg='green')
    
    # Try to get screen
    if SCREENS_MHW != None:
        try:
            img_window = np.array(ImageGrab.grab(bbox=win32gui.GetWindowRect(SCREENS_MHW[0])))
        except:
            SCREENS_MHW = None
            logger.warning("Can't find MHW game. Please execute MHW!")
            text_msg1.set("Can't find MHW game. Please execute MHW!")
            label1.config(bg='red')

    if SCREENS_MHW != None:
        # Check if is MHW window active
        if win32gui.GetWindowText(win32gui.GetForegroundWindow()) != GAME_TITLE.upper():
            IS_CTRL = False
        
        # Check if it's too long doesn't reach goal
        if (IS_CTRL) and (not IS_DIED) and time.time() - T_LAST_REACH_GOAL > KEEP_ALIVE:
            logger.warning("******************** CAN'T REACH GOAL FOR TOO LONG, GO HOME ************************** ")
            T_LAST_REACH_GOAL = time.time()
            # Throw homing ball
            for i in range(3):
                PressKey('3')
                time.sleep(0.8)
                ReleaseKey('3')
                time.sleep(0.8)

        # Get mini map
        (imgH, imgW, _) = img_window.shape # (1080, 1920)
        img_map = img_window[int(imgH*(740/1080)):int(imgW*(1024/1920)), int(imgH*(104/1080)):int(imgW*(400/1920))]
        # Resize img_map, make different resolution screen have some size mini-map.
        img_map = cv2.resize(img_map, (148, 142), interpolation=cv2.INTER_AREA)
        img_hsv = cv2.cvtColor(img_map, cv2.COLOR_RGB2HSV)

        # Mask 
        green_mask = cv2.inRange(img_hsv, NUM_HSV_LO, NUM_HSV_UP)
        remove_isolated_pixels(green_mask)
        
        # Get players location
        p_loc = (0,0,0)
        for ref in N_DIC:
            # Matching with number images
            res = cv2.matchTemplate(green_mask, IMG_DICT[ref], cv2.TM_CCOEFF_NORMED )
            max_cof = np.amax(res)
            loc = np.where(res == np.amax(res))
            pt = (loc[1][0], loc[0][0])
            # Get Bonus
            conf_bonus = 0.0
            # Positive bonus, if center is very near to the previous detected result.
            center  = (pt[0] + IMG_DICT[ref].shape[1]/2,
                        pt[1] + IMG_DICT[ref].shape[0]/2)
            conf_bonus = BONUS_MAX - (abs(center[0] - N_DIC[ref]['cent'][0]) +\
                                        abs(center[1] - N_DIC[ref]['cent'][1])) * BONUS_COF
            conf_bonus = 0.0 if conf_bonus < 0.0 else conf_bonus

            # Negative bonus, avoid two label overlap
            for ref_t in N_DIC:
                if ref_t != ref:
                    bonus_neg = BONUS_MAX - (abs(center[0] - N_DIC[ref_t]['cent'][0]) +\
                                                abs(center[1] - N_DIC[ref_t]['cent'][1])) * BONUS_COF
                    bonus_neg = 0.0 if bonus_neg < 0.0 else bonus_neg
                    conf_bonus -= bonus_neg
            
            # Get geometry
            if (max_cof + conf_bonus) > CONFIENT_THRES:
                N_DIC[ref]['x1'] = pt
                N_DIC[ref]['x2'] = (pt[0] + IMG_DICT[ref].shape[1],
                                    pt[1] + IMG_DICT[ref].shape[0])
                N_DIC[ref]['cent'] = (pt[0] + IMG_DICT[ref].shape[1]/2,
                                        pt[1] + IMG_DICT[ref].shape[0]/2)
                N_DIC[ref]['conf'] = max_cof + conf_bonus
                
                if DEBUG:
                    # Draw rectangle and text
                    img_map = cv2.putText(img_map, ref, N_DIC[ref]['x1'],
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1, cv2.LINE_AA)
                    img_map = cv2.putText(img_map, str(N_DIC[ref]['conf']), N_DIC[ref]['x2'],
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1, cv2.LINE_AA)
                    cv2.rectangle(img_map, N_DIC[ref]['x1'], N_DIC[ref]['x2'], (255, 0, 255), 1)

                # Get player location
                px = N_DIC[ref]['global_loc'][0] - (N_DIC[ref]['cent'][0] - CENTER_P[0])
                py = N_DIC[ref]['global_loc'][1] - (N_DIC[ref]['cent'][1] - CENTER_P[1])
                N_DIC[ref]['player_loc'] = (px, py)
                
                # Find the max confident label's player location 
                if max_cof + conf_bonus > p_loc[2]:
                    p_loc = (px, py, max_cof + conf_bonus)
            
        # Update player's location
        if p_loc != (0,0,0):
            P_LOC = p_loc

        # Check if player's location has been initilized
        if P_LOC == (0,0,0):
            logger.warning("Can't get player's location. Please make sure you're at East Camp(3) of the Guilding Land")
            text_msg2.set("Can't find location.\nPlease make sure you're at East Camp(3) of the Guilding Land")
            label2.config(bg="red")
            IS_CTRL = False
            MAIN_SLEEP = 1000
        else:
            MAIN_SLEEP = 10
            text_msg2.set("Found player's location")
            label2.config(bg="green")
            if text_msg3.get() == '':
                label3.config(bg="red")
                text_msg3.set("Press 'p' to START mining\n Keep your camera facing RIGHT NORTH")

        # Check if player's dead or not
        if abs(P_LOC[0] - DEATH_LOC[0]) < DEATH_TOR and abs(P_LOC[1] - DEATH_LOC[1]) < DEATH_TOR:
            GOAL = THE_WAY_BACK
            GOAL_IDX = 0
            IS_DIED = True
            logger.warning("************** I HAVE DIED ***************")
        
        dx, dy = (GOAL[GOAL_IDX][0] - P_LOC[0], GOAL[GOAL_IDX][1] - P_LOC[1])
        
        # Reached goal, set next goal 
        if T_REST != None or (abs(dx) <= GOAL_TOR and abs(dy) <= GOAL_TOR):
            T_LAST_REACH_GOAL = time.time()
            # Rest a while at this goal 
            if T_REST != None:
                if time.time() - T_REST > GOAL[GOAL_IDX][-1]:
                    T_REST = None
                    # go back to mining zone
                    if IS_DIED and GOAL_IDX == len(GOAL)-1:
                        IS_DIED = False
                        GOAL = WORKING_LIST
                        GOAL_IDX = 0
                        logger.warning("*************** I'M BACK TO WORK ******************")
                    else:
                        GOAL_IDX = (GOAL_IDX+1)%len(GOAL)
            else:
                T_REST = time.time()
        else:
            T_REST = None

        # Control keyboard
        KEY_CMD = ['', '', '']
        if T_REST == None and abs(dx) > GOAL_TOR:
            KEY_CMD[0] = "d" if dx > 0 else "a"
        else:
            KEY_CMD[0] = ''
        
        if T_REST == None and abs(dy) > GOAL_TOR:
            KEY_CMD[1] = "s" if dy > 0 else "w"
        else:
            KEY_CMD[1] = ''
        
        KEY_CMD[2] = '' if IS_DIED else 'f'
        
        # Logger
        if time.time() - T_LOGGER > LOGGER_TIME:
            logger.info("Player Location : " + str(P_LOC))
            logger.info("Current Goal : " + str(GOAL[GOAL_IDX]))
            logger.info("(dx, dy) =  " + str((dx, dy)))
            logger.info("KEY_CMD : " + str(KEY_CMD))
            logger.info("FPS : " + str(int(1/(time.time() - t_start))))
            logger.info("========================")
            T_LOGGER = time.time()
        
        # Show images
        if DEBUG:
            green_mask = cv2.cvtColor(green_mask, cv2.COLOR_GRAY2RGB)
            green_mask = cv2.resize(green_mask, (green_mask.shape[1]*2, green_mask.shape[0]*2))
            img_map = cv2.cvtColor(img_map, cv2.COLOR_BGR2RGB)
            img_map = cv2.resize(img_map, (img_map.shape[1]*2, img_map.shape[0]*2))
            img_debug = cv2.hconcat([green_mask, img_map])
            cv2.imshow('img_debug', img_debug)

            # Draw player location
            img_static_map = cv2.circle(copy.deepcopy(STATIC_MAP), xy2sm(P_LOC), 1, (0, 255, 0), 10)
            # Draw goal location
            img_static_map = cv2.circle(img_static_map, xy2sm(GOAL[GOAL_IDX][:2]), 10, (0, 0, 255), 3)
            # Draw Arrow
            img_static_map = cv2.arrowedLine(img_static_map, xy2sm(P_LOC), xy2sm(GOAL[GOAL_IDX][:2]),
                                             (0, 255, 255), 2, tipLength = 0.1)
            cv2.imshow("STATIC_MAP", img_static_map)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                IS_RUN = False
    # Recursive call main()
    GUI.after(MAIN_SLEEP, main)

if __name__ == '__main__':
    # Set up logger
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    logger = logging.getLogger('logger')
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    # Record logging message at logging file
    h_file = logging.FileHandler("mine_dragonite.log")
    h_file.setFormatter(formatter)
    h_file.setLevel(logging.INFO)
    logger.addHandler(h_file)
    
    # MHW state
    IS_RUN = True # Close all thread when program is down
    IS_DIED = False # Check if character go back home
    IS_CTRL = False # Check if user allow script control keyboard
    KEY_CMD = ['', '', '']# "", 'a', 'w', 'd' # KEY_CMD sent to keyboard
    GOAL_IDX = 0
    P_LOC = (0,0,0)
    SCREENS_MHW = None
    #Timers 
    T_REST = None # timer to rest after reached goal
    T_LAST_REACH_GOAL = time.time() # timer to check script is stuck or not.
    T_LOGGER  = time.time()

    # Listen to key 'p'
    p_listener = pynput.keyboard.GlobalHotKeys({'p': p_pressed})
    p_listener.start()

    # Load number image 
    IMG_11 = cv2.imread("guilding_land_pic/eleven.png" ,cv2.IMREAD_GRAYSCALE)
    IMG_10 = cv2.imread("guilding_land_pic/ten.png" ,cv2.IMREAD_GRAYSCALE)
    IMG_4 = cv2.imread("guilding_land_pic/four.png" ,cv2.IMREAD_GRAYSCALE)
    IMG_3 = cv2.imread("guilding_land_pic/three.png" ,cv2.IMREAD_GRAYSCALE)
    IMG_DICT = {'3' : IMG_3, '4' : IMG_4, '10' : IMG_10, '11' : IMG_11}
    if DEBUG:
        STATIC_MAP = cv2.imread("guilding_land_pic/map_bg.png") # For debugging
        CLS_COLOR = {-1 : (255,0,0), 2 : (0,0,255)}
        for LIST in [WORKING_LIST, THE_WAY_BACK]:
            for i,(x,y,name,cls) in enumerate(LIST):
                STATIC_MAP = cv2.circle(STATIC_MAP, xy2sm((x,y)), 1, CLS_COLOR[cls], 5)
                cv2.putText(STATIC_MAP, str(i), (xy2sm((x,y))[0]-5, xy2sm((x,y))[1]-5), cv2.FONT_HERSHEY_PLAIN,
                            1, (0, 255, 255), 1, cv2.LINE_AA)
    
    GOAL = WORKING_LIST
    # 
    N_DIC = {
            '3' : {
                'x1' : (0,0),
                'x2' : (0,0),
                'cent' : (0,0),
                'conf' : 0.0,
                'global_loc' : (-42.5,83),
                'player_loc' : (0,0)},
            '4' : {
                'x1' : (0,0),
                'x2' : (0,0),
                'cent' : (0,0),
                'conf' : 0.0,
                'global_loc' : (0,0),
                'player_loc' : (0,0)},
            '10' : {
                'x1' : (0,0),
                'x2' : (0,0),
                'cent' : (0,0),
                'conf' : 0.0,
                'global_loc' : (68, 38),
                'player_loc' : (0,0)},
            '11' : {
                'x1' : (0,0),
                'x2' : (0,0),
                'cent' : (0,0),
                'conf' : 0.0,
                'global_loc' : (19, 103),
                'player_loc' : (0,0)}}

    # Init threads
    t_key = threading.Thread(target = key_control) # control 'a', 's', 'd', 'w'
    t_key.start()
    t_f = threading.Thread(target = f_control) # control 'f'
    t_f.start()
    
    # Tk window and frame
    GUI = tk.Tk()
    GUI.title("mine_dragonite")# title of window
    GUI.iconphoto(False, tk.PhotoImage(file='guilding_land_pic/icon.png'))# icon of window
    # GUI.geometry('350x350') # dont specify, tk will automatic assign a proper size.
    GUI.resizable(0,0) # disable resize window 
    
    text_msg1 = tk.StringVar()
    text_msg2 = tk.StringVar()
    text_msg3 = tk.StringVar()
    label1 = tk.Label(GUI, textvariable=text_msg1, font = ("Helvetica", 30) ,bg="red")
    label2 = tk.Label(GUI, textvariable=text_msg2, font = ("Helvetica", 30) ,bg="red")
    label3 = tk.Label(GUI, textvariable=text_msg3, font = ("Helvetica", 30) ,bg="red")
    label1.pack()
    label2.pack()
    label3.pack()

    try:
        main() # Recursive call main()
        GUI.mainloop()
    except (Exception, KeyboardInterrupt) as e:
        IS_RUN = False
        logger.error("Catched Exception!")
        logger.error(e) 
    IS_RUN = False
    try:
        GUI.destroy()# terminate TK gui
    except:
        pass # TK is already gone.
