from main import Main
import numpy as np
import cv2

main = Main()

expected_left_score_list = [None, None, 30, 100, None, 2, 11, None, 19]
expected_right_score_list = [None, 30, None, None, 100, None, None, 10, None]

for i in range(1,9):
    screenshot = cv2.imread('test/Test' + str(i) + '.png')
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
    frame = np.array(screenshot)
    main.set_is_dead(frame)
    if i < 7:
        small_left_frame = main.prepare_frame_for_text(frame, 110, 160, 830, 930, "Left")
        small_right_frame = main.prepare_frame_for_text(frame, 110, 160, 1065, 1165, "Right")
    else:
        small_left_frame = main.prepare_frame_for_text(frame, 110, 160, 870, 970, "Left")
        small_right_frame = main.prepare_frame_for_text(frame, 110, 160, 1325, 1425, "Right")
    left_score = main.get_score(small_left_frame)
    right_score = main.get_score(small_right_frame)
    if left_score == expected_left_score_list[i] and right_score == expected_right_score_list[i]:
        print("#" + str(i) + " correct")
    else:
        print("#" + str(i) + " wrong. " + str(left_score) + " - " + str(right_score))
