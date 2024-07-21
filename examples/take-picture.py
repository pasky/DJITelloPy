import cv2
from djitellopy import Tello

print("tello init...")
tello = Tello()
print("tello connect...")
tello.connect()
print("tello connect OK")

print("tello stream on...")
tello.streamon()
print("tello frame...")
frame_read = tello.get_frame_read()

tello.takeoff()
print("tello frame write...")
cv2.imwrite("picture.png", frame_read.frame)

tello.land()
