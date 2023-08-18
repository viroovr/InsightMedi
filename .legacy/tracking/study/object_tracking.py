import cv2

def similarity_score(mode, previous_roi, current_roi):
    if mode == 'hsv':
        hsv_previous_roi = cv2.cvtColor(previous_roi, cv2.COLOR_BGR2HSV)
        hsv_current_roi = cv2.cvtColor(current_roi, cv2.COLOR_BGR2HSV)

        # 히스토그램 계산
        hist_previous = cv2.calcHist([hsv_previous_roi], [0], None, [256], [0,256])
        hist_current = cv2.calcHist([hsv_current_roi], [0], None, [256], [0,256])

        # 히스토그램 정규화
        hist_previous = hist_previous / hist_previous.sum()
        hist_current = hist_current / hist_current.sum()
        

        # 히스토 그램 유사도 비교 (Bhattacharyya 거리 사용)
        similarity = cv2.compareHist(hist_previous, hist_current, cv2.HISTCMP_BHATTACHARYYA)
        print('similarity:', 1 - similarity)

        return 1 - similarity

THRESHOLD = 0.8

# print(dir(cv2))
#tracker = cv2.TrackerKCF_create()
tracker = cv2.TrackerCSRT_create()
#tracker = cv2.TrackerGOTURN_create()
is_tracking = True

video = cv2.VideoCapture("sample\street.mp4")   # 영상 불러오기

ok, frame = video.read()   # ok: opencv에서 영상을 읽을 수 있는 지 / frame: 영상의 frame

bbox = cv2.selectROI(frame)   # 첫 번쨰 frame의 정보만 저장하고 있음
#print(bbox)   # bounding box 위치

ok = tracker.init(frame, bbox)    # frame의 bounding box tracking 시작
#print(ok)

while True:
    x, y, w, h = [int(i) for i in bbox]
    roi_img = frame[y : y+h, x: x+w]
    ok, frame = video.read()

    if not ok:
        break
    
    if is_tracking:
    # frame update하기 (bbox에 있는 frame은 첫 번째 frame으로 고정되어 있음
        ok, bbox = tracker.update(frame)
        x, y, w, h = [int(i) for i in bbox]
        new_roi_image = frame[y: y+h, x : x+w]
        #print(bbox)
        #print(ok)
        if similarity_score('hsv', roi_img, new_roi_image) >= THRESHOLD:
            if ok:
                (x, y, w, h) = [int(v) for v in bbox]
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2, 1)   # 두께: 2, 윤곽선: 1
            else:
                cv2.putText(frame, 'Error', (100,80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255))
        else:
            cv2.putText(frame, 'TRACKING FALSE', (100,80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255))
            print("벗어남!!!!")
            is_tracking = False
    else:
        cv2.putText(frame, 'traking stopped', (100, 80), cv2.FONT_HERSHEY_COMPLEX, 1, (0,0,255))
        cv2.waitKey(33)

    cv2.imshow("Tracking", frame)

    if cv2.waitKey(1) & 0XFF == 27:   # ESC 누르면 창 닫힘
        break