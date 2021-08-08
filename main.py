import cv2
import pytesseract
from PIL import ImageGrab
import numpy as np
import threading
import time
import math

'''
Only working for 1920x1080 screens for now!
'''
class Main:
    def __init__(self):
        self.is_dead = False
        self.left_team_score = 0
        self.right_team_score = 0
        self.first_goal = False
        self.last_left_score = 0
        self.last_right_score = 0
        self.screenshot = None
        self.border_size = 10
        self.balls = 0
        
        self.DEBUG = True
        self.disable_double_check = False # Set to on for slower computers (One iteration > 0.5 seconds), less accurate.
        
    def set_is_dead(self, frame):
        if sum(frame[52][1818]) > 500: # Checks "+" Button at top right for greyscreen
            self.is_dead = False
        else:
            self.is_dead = True
            self.balls = 0
        
    def check_contours(self, frame):
        orig_cnts = cv2.findContours(frame, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[0]
        mask = np.ones(frame.shape[:2], dtype="uint8") * 255
        cnts = []
        for c in orig_cnts:
            x,y,w,h = cv2.boundingRect(c)
            if all([cv2.contourArea(c) >= 120, h <= 60, h >= 25, w <= 45, w >= 5,
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
            if min_dist > 45: # Two contours: Take the one closer to middle; three or more: take the best group
                if len(cnts) == 2 and distance_to_middle == max_dist_to_middle:
                    cv2.drawContours(mask, [c], -1, 0, -1)
                if len(cnts) > 2: # Problem: What if there are 3 single contours where only 1 is correct?
                    cv2.drawContours(mask, [c], -1, 0, -1)
            if len(cnts) > 2 and (min_height_diff > 5 or min_y_diff > 5):
                cv2.drawContours(mask, [c], -1, 0, -1)
        frame = cv2.bitwise_and(frame, frame, mask=mask)
        return frame
    
    def prepare_frame_for_text(self, frame, y1, y2, x1, x2, window_name):
        frame_small = frame[(y1-self.border_size):(y2+self.border_size), (x1-self.border_size):(x2+self.border_size)]
        frame_small = cv2.copyMakeBorder(frame_small, self.border_size, self.border_size, self.border_size, self.border_size, cv2.BORDER_CONSTANT)
        if window_name == "Balls":
            frame_small = cv2.resize(frame_small, (0, 0), fx=1.5, fy=1.5, interpolation=cv2.INTER_AREA)
        frame_hsv = cv2.cvtColor(frame_small, cv2.COLOR_RGB2HSV) # Screenshot is RGB
        if self.is_dead:
            frame_cleaned = cv2.inRange(frame_hsv, (15,55,120), (40,205,150))
        else:
            frame_cleaned = cv2.inRange(frame_hsv, (15,55,200), (40,205,255))
        frame_cleaned = cv2.dilate(frame_cleaned, np.ones((2, 2), np.uint8))
        frame_cleaned = cv2.erode(frame_cleaned, np.ones((2, 2), np.uint8))
        frame_cleaned = self.check_contours(frame_cleaned)
        if frame_cleaned is None:
            return None
        frame_final = cv2.bitwise_not(frame_cleaned) # Swap Black/White
        frame_final = cv2.resize(frame_final, (0, 0), fx=1.5, fy=1.5, interpolation=cv2.INTER_AREA) # Maybe bad?
        
        shear_value = 0.18
        M = np.float32([[1, shear_value, 0],
             	[0, 1  , 0],
            	[0, 0  , 1]])  
        y, x = frame_final.shape
        frame_final = cv2.warpPerspective(frame_final,M,(x,y)) # Shear
        frame_final = frame_final[0:y, int(y*shear_value):x]
        
        if self.DEBUG:
            t = time.time()
            cv2.imwrite("DEBUG/" + window_name + str(t) + ".png", frame_final)
            # cv2.imwrite("DEBUG/" + window_name + str(t) + "_c.png", frame)
        return frame_final
        
    def get_score(self, frame, side):
        tess_config = r'--oem 3 --psm 7 outputbase digits -c tessedit_char_whitelist=0123456789' # psm 7: Treat image as single line
        try:
            number = int(pytesseract.image_to_string(frame, config=tess_config))
            if self.DEBUG:
                print(side + " " + str(number))
            if number > 0 and number < 51 or (number > 50 and number < 101 and number % 2 == 0):
                return number
            return None
        except:
            return None
            
    def get_own_balls(self, frame):
        tess_config = r'--oem 3 --psm 6 outputbase digits -c tessedit_char_whitelist=0123456789' # psm 6 (Uniform block of text) works better here
        try:
            number = int(pytesseract.image_to_string(frame, config=tess_config))
            if self.DEBUG:
                print("Balls: " + str(number))
            if number >= 0 and number < 51:
                return number
            return None
        except:
            return None
            
    def check_scored(self, y1, y2, x1, x2, side, last_score): # Needs to display the same number for 2 frames in a row
        small_frame = self.prepare_frame_for_text(self.screenshot, y1, y2, x1, x2, side)
        score = None
        if small_frame is not None:
            score = self.get_score(small_frame, side)
        if(score != None):
            if last_score == score or self.disable_double_check:
                if side == "Left":
                    self.left_team_score += score
                else:
                    self.right_team_score += score
                print (side + " Team scored " + str(score) + " points!")
                print ("Left " + str(self.left_team_score) + " - " + str(self.right_team_score) + " Right")
                last_score = -1
            else:
                last_score = score
        else:
            last_score = 0
        return last_score
        
    def left_thread(self):
        if not self.first_goal:
            self.last_left_score = self.check_scored(110, 190, 870, 970, "Left", self.last_left_score)
        else:
            self.last_left_score = self.check_scored(110, 160, 780, 930, "Left", self.last_left_score)
        if self.last_left_score == -1:
            self.first_goal = True
            
    def right_thread(self):
        if not self.first_goal:
            self.last_right_score = self.check_scored(110, 190, 1325, 1425, "Right", self.last_right_score)
        else:
            self.last_right_score = self.check_scored(110, 160, 1065, 1210, "Right", self.last_right_score)
        if self.last_right_score == -1:
            self.first_goal = True
            
    def own_balls_thread(self):
        ball_frame = self.prepare_frame_for_text(self.screenshot, 775, 825, 933, 987, "Balls")
        current_balls = self.get_own_balls(ball_frame)
        if current_balls is None:
            return
        if self.balls > 0 and current_balls == 0:
            self.left_team_score += self.balls
            self.first_goal = True
            print ("You scored " + str(self.balls) + " points!")
            print ("Left " + str(self.left_team_score) + " - " + str(self.right_team_score) + " Right")
        self.balls = current_balls

    def main(self):
        while True:
            try:
                start = time.time()
                screenshot = ImageGrab.grab()
                self.screenshot = np.array(screenshot)
                self.set_is_dead(self.screenshot)
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
            except KeyboardInterrupt:
                print("Done")
                break

if __name__ == "__main__":
    main = Main()
    main.main()
