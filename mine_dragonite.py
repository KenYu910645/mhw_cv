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

# Configuration
DEBUG = False
GAME_TITLE = 'monster hunter: world(421471)' # windows title must cantain these characters
KEEP_ALIVE = 120 # sec
GOAL_TOR = 0.5
# Color range
NUM_HSV_LO = (30, 0, 0) # Green number on mini-map
NUM_HSV_UP = (45, 255, 255)
CONFIENT_THRES = 0.75 # If confient higher then threshold, then detect as a number.
CENTER_P = (74, 71) # The location of player in mini-map(always center)
BONUS_MAX = 0.2 # Match confident will received a bonus, if it's very near its previous detected location.
BONUS_COF = 0.02 # 0.2/10 <- 10 is the pixel range you wanna allow
# Death 
DEATH_LOC = (-23, 73) # Consider been killed if player near this location
DEATH_TOR = 2 # The radius of the death zone.


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
    else:
        logger.warning("************ USER PRESS P, RESUME MINEING **************")
        IS_CTRL = True

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

    try:
        winlist = []
        names = list_all_windows_name()
        # print(names)
        
        screen = None
        while screen == None:
            for name in names:
                if GAME_TITLE in name:
                    screen = name
                    logger.info("Windows name: " + screen)
            logger.warning("Can't find MHW game. Please execute MHW!")
            time.sleep(0.1)
        logger.info("Found MHW screen!")
        screens = get_screens(screen)
        
        # MHW state
        IS_RUN = True # Close all thread when program is down
        IS_DIED = False # Check if character go back home
        IS_CTRL = False # Check if user allow script control keyboard
        KEY_CMD = ['', '', '']# "", 'a', 'w', 'd' # KEY_CMD sent to keyboard
        t_rest = None # timer to rest after reached goal
        t_last_reach_goal = time.time() # timer to check script is stuck or not.
        
        # Init threads
        t_key = threading.Thread(target = key_control) # control 'a', 's', 'd', 'w'
        t_key.start()
        t_f = threading.Thread(target = f_control) # control 'f'
        t_f.start()

        # Listen to key 'p'
        p_listener = pynput.keyboard.GlobalHotKeys({'p': p_pressed})
        p_listener.start()

        # Load number image 
        IMG_11 = cv2.imread("guilding_land_pic/eleven.png" ,cv2.IMREAD_GRAYSCALE)
        IMG_10 = cv2.imread("guilding_land_pic/ten.png" ,cv2.IMREAD_GRAYSCALE)
        IMG_4 = cv2.imread("guilding_land_pic/four.png" ,cv2.IMREAD_GRAYSCALE)
        IMG_3 = cv2.imread("guilding_land_pic/three.png" ,cv2.IMREAD_GRAYSCALE)
        IMG_DICT = {'3' : IMG_3, '4' : IMG_4, '10' : IMG_10, '11' : IMG_11}
        WORKING_LIST = [
                (30, 24, 'mine_10', 2),
                (30, 52, 'neck_point', -1), 
                (26, 55.5, 'mine_neck', 2),
                (26, 65, 'mid_11', -1),
                (16.5, 55, 'upper_vein', -1), 
                (23, 48, 'mine_bridge_right', 2),
                (16.5, 55, 'upper_vein', -1),
                (11, 62, 'mine_bridge_left', 2),
                (12.5, 76.0, 'lower_vein', -1),
                (19, 75, 'trail_11', 2),
                (41, 87, 'bone_11', 2),
                (26, 65, 'mid_11', -1),
                (30, 52, 'neck_point', -1),
                (51, 39, 'super_mine', 2),
                (58, 27, 'trail_10', 2),
                (61, 22, 'bone_10', 2),
                (68.5, 11, 'mine_cats', 2),
                (70, 8, 'trail_cats', 2),
                (69, -2, 'upper_vein', -1),
                (73, -6, 'lower_vein', -1),
                (70, -10, 'super_bone', 2),
                (73, -6, 'lower_vein', -1),
                (63, 2, 'upper_vein', -1),
                (56.5, 8, 'bone_tree', 2),
                (44, 6, 'avoid_deer_1', -1),
                (33, 11, 'avoid_deer_2', -1)]

        THE_WAY_BACK = [(-25.5, 68, 'mid_home', -1),
                        (-26.5, 59, 'upper_vein', -1),
                        (-29, 52, 'lower_vein', -1),
                        (-18, 49, 'transition', -1),
                        (3, 24, 'entry_point', -1),
                        (28, 9, 'mid_4', -1),
                        (51, 18 ,'mid_10', -1)]
        GOAL_IDX = 0
        GOAL = WORKING_LIST
        P_LOC = (0,0,0)
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

        while IS_RUN:
            t_start = time.time()
            
            # Check if is MHW window active
            if win32gui.GetWindowText(win32gui.GetForegroundWindow()) != GAME_TITLE.upper():
                IS_CTRL = False
            
            # Check if it's too long doesn't reach goal
            if (IS_CTRL) and (not IS_DIED) and time.time() - t_last_reach_goal > KEEP_ALIVE:
                logger.warning("******************** CAN'T REACH GOAL FOR TOO LONG, GO HOME ************************** ")
                t_last_reach_goal = time.time()
                # Throw homing ball
                for i in range(3):
                    PressKey('3')
                    time.sleep(0.8)
                    ReleaseKey('3')
                    time.sleep(0.8)
            
            # Convert to array
            img_window = np.array(ImageGrab.grab(bbox=win32gui.GetWindowRect(screens[0][0])))
            (imgH, imgW, _) = img_window.shape # (1080, 1920)
            # Get mini map
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
                
                # Get Bonus
                conf_bonus = 0.0
                for pt in zip(*loc[::-1]):
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
                    for pt in zip(*loc[::-1]):
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

            # Check player's location has been init
            if P_LOC == (0,0,0):
                logger.warning("Can't get player's location. Please make sure you're at East Camp(3) of the Guilding Land")
                IS_CTRL = False

            # Check player's death or not
            if abs(P_LOC[0] - DEATH_LOC[0]) < DEATH_TOR and abs(P_LOC[1] - DEATH_LOC[1]) < DEATH_TOR:
                GOAL = THE_WAY_BACK
                GOAL_IDX = 0
                IS_DIED = True
                logger.warning("************** I HAVE DIED ***************")
            
            dx, dy = (GOAL[GOAL_IDX][0] - P_LOC[0], GOAL[GOAL_IDX][1] - P_LOC[1])
            
            # Reach goal, change to next one 
            if t_rest != None or (abs(dx) <= GOAL_TOR and abs(dy) <= GOAL_TOR):
                t_last_reach_goal = time.time()
                # Relex a while at goal 
                if t_rest != None:
                    if time.time() - t_rest > GOAL[GOAL_IDX][-1]:
                        t_rest = None
                        # go back to mining zone
                        if IS_DIED and GOAL_IDX == len(GOAL)-1:
                            IS_DIED = False
                            GOAL = WORKING_LIST
                            GOAL_IDX = 0
                            logger.warning("*************** I'M BACK TO WORK ******************")
                        else:
                            GOAL_IDX = (GOAL_IDX+1)%len(GOAL)
                else:
                    t_rest = time.time()
            else:
                t_rest = None

            # Control keyboard
            KEY_CMD = ['', '', '']
            if t_rest == None and abs(dx) > GOAL_TOR:
                KEY_CMD[0] = "d" if dx > 0 else "a"
            else:
                KEY_CMD[0] = ''
            
            if t_rest == None and abs(dy) > GOAL_TOR:
                KEY_CMD[1] = "s" if dy > 0 else "w"
            else:
                KEY_CMD[1] = ''
            
            KEY_CMD[2] = '' if IS_DIED else 'f'
            
            # Logger
            logger.info("Player Location : " + str(P_LOC))
            logger.info("Current Goal : " + str(GOAL[GOAL_IDX]))
            logger.info("(dx, dy) =  " + str((dx, dy)))
            logger.info("KEY_CMD : " + str(KEY_CMD))
            logger.info("FPS : " + str(int(1/(time.time() - t_start))))
            logger.info("========================")
            
            # Show images
            if DEBUG:
                cv2.imshow('green_mask', green_mask)
                cv2.imshow('window',cv2.cvtColor(img_map, cv2.COLOR_BGR2RGB))
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    IS_RUN = False
    except (Exception, KeyboardInterrupt) as e:
        IS_RUN = False
        logger.error("Catched Exception!")
        logger.error(e)