
import cv2
import numpy as np
import os
input_file_path = ["/Users/lucky/Desktop/feature_map/feature_map_enlightenGAN/yolo_layer_output/"]

R = 2.5 # Please Adjust radio according to your screen

# read image
img_list = []
for i in range(27):
    img_list.append(cv2.imread(input_file_path[0] + "52x52_" + str(i) + ".jpg"))

# combine images

img_com_0 = np.concatenate(img_list[0:9], axis=1) # axis = 0 is vertical
img_com_1 = np.concatenate(img_list[9:18], axis=1) # axis = 0 is vertical
img_com_2 = np.concatenate(img_list[18:27], axis=1) # axis = 0 is vertical
# img_com_4 = np.concatenate(img_list[24:32], axis=1) # axis = 0 is vertical
img_com_01 = np.concatenate((img_com_0, img_com_1), axis=0) # axis = 0 is vertical
# img_com_02 = np.concatenate((img_com_3, img_com_4), axis=0) # axis = 0 is vertical
img_com = np.concatenate((img_com_01, img_com_2), axis=0) # axis = 0 is vertical


# Resize image to make it fit your screen
img_com = cv2.resize(img_com,
                        (int(img_com.shape[1]*R), int(img_com.shape[0]*R)),
                        interpolation=cv2.INTER_AREA)

cv2.imshow("Show pair images", img_com)
cv2.imwrite("tmp.jpg", img_com)

# Key Event
key = cv2.waitKey(0) # msec
cv2.destroyAllWindows()