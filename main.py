import cv2
import pytesseract
from PIL import ImageGrab
import numpy as np

'''
Only working for 1920x1080 screens for now!
'''
class Main:
    def __init__(self):
        self.is_dead = False
        self.disable_double_check = False # Set to on for slower computers (One iteration > 0.5 seconds), less accurate.
        self.left_team_score = 0
        self.right_team_score = 0
        
    def set_is_dead(self, frame):
        if sum(frame[52][1818]) > 500: # Check "+" Button at top right for greyscreen
            self.is_dead = False
        else:
            self.is_dead = True
        
    def __check_contours(self, frame):
        cnts = cv2.findContours(frame, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[0]
        mask = np.ones(frame.shape[:2], dtype="uint8") * 255
        for c in cnts:
            x,y,w,h = cv2.boundingRect(c)
            if cv2.contourArea(c) < 120 or h > 70 or h < 25 or w > 50 or w < 5: # contours with unusual forms get deleted
                cv2.drawContours(mask, [c], -1, 0, -1)
        frame = cv2.bitwise_and(frame, frame, mask=mask)
        return frame
    
    def prepare_frame_for_text(self, frame, y1, y2, x1, x2, window_name):
        border_size = 10
        frame_small = frame[y1-border_size:y2+border_size, x1-border_size:x2+border_size]
        frame_small = cv2.copyMakeBorder(frame_small, border_size, border_size, border_size, border_size, cv2.BORDER_CONSTANT)
        frame_hsv = cv2.cvtColor(frame_small, cv2.COLOR_RGB2HSV) # Screenshot is RGB
        if self.is_dead:
            frame_cleaned = cv2.inRange(frame_hsv, (15,55,120), (40,205,150))
        else:
            frame_cleaned = cv2.inRange(frame_hsv, (15,55,200), (40,205,255))
        frame_cleaned = self.__check_contours(frame_cleaned)
        frame_cleaned = cv2.dilate(frame_cleaned, np.ones((2, 2), np.uint8))
        frame_cleaned = cv2.erode(frame_cleaned, np.ones((2, 2), np.uint8))
        frame_final = cv2.bitwise_not(frame_cleaned) # Swap Black/White
        cv2.imshow(window_name, frame_cleaned)
        cv2.waitKey(1)
        return frame_final
        
    def get_score(self, frame):
        tess_config = r'--oem 3 --psm 7 outputbase digits -c tessedit_char_whitelist=0123456789' # psm 7: Treat image as single line
        try:
            number = int(pytesseract.image_to_string(frame, config=tess_config))
            print(str(number))
            if number > 0 and number < 51 or (number > 50 and number < 101 and number % 2 == 0):
                return number
            return None
        except:
            return None
            
    def get_own_balls(self, frame):
        tess_config = r'--oem 3 --psm 7 outputbase digits -c tessedit_char_whitelist=0123456789'
        try:
            number = int(pytesseract.image_to_string(frame, config=tess_config))
            print("Balls: " + str(number))
            if number >= 0 and number < 51:
                return number
            return None
        except:
            return None
            
    def check_scored(self, frame, y1, y2, x1, x2, side, last_score): # Needs to display the same number for 2 frames in a row
        small_frame = self.prepare_frame_for_text(frame, y1, y2, x1, x2, side)
        score = self.get_score(small_frame)
        if(score != None):
            if last_score == score or self.disable_double_check:
                if side == "Left":
                    self.left_team_score += score
                else:
                    self.right_team_score += score
                print (side + " Team scored " + str(score) + " points!")
                print ("Left " + str(self.left_team_score) + " - " + str(self.right_team_score) + " Right")
                last_score = -1
            if last_score == 0:
                last_score = score
        else:
            last_score = 0
        return last_score

    def main(self):
        first_goal = False
        last_left_score = 0
        last_right_score = 0
        while True:
            try:
                screenshot = ImageGrab.grab()
                frame = np.array(screenshot)
                self.set_is_dead(frame)
                if not first_goal:
                    last_left_score = self.check_scored(frame, 110, 190, 870, 970, "Left", last_left_score)
                    last_right_score = self.check_scored(frame, 110, 190, 1325, 1425, "Right", last_right_score)
                else:
                    last_left_score = self.check_scored(frame, 110, 160, 780, 930, "Left", last_left_score)
                    last_right_score = self.check_scored(frame, 110, 160, 1065, 1210, "Right", last_right_score)
                if last_left_score == -1 or last_right_score == -1:
                    first_goal = True
                # ball_frame = self.prepare_frame_for_text(frame, 780, 822, 930, 990, "Balls")
                # own_balls = self.get_own_balls(ball_frame) # TODO: Was mit machen
            except KeyboardInterrupt:
                print("Done")
                break

if __name__ == "__main__":
    main = Main()
    main.main()
