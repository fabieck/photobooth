
import cv2
import numpy as np

file_name = "video location here"
window_name = "window"
interframe_wait_ms = 30

cap = cv2.VideoCapture('/Users/fabianeckert/Downloads/IMG_9252.MOV')
if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

while (True):
    ret, frame = cap.read()
    if not ret:
        print("Reached end of video, exiting.")
        break
    cv2.moveWindow(window_name, 0, 0)  # Move it to (40,30)
    #cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    #cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    #cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)

    frame = cv2.resize(frame, (1280, 800), interpolation=cv2.INTER_CUBIC)
    #frame = cv2.rotate(frame, rotateCode=cv2.ROTATE_90_CLOCKWISE)
    #frame = cv2.flip(frame, flipCode=1)
    #cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    #cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow(window_name, frame)
    if cv2.waitKey(interframe_wait_ms) & 0x7F == ord('q'):
        print("Exit requested.")
        break

cap.release()
cv2.destroyAllWindows()