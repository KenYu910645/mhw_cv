import win32gui
import numpy as np
import pydirectinput # This one is slower than pyautogui, but only this one can control keyboard
import threading
import random
import time
from PIL import ImageGrab
import cv2

# Configuration
DEBUG = True

GAME_TITLE = 'monster hunter: world(421471)' # windows title must cantain these characters
RESIZE_SCALE = 0.5
KEEP_ALIVE = 2 # sec
guess_table = { 0 : '123',
                1 : '132',
                2 : '213',
                3 : '231',
                4 : '312',
                5 : '321'}

keyboard_map = {'1' : 'a',
                '2' : 'w',
                '3' : 'd'}

# Color range
YELLOW_MARK_HSV_UP = (35, 130, 255) # HSV = (30,126,255) 
YELLOW_MARK_HSV_LO = (25,  120,  200)
GRAY_CROSS_HSV_UP = (5, 5, 140) # HSV = (0, 0, 131)
GRAY_CROSS_HSV_LO = (0,  0,  125)
WRITE_CHAR_HSV_UP = (60, 30, 255) # HSV = (30,1,230)
WRITE_CHAR_HSV_LO = (0,  0, 140)
# WRITE_CHAR_HSV_UP = (0, 0, 255) # HSV = (30,1,230)
# WRITE_CHAR_HSV_LO = (0,  0, 150)
ANS_HSV_UP = (0, 0, 245)
ANS_HSV_LO = (0, 0, 200)
HINT_HSV_UP = (40, 180, 255)
HINT_HSV_LO = (10,  60, 230)

# If mask image have enough pixels will be recognized as a result
CORRECT_THRES = 60 # 74
WRONG_THRES = 60 # 76
READY_THRES = 40 # 70 # 100 
ANS_THRES = 30 # 0,1,2
HINT_THRES = 50 # 40 # 
TEXT_DOWN_OFFSET = 20

# Text log location
LOG_LOC = (25, 310)
LOG_COLOR = (255,255,255)
LOG_HEIGHT = 18

# DEBUG image location
DEBUG_LOC = (800, 250)

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
    global is_run, KEY_CMD, B_DIC
    is_last_ans = False
    while is_run:
        if KEY_CMD != "":
            mutex.acquire()
            key = KEY_CMD[0]
            print("Try Pressing " + key )
            pydirectinput.press(keyboard_map[key])

            # Check if the box is pressed
            if B_DIC['b' + key]['result'] != 'READY':
                # The pressing is done
                print("Pressed " + key)
                KEY_CMD = KEY_CMD[1:]
            
            # Check if a new answer appeared
            if B_DIC['b1']['answer'] != '':
                if not is_last_ans : # It's a new answer
                    if len(KEY_CMD) <= 1:
                        print("Get answer! finish key_control")
                        KEY_CMD = ""
                    else: # Reject clear cmd
                        print("Get answer! But reject clear cmd, because new cmd arrived.")
                        
                is_last_ans = True
            else:
                is_last_ans = False
            mutex.release()
        else:
            time.sleep(0.1)

def switch_mode(mode):
    '''
    mode = 'default','fullpower', 'cats', 'unknown'
    '''
    global B_DIC, IMG_123, CUR_MODE
    CUR_MODE = mode
    if mode == 'default':
        LEFT_UP_X = 820
        LEFT_UP_Y = 870
        INTERVAL_12 = 300
        INTERVAL_13 = 600
        BOX_H = 58 # Hit box size
        BOX_W = 78
        ANS_H = 70 # Ans box size
        ANS_W = 78
    elif mode == 'fullpower':
        LEFT_UP_X = 762
        LEFT_UP_Y = 870
        INTERVAL_12 = 420
        INTERVAL_13 = 800
        BOX_H = 58 # Hit box size
        BOX_W = 78
        ANS_H = 70 # Ans box size
        ANS_W = 78
    elif mode == 'cats':
        LEFT_UP_X = 492
        LEFT_UP_Y = 870
        INTERVAL_12 = 480
        INTERVAL_13 = 930
        BOX_H = 58 # Hit box size
        BOX_W = 78
        ANS_H = 70 # Ans box size
        ANS_W = 78
    
    # Calculate boxes location 
    B_DIC['b1']['c1'] = (int((LEFT_UP_X)*RESIZE_SCALE), int(LEFT_UP_Y*RESIZE_SCALE)) # (col, row)
    B_DIC['b1']['c2'] = (int((LEFT_UP_X + BOX_W )*RESIZE_SCALE), int((LEFT_UP_Y + BOX_H)*RESIZE_SCALE)) # (col, row)
    B_DIC['b1']['a1'] = (int((LEFT_UP_X)*RESIZE_SCALE), int((LEFT_UP_Y - ANS_H)*RESIZE_SCALE)) # (col, row)
    B_DIC['b1']['a2'] = (int((LEFT_UP_X + ANS_W)*RESIZE_SCALE), int((LEFT_UP_Y)*RESIZE_SCALE)) # (col, row)

    B_DIC['b2']['c1'] = (int((LEFT_UP_X + INTERVAL_12)*RESIZE_SCALE), int(LEFT_UP_Y*RESIZE_SCALE)) # (col, row)
    B_DIC['b2']['c2'] = (int((LEFT_UP_X + BOX_W + INTERVAL_12)*RESIZE_SCALE), int((LEFT_UP_Y + BOX_H)*RESIZE_SCALE)) # (col, row)
    B_DIC['b2']['a1'] = (int((LEFT_UP_X + INTERVAL_12)*RESIZE_SCALE), int((LEFT_UP_Y - ANS_H)*RESIZE_SCALE)) # (col, row)
    B_DIC['b2']['a2'] = (int((LEFT_UP_X + ANS_W + INTERVAL_12)*RESIZE_SCALE), int((LEFT_UP_Y)*RESIZE_SCALE)) # (col, row)

    B_DIC['b3']['c1'] = (int((LEFT_UP_X + INTERVAL_13)*RESIZE_SCALE), int(LEFT_UP_Y*RESIZE_SCALE)) # (col, row)
    B_DIC['b3']['c2'] = (int((LEFT_UP_X + BOX_W + INTERVAL_13)*RESIZE_SCALE), int((LEFT_UP_Y + BOX_H)*RESIZE_SCALE)) # (col, row)
    B_DIC['b3']['a1'] = (int((LEFT_UP_X + INTERVAL_13)*RESIZE_SCALE), int((LEFT_UP_Y - ANS_H)*RESIZE_SCALE)) # (col, row)
    B_DIC['b3']['a2'] = (int((LEFT_UP_X + ANS_W + INTERVAL_13)*RESIZE_SCALE), int((LEFT_UP_Y)*RESIZE_SCALE)) # (col, row)

    # Load reference image
    _,IMG_1 = cv2.threshold(cv2.imread('1_' + mode + '.jpg', cv2.IMREAD_UNCHANGED),127,255,cv2.THRESH_BINARY)
    _,IMG_2 = cv2.threshold(cv2.imread('2_' + mode + '.jpg', cv2.IMREAD_UNCHANGED),127,255,cv2.THRESH_BINARY)
    _,IMG_3 = cv2.threshold(cv2.imread('3_' + mode + '.jpg', cv2.IMREAD_UNCHANGED),127,255,cv2.THRESH_BINARY)
    IMG_123 =  [IMG_1, IMG_2, IMG_3]

def show_text(img, text):
    # Draw a solid rectangle 
    img = cv2.rectangle(img, LOG_LOC, (LOG_LOC[0] + 200, LOG_LOC[1] + (len(text)+1)*LOG_HEIGHT), (0, 0, 0), -1)
    
    for i in range(len(text)):
        img = cv2.putText(img,
                          text[i],
                          (LOG_LOC[0], LOG_LOC[1] + LOG_HEIGHT*(i+1)),
                          cv2.FONT_HERSHEY_SIMPLEX,
                          0.5,
                          LOG_COLOR,
                          1,
                          cv2.LINE_AA)

if __name__ == '__main__':
    try:
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
        IS_LAST_ANS = False
        KEY_CMD = "" # 'a', 'w', 'd'
        CUR_GUESS = ""
        CUR_MODE = "default"
        WIN_TIME = 0
        B_DIC = {'b1': {'c1': (None, None),
                        'c2': (None, None),
                        'a1': (None, None),
                        'a2': (None, None),
                        'yellow_num' : None,
                        'gray_num' : None,
                        'write_num' : None,
                        'hint_num' : None,
                        'result' : '',
                        'answer' : '',
                        'hint' : False},
                'b2': {'c1': (None, None),
                        'c2': (None, None),
                        'a1': (None, None),
                        'a2': (None, None),
                        'yellow_num' : None,
                        'gray_num' : None,
                        'write_num' : None,
                        'hint_num' : None,
                        'result' : '',
                        'answer' : '',
                        'hint' : False},
                'b3': {'c1': (None, None),
                        'c2': (None, None),
                        'a1': (None, None),
                        'a2': (None, None),
                        'yellow_num' : None,
                        'gray_num' : None,
                        'write_num' : None,
                        'hint_num' : None,
                        'result' : '',
                        'answer' : '',
                        'hint' : False}}
        HISTORY = [] # [('guess', 'result', 'answer'), ....]
        # Init box location
        switch_mode(CUR_MODE)

        # Init threads
        t_key = threading.Thread(target = key_control)
        t_key.start()
        mutex = threading.Lock()

        # time til last alive observe
        t_alive = time.time()

        # Switch mode, for unknown mode
        mode_list = ['default', 'fullpower', 'cats']
        mode_idx = 0

        while is_run:
            t_start = time.time()
            
            # Check if is MHW window active
            if win32gui.GetWindowText(win32gui.GetForegroundWindow()) != "MONSTER HUNTER: WORLD(421471)":
                continue
            
            # Convert to array
            img_window = np.array(ImageGrab.grab(bbox=win32gui.GetWindowRect(screens[0][0])))
            
            # Resize
            (imgH, imgW, _) = img_window.shape
            img_mhw = cv2.resize(img_window, (int(imgW*RESIZE_SCALE), int(imgH*RESIZE_SCALE)), interpolation=cv2.INTER_AREA)
            (h, w, _) = img_mhw.shape

            # Check if it's death for too long 
            if time.time() - t_alive > KEEP_ALIVE:
                mode_idx += 1
                switch_mode(mode_list[mode_idx%len(mode_list)])
                CUR_MODE = 'unknown'

            # Draw rectangle on boxes
            for i in ['b1', 'b2', 'b3']:
                cv2.rectangle(img_mhw, B_DIC[i]['c1'], B_DIC[i]['c2'], (255,0,0), 1) # Red 
                cv2.rectangle(img_mhw, B_DIC[i]['a1'], B_DIC[i]['a2'], (255,0,255), 1)# Magenta
            
            # Observer answer
            mask_con = []
            for i in ['b1', 'b2', 'b3']:
                ans_hsv = cv2.cvtColor(img_mhw[B_DIC[i]['a1'][1]:B_DIC[i]['a2'][1],
                                            B_DIC[i]['a1'][0]:B_DIC[i]['a2'][0]],
                                            cv2.COLOR_RGB2HSV)
                ans_mask = cv2.inRange(ans_hsv, ANS_HSV_LO, ANS_HSV_UP)
                
                # Show maskes
                mask_con.append(ans_mask) # axis = 0 is vertical

                mask_count = []
                mask_tmp = []
                for ii in IMG_123:
                    mask_xor = cv2.bitwise_xor(ii, ans_mask)
                    mask_count.append(cv2.countNonZero(mask_xor))
                    mask_tmp.append(mask_xor)

                # img_tmp = np.concatenate(mask_tmp, axis=1) # axis = 0 is vertical
                # cv2.imshow('tmp', img_tmp)
                # print(mask_count)
                
                B_DIC[i]['answer'] = ''
                for ii in range(3):
                    if mask_count[ii] < ANS_THRES:
                        B_DIC[i]['answer'] = str(ii+1)
                        break

                # Draw text on top of boxes
                img_mhw = cv2.putText(img_mhw, B_DIC[i]['answer'], (B_DIC[i]['a1'][0] + 10, B_DIC[i]['a2'][1] - 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2, cv2.LINE_AA)
            

            # Check WIN/LOSE
            ans = B_DIC['b1']['answer'] + B_DIC['b2']['answer'] + B_DIC['b3']['answer']
            # if ans != '':
            if len(ans) == 3:
                if not IS_LAST_ANS:
                    IS_LAST_ANS = True
                    if ans == CUR_GUESS or CUR_MODE == 'cat':
                        HISTORY.append((CUR_GUESS, "WIN ", ans))
                        WIN_TIME += 1
                    else:
                        HISTORY.append((CUR_GUESS, "LOSE", ans))
            else:
                IS_LAST_ANS = False

            # Save maskes images
            # cv2.imwrite('1_cats.jpg', mask_con[0])
            # cv2.imwrite('2_cats.jpg', mask_con[1])
            # cv2.imwrite('3_cats.jpg', mask_con[2])

            # Show maskes
            if DEBUG:
                img_ans = np.concatenate(mask_con, axis=1) # axis = 0 is vertical
                img_ans = cv2.cvtColor(img_ans, cv2.COLOR_GRAY2RGB)
                (ans_h, ans_w, _) = img_ans.shape
                img_mhw[DEBUG_LOC[1]:DEBUG_LOC[1]+ans_h, DEBUG_LOC[0]:DEBUG_LOC[0]+ans_w] = img_ans                

            # Observe results
            mask_con = []
            for i in ['b1', 'b2', 'b3']:
                box_hsv = cv2.cvtColor(img_mhw[B_DIC[i]['c1'][1]:B_DIC[i]['c2'][1],
                                               B_DIC[i]['c1'][0]:B_DIC[i]['c2'][0]],
                                               cv2.COLOR_RGB2HSV)
                # Get mask
                yellow_mask = cv2.inRange(box_hsv, YELLOW_MARK_HSV_LO, YELLOW_MARK_HSV_UP)
                gray_mask   = cv2.inRange(box_hsv, GRAY_CROSS_HSV_LO,  GRAY_CROSS_HSV_UP)
                write_mask  = cv2.inRange(box_hsv, WRITE_CHAR_HSV_LO,  WRITE_CHAR_HSV_UP)
                hint_mask  = cv2.inRange(box_hsv, HINT_HSV_LO,  HINT_HSV_UP)
                
                # Get mask count
                B_DIC[i]['yellow_num'] = cv2.countNonZero(yellow_mask)
                B_DIC[i]['gray_num'] = cv2.countNonZero(gray_mask)
                B_DIC[i]['write_num'] = cv2.countNonZero(write_mask)
                B_DIC[i]['hint_num'] = cv2.countNonZero(hint_mask)

                # Show maskes
                mask_con.append(np.concatenate([yellow_mask, gray_mask, write_mask, hint_mask], axis=1)) # axis = 0 is vertical

                # Get result
                if B_DIC[i]['yellow_num'] > CORRECT_THRES:
                    B_DIC[i]['result'] = 'CORRECT'
                elif B_DIC[i]['gray_num'] > WRONG_THRES:
                    B_DIC[i]['result'] = 'WRONG'
                elif B_DIC[i]['write_num'] > READY_THRES:
                    B_DIC[i]['result'] = 'READY'
                else:
                    B_DIC[i]['result'] = ''

                img_mhw = cv2.putText(img_mhw, B_DIC[i]['result'], (B_DIC[i]['c1'][0], B_DIC[i]['c2'][1] + TEXT_DOWN_OFFSET),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
                # Get hint T/F
                if B_DIC[i]['hint_num'] > HINT_THRES:
                    B_DIC[i]['hint'] = True
                else:
                    B_DIC[i]['hint'] = False

            # Show maskes
            if DEBUG:
                img_mask = np.concatenate(mask_con, axis=0)
                img_mask = cv2.cvtColor(img_mask, cv2.COLOR_GRAY2RGB)
                (mask_h, mask_w, _) = img_mask.shape
                img_mhw[DEBUG_LOC[1]+50:DEBUG_LOC[1]+50+mask_h, DEBUG_LOC[0]:DEBUG_LOC[0]+mask_w] = img_mask

            
            if CUR_MODE != 'cats':
                if  B_DIC['b1']['result'] == 'READY' and\
                    B_DIC['b2']['result'] == 'READY' and\
                    B_DIC['b3']['result'] == 'READY' and\
                    KEY_CMD == "":
                    # Get a new guess
                    guess = guess_table[random.randint(0, 5)]
                    if mutex.acquire(blocking = False):# Critical Section
                        KEY_CMD = guess
                        mutex.release()
                        print("New Guess: " + guess)
                    CUR_GUESS = guess
            else:
                CUR_GUESS = ""
                # Cats modes hints
                for i in ['b1', 'b2', 'b3']:
                    if B_DIC[i]['result'] == 'READY' and B_DIC[i]['hint']:
                        if mutex.acquire(blocking = False):
                            KEY_CMD = i[-1]
                            mutex.release()
                            print("Get Hint at " + str(i))

            if  B_DIC['b1']['result'] != '' and \
                B_DIC['b2']['result'] != '' and \
                B_DIC['b3']['result'] != '':
                if CUR_MODE == 'unknown':
                    switch_mode(mode_list[mode_idx%len(mode_list)])
                t_alive = time.time()

            # Calculate win rate 
            try:
                win_rate = WIN_TIME/len(HISTORY)
            except ZeroDivisionError:
                win_rate = 0

            # Put text on window
            if HISTORY == []:
                last_his = ('', '', '')
            else:
                last_his = HISTORY[-1]
            text = ['Mode: ' + CUR_MODE,
                    'Guess: ' + CUR_GUESS,
                    'Last Result: ' + last_his[1],
                    'Last Answer: ' + last_his[2],
                    'Win Rate: ' + str(round(win_rate,2)),
                    '-------']
            
            for i in [-1, -2 ,-3, -4, -5]:
                try:
                    text.append(HISTORY[i][0] + " " + HISTORY[i][1] + " " + HISTORY[i][2])
                except:
                    break
            show_text(img_mhw, text)

            # print("loop took {} seconds".format(time.time() - t_start))
            
            # Show image
            cv2.imshow('window',cv2.cvtColor(img_mhw, cv2.COLOR_BGR2RGB))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                is_run = False
    except (Exception, KeyboardInterrupt) as e:
        is_run = False
        print("Catched Exception!")
        print(e)
        t_key.join()