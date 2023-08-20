import cv2
from data.data_manager import DataManager
from .draw_manager import DrawManager


class TrackerManager():
    def __init__(self, get, dm) -> None:
        self.get = get
        self.dd: DataManager = self.get('data')
        self.dm: DrawManager = dm
        self.multitracker = None

        self.is_init = True
        self.is_tracking = False

    def init_object_tracking(self, oldframe, newframe):
        # object tracking이 가능한 상태인 지 확인하는 함수

        bbox = self.get_bbox()
        if bbox and self.is_tracking:
            if self.is_init:
                # object tracking 한 결과 나온 라벨링 그리기
                self.object_tracking(oldframe, newframe, bbox, True)
                self.is_init = False

            else:
                self.object_tracking(oldframe, newframe, bbox)
        else:
            print("bbox error")
            self.stop_tracking()

    def get_tracking_status(self):
        return self.is_tracking

    def get_init_status(self):
        return self.is_init

    def start_tracking(self):
        self.is_tracking = True
        self.is_init = True

    def stop_tracking(self):
        self.is_tracking = False
        self.is_init = True

    def get_bbox(self):
        """
        object tracking이 가능한 상태인 지 확인하고, bbox를 반환합니다.

        Returns:
            bbox (list, empty = False): object tracking이 가능한 상태면 bbox 좌표를 반환하고, 아니면 False를 반환합니다.
        """
        fn = self.dd.get_frame_number()
        next_label_list = self.dd.frame_label_check(fn)
        bbox = []
        # print(label_list, next_label_list, self.annotation)
        for annotation in self.dm.get_current_rectangle_annotation_info():
            label, ((x, y), w, h), color = annotation
            if label in next_label_list:
                self.dd.delete_label(label, fn)
            x, y, w, h = map(int, [x, y, w, h])
            bbox.append((label, [x, y, w, h], color))
            print("현재 프레임의 bbox들 좌표:", bbox)

        return bbox

    def object_tracking(self, oldframe, newframe, bbox, init=False):
        """ 주어진 frame이미지에 tracking한 물체에 bbox를 그리고 정보를 저장합니다.

        Args:
            frame (ndarray): frame이미지
            bbox (List): bounding box의 좌표 리스트 [(라벨명, (좌표), 컬러)]
            init (bool, optional): True일때, tracker를 생성합니다. Defaults to False.
        """

        if init:
            print("multitracker 초기화")
            self.multitracker = cv2.legacy.MultiTracker_create()
            # ok = self.tracker[label].init(frame, label_bbox)
            for label_bbox in bbox:
                tracker = cv2.legacy.TrackerCSRT_create()
                self.multitracker.add(tracker, oldframe, label_bbox[1])

        ok, new_bboxes = self.multitracker.update(newframe)

        if ok:
            # print(new_bboxes)
            log_path = self.dd.check_log_path()
            with open(f"{log_path}/bbox_log.txt", "a") as log_file:
                for i, new_bbox in enumerate(new_bboxes):
                    # 새로운 라벨 저장을 위해 필요한 데이터들
                    bbox_ = self.refine_bbox(new_bbox, self.dd.get_mp4_info())
                    if not self.is_roi_within_bounds(new_bbox, bbox_):
                        print(f"{bbox[i][0]} box가 화면 벗어남")
                        self.start_tracking()
                        self.dm.pop_annotation(bbox[i][0])
                        continue
                    if self.compare_image(oldframe, newframe, bbox[i][1], bbox_, 0.6, 50):
                        # print(self.dd.frame_label_check(self.dd.frame_number - 1))
                        color = bbox[i][2]
                        label = bbox[i][0]
                        log_file.write(
                            f"Frame: {self.dd.get_frame_number()}, Label: {label}, Bbox: {new_bbox}\n")
                        print(f"new_bbox : {bbox_}, {color}, {label}")
                        # 라벨 그리기 및 저장
                        self.dm.draw_rectangle(
                            label, bbox_, color, isSelect=True)
                        self.dd.add_label('rectangle', label, bbox_, color,
                                          frame_number=self.dd.get_frame_number())
                    else:
                        print("유사도 떨어짐 감지")
                        self.start_tracking()
                        self.dm.pop_annotation(bbox[i][0])
        else:
            self.stop_tracking()
            print("object tracking failed")

    def compare_image(self, oldframe, newframe, oldbox, newbox, similarity_threshold, coords_threshold):
        # print(f"old : {oldbox}, new: {newbox}")
        # print(np.array_equal(oldframe, newframe))
        roi1 = oldframe[oldbox[1]:oldbox[1] +
                        oldbox[3], oldbox[0]:oldbox[0] + oldbox[2]]
        roi2 = newframe[newbox[0][1]:newbox[0][1] +
                        newbox[2], newbox[0][0]:newbox[0][0] + newbox[1]]

        if abs(oldbox[0] - newbox[0][0]) > coords_threshold or abs(oldbox[1] - newbox[0][1]) > coords_threshold:
            similarity = self.similarity_score('hsv', roi1, roi2)

            if similarity <= similarity_threshold:
                print("label이 튀고 유사도가 낮음", similarity)
                return False
            else:
                print("label 튀었지만 유사도 높음", similarity)
                return True
        else:
            return True

    def similarity_score(self, mode, previous_roi, current_roi):
        if mode == 'hsv':
            previous_hsv = cv2.cvtColor(previous_roi, cv2.COLOR_BGR2HSV)
            current_hsv = cv2.cvtColor(current_roi, cv2.COLOR_BGR2HSV)

            # histogram
            previous_hist = cv2.calcHist(
                [previous_hsv], [0], None, [256], [0, 256])
            current_hist = cv2.calcHist(
                [current_hsv], [0], None, [256], [0, 256])

            # normalize
            previous_hist = previous_hist / previous_hist.sum()
            current_hist = current_hist / current_hist.sum()

            # comapre histogram
            score = cv2.compareHist(
                previous_hist, current_hist, cv2.HISTCMP_BHATTACHARYYA)
            print('similarity score:', 1 - score)

            return 1 - score

    def is_roi_within_bounds(self, bbox, refined_bbox, max_ratio=0.8):
        roi_width = bbox[2]
        roi_height = bbox[3]

        refined_roi_width = refined_bbox[1]
        refined_roi_height = refined_bbox[2]

        roi_area = roi_width * roi_height
        refined_roi_area = refined_roi_width * refined_roi_height
        roi_ratio = refined_roi_area / roi_area

        return roi_ratio >= max_ratio

    def refine_bbox(self, bbox, frame_info):
        x = max(int(bbox[0]), 0)
        y = max(int(bbox[1]), 0)
        w = min(int(bbox[2]), frame_info[0] - x)
        h = min(int(bbox[3]), frame_info[1] - y)

        print('refined bbox coords:', ((x, y), w, h))

        return ((x, y), w, h)
