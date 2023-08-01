# import cv2
# import sys
# # import os
# # print(os.getcwd())
# tracker = cv2.TrackerGOTURN_create()

# video = cv2.VideoCapture("../../sample/street.mp4")

# if not video.isOpened():
#     print("Could not open video.")
#     sys.exit()

# ok, frame = video.read()
# # print(type(frame))
# if not ok:
#     print("Cannot read video file.")
#     sys.exit()

# x, y = map(int, [644.9351366706646, 191.70674199861128])
# width, height = map(int, [84.66870778359953, 195.47168739347256])
# # print(x, y, width, height)
# bbox = (x, y, width, height)

# ok = tracker.init(frame, bbox)

# while True:
#     ok, frame = video.read()
#     if not ok:
#         break

#     timer = cv2.getTickCount()

#     ok, bbox = tracker.update(frame)

#     fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer)

#     if ok:
#         p1 = (int(bbox[0]), int(bbox[1]))
#         p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
#         cv2.rectangle(frame, p1, p2, (255, 0 , 0), 2, 1)
#     else:
#         cv2.putText(frame, "Tracking failure detected", (100, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255),2)
    
#     cv2.putText(frame, "GOTURN tracker", (100, 20), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (50, 170, 120), 2)
#     cv2.putText(frame, "FPS : " + str(int(fps)), (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50, 170, 50), 2)

#     cv2.imshow("Tracking", frame)

#     k = cv2.waitKey(1) & 0xff
#     if k == 27:
#         break