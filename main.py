import cv2
import pytesseract
from PIL import ImageGrab
import numpy as np

class Main:
    def __init__(self):
        pass
        
    def get_score(self, frame, y1, y2, x1, x2, window_name): # TODO: Check colors next to text or something like that
        score = frame[y1:y2, x1:x2]
        score_hsv = cv2.cvtColor(score, cv2.COLOR_RGB2HSV)
        final_score = cv2.inRange(score_hsv, (15,55,120), (40,205,255)) # TODO: Cleaner text (Dilate etc.)
        cv2.imshow(window_name, final_score)
        cv2.waitKey(1)
        tess_config = r'--oem 3 --psm 6 outputbase digits -c tessedit_char_whitelist=0123456789'
        try:
            number = int(pytesseract.image_to_string(final_score, config=tess_config))
            print(str(number))
            if number > 0 and number < 51 or (number > 50 and number < 101 and number % 2 == 0):
                return number
            return None
        except:
            return None

    def main(self):
        left_scored = False
        right_scored = False
        while True:
            try:
                screenshot = ImageGrab.grab() # cv2.imread('test/Test1.png')
                frame = np.array(screenshot)
                left_score = self.get_score(frame, 110, 160, 830, 930, "Left")
                if(left_score != None):
                    if not left_scored:
                        print ("Left Team scored " + str(left_score) + " points!")
                        left_scored = True
                else:
                    left_scored = False
                right_score = self.get_score(frame, 110, 160, 1065, 1165, "Right")
                if(right_score != None):
                    if not right_scored:
                        print ("Right Team scored " + str(right_score) + " points!")
                        right_scored = True
                else:
                    right_scored = False
            except KeyboardInterrupt:
                print("Done")
                break

if __name__ == "__main__":
    main = Main()
    main.main()
