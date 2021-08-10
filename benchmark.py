from main import Main
import numpy as np
import cv2
import pytesseract

main = Main()

overall_conf = 0
num_of_numbers = 0
min_conf = 100
def get_number_with_confidence(tess_dict, conf):
    number = ''
    global overall_conf
    global num_of_numbers
    global min_conf
    try:
        for i in range(0, len(tess_dict['text'])):
            if int(tess_dict['conf'][i]) > conf:
                number += tess_dict['text'][i]
                overall_conf += tess_dict['conf'][i]
                num_of_numbers += 1
                if tess_dict['conf'][i] < min_conf:
                    min_conf = tess_dict['conf'][i]
        return int(number)
    except:
        pass
    return None
    
def get_frame(first_goal):
    screenshot = cv2.imread('test/Test' + first_goal + str(i) + '.png')
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
    frame = np.array(screenshot)
    return frame
    
def check_score(small_left_frame, small_right_frame, expected_left_score_list, expected_right_score_list, i):
    tess_config = r'--oem 3 --psm 7 -l digits -c tessedit_char_whitelist=0123456789'
    left_score = None
    right_score = None
    if small_left_frame is not None:
        tess_dict_left = pytesseract.image_to_data(small_left_frame, config=tess_config, output_type=pytesseract.Output.DICT)
        left_score = get_number_with_confidence(tess_dict_left, 82)
    if small_right_frame is not None:
        tess_dict_right = pytesseract.image_to_data(small_right_frame, config=tess_config, output_type=pytesseract.Output.DICT)
        right_score = get_number_with_confidence(tess_dict_right, 82)
    if left_score == expected_left_score_list[i] and right_score == expected_right_score_list[i]:
        print("#" + str(i) + " correct")
    else:
        print("#" + str(i) + " wrong. " + str(left_score) + " - " + str(right_score))
          

expected_left_score_list = [None, None, 30, 100, None, 2, 11, 4, 32, 35, 40,
                            None, None, None, 100, 15, 30, None, 31, 29, 22,
                            None, None, 11, 11, 23, None, None, None, 28, None,
                            1, None, None, None, 35]
expected_right_score_list = [None, 30, None, None, 100, None, None, None, None, None, None,
                            100, 100, 100, None, None, None, 30, None, None, None,
                            17, 17, None, None, None, 86, 29, 18, None, 14,
                            None, 10, 10, 23, None]

for i in range(1,36):
    frame = get_frame('')
    main.set_is_dead(frame)
    small_left_frame = main.prepare_frame_for_text(frame, 110, 160, 780, 930, "Left")
    small_right_frame = main.prepare_frame_for_text(frame, 110, 160, 1065, 1210, "Right")
    check_score(small_left_frame, small_right_frame, expected_left_score_list, expected_right_score_list, i)

expected_left_score_list = [None, None, 19, 30, 30, None, 18]
expected_right_score_list = [None, 10, None, None, None, 11, None]
        
for i in range(1,7):
    frame = get_frame('f')
    main.set_is_dead(frame)
    small_left_frame = main.prepare_frame_for_text(frame, 110, 190, 870, 970, "Left")
    small_right_frame = main.prepare_frame_for_text(frame, 110, 190, 1325, 1425, "Right")
    check_score(small_left_frame, small_right_frame, expected_left_score_list, expected_right_score_list, i)
        
print("Average confidence: " + str(overall_conf/num_of_numbers))
print("Min confidence: " + str(min_conf))