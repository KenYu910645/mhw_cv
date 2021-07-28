import cv2 

img = cv2.imread("eleven.png" ,cv2.IMREAD_UNCHANGED)
ret, out = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
print(out)
cv2.imwrite("eleven.png", out)