import threading
import time
import math
import sys
import os
import tkinter as tk
from tkinter import ttk
import cv2
import pytesseract
from PIL import ImageGrab
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'

'''
Convert coordinates for different screen sizes. Only works for 16:9 format.
'''
class ScreenConverter:
    def __init__(self):
        self.base_x = 1920
        
        self.value = {}
        
        self.value['dead_x'] = 1818
        self.value['dead_y'] = 52
        
        self.value['last_x'] = 1000
        self.value['last_y'] = 25
        
        self.value['contour_area_min'] = 120
        self.value['contour_height_max'] = 60
        self.value['contour_height_min'] = 25
        self.value['contour_width_max'] = 45
        self.value['contour_width_min'] = 5
        self.value['contour_diff_dist_max'] = 45
        self.value['contour_diff_height_max'] = 5
        self.value['contour_diff_y_max'] = 5
        
        self.value['check_left_first_x1'] = 110
        self.value['check_left_first_x2'] = 190
        self.value['check_left_first_y1'] = 870
        self.value['check_left_first_y2'] = 970
        
        self.value['check_left_x1'] = 110
        self.value['check_left_x2'] = 160
        self.value['check_left_y1'] = 780
        self.value['check_left_y2'] = 930
        
        self.value['check_right_first_x1'] = 110
        self.value['check_right_first_x2'] = 190
        self.value['check_right_first_y1'] = 1325
        self.value['check_right_first_y2'] = 1425
        
        self.value['check_right_x1'] = 110
        self.value['check_right_x2'] = 160
        self.value['check_right_y1'] = 1065
        self.value['check_right_y2'] = 1210

        self.value['check_balls_x1'] = 775
        self.value['check_balls_x2'] = 825
        self.value['check_balls_y1'] = 933
        self.value['check_balls_y2'] = 987
        
    def convert(self, x):
        factor = self.base_x / x
        for v in self.value:
            self.value[v] = int(self.value[v] / factor)

'''
A very simple graphical user interface.
'''
class Gui:
    def __init__(self, main):
        self.main = main
        self.root = tk.Tk(className="wag-viewer")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def show(self):
        self.left_score_label = tk.Label(self.root, text = "0", font=("calibre", 50, "bold"), width=4)
        self.left_score_label.grid(row=0)
        self.right_score_label = tk.Label(self.root, text = "0", font=("calibre", 50, "bold"), width=4)
        self.right_score_label.grid(row=0, column=2)
        
        source_label = tk.Label(self.root, text="Source")
        source_label.grid(row=1)
        self.source = ttk.Combobox(self.root, values = ["Monitor", "Virtualcam"], state="readonly", width=10)
        self.source.set("Monitor")
        self.source.bind('<<ComboboxSelected>>', self.source_changed)
        self.source.grid(row=1, column=2)
        
        device_number_var = tk.IntVar()
        device_number_label = tk.Label(self.root, text="Cam Device Number")
        device_number_label.grid(row=2)
        self.device_number = tk.Entry(self.root, textvariable=device_number_var, width=3, state="disabled")
        self.device_number.grid(row=2, column=2)
        
        self.start_button = tk.Button(self.root, text="Start", command=self.start)
        self.start_button.grid(row=3)

        self.pause_button = tk.Button(self.root, text="Pause", command=self.pause)
        self.pause_button.grid(row=3, column=1)

        self.reset_button = tk.Button(self.root, text="Reset", command=self.reset)
        self.reset_button.grid(row=3, column=2)
        
        self.reset()
        
        update_gui_thread = threading.Thread(target=self.update_gui_thread)
        update_gui_thread.start()
        
        self.root.mainloop()
        
    def update_gui_thread(self):
        while True:
            start = time.time()
            self.left_score_label.config(text=self.main.left_team_score)
            self.right_score_label.config(text=self.main.right_team_score)
            try:
                time.sleep(start - time.time() + 0.5)
            except:
                pass
                
    def source_changed(self, event):
        if self.source.get() == "Monitor":
            self.main.use_capture_card = False
            self.device_number.config(state="disabled")
        else:
            self.main.use_capture_card = True
            self.device_number.config(state="normal")
        
    def start(self):
        self.main.device_number = self.device_number.get()
        self.start_button.config(state="disabled")
        self.pause_button.config(state="normal")
        self.reset_button.config(state="normal")
        self.source.config(state="disabled")
        self.device_number.config(state="disabled")
        self.main.start()
            
    def pause(self):
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled")
        self.reset_button.config(state="normal")
        self.main.pause()
            
    def reset(self):
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled")
        self.reset_button.config(state="disabled")
        self.source.config(state="readonly")
        if self.source.get() == "Monitor":
            self.device_number.config(state="disabled")
        else:
            self.device_number.config(state="normal")
        self.main.reset()

    def on_closing(self):
        self.reset()
        self.root.destroy()
        sys.exit()
        
        
'''
Main Class. Contains all the logic.
'''
class Main:
    def __init__(self):
        self.DEBUG = False
        self.border_size = 10
        self.tesseract_confidence = 82
        self.initialize()
        self.update_screensize(1920)
        self.use_capture_card = False
        self.device_number = 0
        
    def initialize(self):
        self.running = False
        
        self.is_last_2_min = False
        self.is_dead = False
        
        self.left_team_score = 0
        self.right_team_score = 0
        self.first_goal = False
        self.left_score_list = [None, None, None, None, None]
        self.right_score_list = [None, None, None, None, None]
        self.ball_list = [0,0,0,0,0]
        
        self.screenshot = None
        
    def update_screensize(self, screensize):
        self.screen_size = screensize
        self.screen = ScreenConverter()
        self.screen.convert(self.screen_size)
        
    def set_is_dead(self, frame):
        try:
            if sum(frame[self.screen.value['dead_y']][self.screen.value['dead_x']]) > 500: # Checks "+" Button at top right for greyscreen
                self.is_dead = False
            else:
                self.is_dead = True
                self.ball_list.append(0)
        except:
            print("Failed to check death")
            
    def set_is_last_2_min(self, frame):
        try:
            if (frame[self.screen.value['last_y']][self.screen.value['last_x']].item(0) > 200
                and frame[self.screen.value['last_y']][self.screen.value['last_x']].item(1) > 200
                and frame[self.screen.value['last_y']][self.screen.value['last_x']].item(2) < 100): # Checks color of timer at top; 200,200,100 for yellow
                self.is_last_2_min = True
            else:
                self.is_last_2_min = False
        except:
            print("Failed to check last 2 minutes timer")
        
    def check_contours(self, frame):
        orig_cnts = cv2.findContours(frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        mask = np.ones(frame.shape[:2], dtype="uint8") * 255
        cnts = []
        for c in orig_cnts:
            x,y,w,h = cv2.boundingRect(c)
            if all([cv2.contourArea(c) >= self.screen.value['contour_area_min'],
                    h <= self.screen.value['contour_height_max'],
                    h >= self.screen.value['contour_height_min'],
                    w <= self.screen.value['contour_width_max'],
                    w >= self.screen.value['contour_width_min'],
                    x > self.border_size * 1.2, x+w < (frame.shape[1] - (self.border_size * 1.2)),
                    y > self.border_size * 1.2, y+h < (frame.shape[0] - (self.border_size * 1.2))]): # only keep contours with good forms and not at border
                cnts.append(c)
            else:
                cv2.drawContours(mask, [c], -1, 0, -1)
        if len(cnts) == 0:
            return None
        i = 0
        for c in cnts:
            i += 1
            x,y,w,h = cv2.boundingRect(c)
            middle_x = x + (w / 2)
            middle_y = y + (h / 2)
            distance_to_middle = math.sqrt(((frame.shape[1]/2) - middle_x)**2 + ((frame.shape[0]/2) - middle_y)**2)
            min_dist = 9999
            max_dist_to_middle = 0
            min_height_diff = 9999
            min_y_diff = 9999
            j = 0
            for c2 in cnts: # Check distance and other relations to all other contours
                j += 1
                if i == j:
                    continue
                x2,y2,w2,h2 = cv2.boundingRect(c2)
                middle_x2 = x2 + (w2 / 2)
                middle_y2 = y2 + (h2 / 2)
                dist = math.sqrt((middle_x - middle_x2)**2 + (middle_y - middle_y2)**2)
                other_distance_to_middle = math.sqrt(((frame.shape[1]/2) - middle_x2)**2 + ((frame.shape[0]/2) - middle_y2)**2)
                if dist < min_dist:
                    min_dist = dist
                if other_distance_to_middle > max_dist_to_middle:
                    max_dist_to_middle = other_distance_to_middle
                if abs(h - h2) < min_height_diff:
                    min_height_diff = abs(h - h2)
                if abs(y - y2) < min_y_diff:
                    min_y_diff = abs(y - y2)
            if min_dist > self.screen.value['contour_diff_dist_max']: # Two contours far from each other: Take the one closer to middle; three or more: take the best group
                if len(cnts) == 2 and distance_to_middle == max_dist_to_middle:
                    cv2.drawContours(mask, [c], -1, 0, -1)
                if len(cnts) > 2: # Problem: If there are 3 single contours all get deleted
                    cv2.drawContours(mask, [c], -1, 0, -1)
            if len(cnts) > 2 and (min_height_diff > self.screen.value['contour_diff_height_max'] or min_y_diff > self.screen.value['contour_diff_y_max']):
                cv2.drawContours(mask, [c], -1, 0, -1)
        frame = cv2.bitwise_and(frame, frame, mask=mask)
        return frame
    
    def prepare_frame_for_text(self, frame, y1, y2, x1, x2, window_name):
        frame_small = frame[(y1-self.border_size):(y2+self.border_size), (x1-self.border_size):(x2+self.border_size)]
        # frame_small = cv2.bilateralFilter(frame_small,9,75,75)
        frame_small = cv2.copyMakeBorder(frame_small, self.border_size, self.border_size, self.border_size, self.border_size, cv2.BORDER_CONSTANT)
        if window_name == "Balls":
            frame_small = cv2.resize(frame_small, (0, 0), fx=1.5, fy=1.5, interpolation=cv2.INTER_AREA)
        space = cv2.COLOR_RGB2HSV # Screenshot is RGB
        if self.use_capture_card:
            space = cv2.COLOR_BGR2HSV
        frame_hsv = cv2.cvtColor(frame_small, space)
        if self.is_dead:
            frame_cleaned = cv2.inRange(frame_hsv, (15,40,120), (40,225,160))
        else:
            frame_cleaned = cv2.inRange(frame_hsv, (15,40,200), (40,225,255))
        frame_cleaned = self.check_contours(frame_cleaned)
        if frame_cleaned is None:
            return None
         
        frame_cleaned = cv2.erode(frame_cleaned, np.ones((2, 2), np.uint8))
        frame_cleaned = cv2.dilate(frame_cleaned, np.ones((2, 2), np.uint8))
            
        frame_final = cv2.bitwise_not(frame_cleaned) # Swap Black/White
        
        ''' # Remove cursive by shearing - doesn't help in practise
        shear_value = 0.18
        M = np.float32([[1, shear_value, 0],
             	[0, 1  , 0],
            	[0, 0  , 1]])  
        y, x = frame_final.shape
        frame_final = cv2.warpPerspective(frame_final,M,(x,y)) # Shear
        frame_final = frame_final[0:y, int(y*shear_value):x]
        
        frame_final = cv2.blur(frame_final, (2,2))
        '''
        
        if self.DEBUG:
            t = time.time()
            cv2.imwrite("DEBUG/" + window_name + str(t) + ".png", frame_final)
            # cv2.imwrite("DEBUG/" + window_name + str(t) + "_c.png", frame_small)
        return frame_final
        
    def get_number_with_confidence(self, tess_dict, conf):
        try:
            for i in range(0, len(tess_dict['text'])):
                if int(tess_dict['conf'][i]) > conf:
                    number = tess_dict['text'][i]
                    conf = int(tess_dict['conf'][i])
            return int(number)
        except:
            return None
        
    def get_score(self, frame, side):
        tess_config = r'--oem 3 --psm 7 -l digits -c tessedit_char_whitelist=0123456789' # psm 7: Treat image as single line
        try:
            tess_dict = pytesseract.image_to_data(frame, config=tess_config, output_type=pytesseract.Output.DICT)
            number = self.get_number_with_confidence(tess_dict, self.tesseract_confidence)
            if self.DEBUG:
                print(str(tess_dict['text']) + str(tess_dict['conf']))
                print(side + " " + str(number))
            if number > 0 and number < 51 or (number > 50 and number < 101 and number % 2 == 0):
                return number
            return None
        except:
            return None
            
    def get_own_balls(self, frame):
        tess_config = r'--oem 3 --psm 6 -l digits -c tessedit_char_whitelist=0123456789' # psm 6 (Uniform block of text) works better here
        try:
            tess_dict = pytesseract.image_to_data(frame, config=tess_config, output_type=pytesseract.Output.DICT)
            number = self.get_number_with_confidence(tess_dict, self.tesseract_confidence)
            if self.DEBUG and number != self.ball_list[-1]:
                print("Balls: " + str(number))
            if number >= 0 and number < 51:
                return number
            return None
        except:
            return None
            
    def check_scored(self, y1, y2, x1, x2, side, score_list):
        small_frame = self.prepare_frame_for_text(self.screenshot, y1, y2, x1, x2, side)
        score = None
        if small_frame is not None:
            score = self.get_score(small_frame, side)
        if(score != None and
            score_list[-4] != score and
            score_list[-3] != score and
            (score_list[-2] != score_list[-1] and # Same number needs to be already found last or second last time
            (score_list[-2] == score or
            score_list[-1] == score))):
                if side == "Left":
                    self.left_team_score += score
                else:
                    self.right_team_score += score
                print (side + " Team scored " + str(score) + " points!")
                print ("Left " + str(self.left_team_score) + " - " + str(self.right_team_score) + " Right")
                self.first_goal = True
        score_list.append(score)
        return score
        
    def left_thread(self): 
        if not self.first_goal:
            self.check_scored(self.screen.value['check_left_first_x1'], self.screen.value['check_left_first_x2'],
                                self.screen.value['check_left_first_y1'], self.screen.value['check_left_first_y2'], "Left", self.left_score_list)
        else:
            self.check_scored(self.screen.value['check_left_x1'], self.screen.value['check_left_x2'],
                                self.screen.value['check_left_y1'], self.screen.value['check_left_y2'], "Left", self.left_score_list)
            
    def right_thread(self):
        if not self.first_goal:
            self.check_scored(self.screen.value['check_right_first_x1'], self.screen.value['check_right_first_x2'],
                                self.screen.value['check_right_first_y1'], self.screen.value['check_right_first_y2'], "Right", self.right_score_list)
        else:
            self.check_scored(self.screen.value['check_right_x1'], self.screen.value['check_right_x2'],
                                self.screen.value['check_right_y1'], self.screen.value['check_right_y2'], "Right", self.right_score_list)
            
    def own_balls_thread(self):
        ball_frame = self.prepare_frame_for_text(self.screenshot, self.screen.value['check_balls_x1'], self.screen.value['check_balls_x2'],
                                                    self.screen.value['check_balls_y1'], self.screen.value['check_balls_y2'], "Balls")
        current_balls = self.get_own_balls(ball_frame)
        if current_balls is None:
            return
        if (self.ball_list[-4] != 0 and
            self.ball_list[-3] != 0 and
            self.ball_list[-2] == 0 and
            self.ball_list[-1] == 0 and
            current_balls == 0): # Needs 0 three times to count score
            score = self.ball_list[-3]
            if self.is_last_2_min:
                score *= 2
            self.left_team_score += score
            self.first_goal = True
            print ("You scored " + str(score) + " points!")
            print ("Left " + str(self.left_team_score) + " - " + str(self.right_team_score) + " Right")
        self.ball_list.append(current_balls)
        
    def start(self):
        self.running = True
        main_thread = threading.Thread(target=self.main_thread)
        main_thread.start()
        
    def pause(self):
        self.running = False
        
    def reset(self):
        self.running = False
        time.sleep(0.5)
        self.initialize() # The main_thread might crash, but it should be fine
        
    def main_thread(self):
        if self.use_capture_card:
            num = 0
            try:
                num = int(self.device_number)
            except:
                pass
            cap = cv2.VideoCapture(num)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            if not cap.isOpened():
                print("ERROR: Cannot open camera " + str(self.device_number))
                return
        while self.running:
            start = time.time()
            screenshot = None
            if self.use_capture_card:
                ret, screenshot = cap.read()
            else:
                screenshot = ImageGrab.grab()
            self.screenshot = np.array(screenshot)
            if (self.screenshot.shape[1] != self.screen_size):
                self.update_screensize(self.screenshot.shape[1])
            self.set_is_dead(self.screenshot)
            self.set_is_last_2_min(self.screenshot)
            t1 = threading.Thread(target=self.left_thread)
            t2 = threading.Thread(target=self.right_thread)
            t3 = threading.Thread(target=self.own_balls_thread)
            t1.start()
            t2.start()
            if not self.is_dead:
                t3.start()
            t1.join()
            t2.join()
            if not self.is_dead:
                t3.join()
            sleeptime = start - time.time() + 0.3
            if sleeptime > 0:
                time.sleep(sleeptime) # Run every 0.3 seconds
                    
    def main(self):
        if not os.path.isfile(pytesseract.pytesseract.tesseract_cmd):
            print("ERROR: Tesseract is missing: " + str(pytesseract.pytesseract.tesseract_cmd))
            sys.exit()
        self.gui = Gui(self)
        self.gui.show()

if __name__ == "__main__":
    main = Main()
    if (len(sys.argv) > 1 and sys.argv[1] == "DEBUG"):
        main.DEBUG = True
    main.main()