from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas

from data.data_manager import DataManager
from .draw_manager import DrawManager
# from gui.test_gui import Gui as gu


class Controller():
    def __init__(self, get) -> None:
        self.get = get

        self.tracker = {}
        self.is_tracking = False
        self.toggle = False

    def init_instance_member(self):
        self.dd: DataManager = self.get('data')
        self.gui = self.get('gui')
        self.canvas: FigureCanvas = self.gui.canvas
        self.dm = DrawManager(self.canvas, self.get)

    # init functions
    def init_draw_mode(self, mode, label):
        print(f"Drawing mode : {mode}, label : {label}")
        self.dm.init_draw_mode(mode, label)

    def init_selector(self, mode):
        self.dm.init_selector(mode)

    def delete_label(self, label_name):
        """ contorls -> Viewer_GUI -> dcm_data순으로 버튼을 비활성화하고 데이터를 지웁니다."""
        # 모든 frame에 label_name 이름을 가진 label의 개수
        count = self.dd.label_count(label_name)

        # GUI에서 모든 프레임에 라벨이 1개만 존재하면 버튼 비활성화
        if count == 1:
            self.gui.disable_label_button(label_name)

        # data에서 현재 frame의 해당 라벨이름 정보 제거하기
        self.dd.delete_label(label_name)

    def update_frame(self):
        ret, frame_number, prev_frame, frame = self.dd.update_frame()
        if ret:
            self.frame_show(frame, clear=True)
            # frame에 라벨이 존재하면 라벨을 보여줍니다.
            # if self.is_tracking:
            #     self.cl.init_object_tracking(prev_frame, frame)
            if self.dd.frame_label_check(frame_number):
                self.label_clicked(frame_number)
        return ret, frame_number

    def select_off_all(self):
        self.dm.select_off_all()

    def remove_annotation(self):
        self.dm.remove_annotation()

    def erase_annotation(self, _label_name):
        self.dm.erase_annotation(_label_name)

    def erase_all_annotation(self):
        """현재 self.ax에 있는 모든 patch들과 선들을 제거합니다."""
        self.dm.erase_all_annotation()

    def label_clicked(self, frame_number, _label_name=[]):
        """
        go버튼 클릭 시 모든 annotation을 지우고 해당 frame으로 이동한 뒤 캔버스에 plot을 그려줍니다.

        Args:
            _label_name(string or empty list): 해당 라벨의 두께를 두껍게 합니다.
                                        empty list일 경우, self.annotation 라벨들의 강조를 유지합니다.
        """
        self.dm.go_to_frame(frame_number, _label_name)

    def label_button_clicked(self, label_name):
        if self.dd.is_label_exist(label_name):
            self.delete_label(label_name)
        return True

    def init_figure(self):
        self.dm.init_figure()

    def frame_show(self, frame, cmap='viridis', clear=False):
        """
        img를 보여줍니다.

        Args:
            frame (ndarray): self.ax에 보여줄 이미지 입니다.
            cmap (cmap): 이미지의 color map을 설정합니다.
            clear (bool): self.ax를 clear하고 이미지를 보여줍니다.
        """
        self.dm.frame_show(frame, cmap, clear)

    # def init_object_tracking(self, oldframe, newframe):
    #     bbox = self.check_bbox()   # object tracking이 가능한 상태인 지 확인하는 함수
    #     if bbox:
    #         # print(np.array_equal(self.dd.image, frame))
    #         # self.gui.slider.setValue(
    #         #     self.dd.frame_number + 1)   # 다음 frame으로 업데이트
    #         # print(np.array_equal(self.dd.image, frame))
    #         if not self.is_tracking:
    #             # object tracking 한 결과 나온 라벨링 그리기
    #             self.object_tracking(oldframe, newframe, bbox, init=True)
    #             self.is_tracking = True
    #         else:
    #             # object tracking 한 결과 나온 라벨링 그리기
    #             self.object_tracking(oldframe, newframe, bbox)
    #     else:
    #         print("No bbox")

    # def check_bbox(self):
    #     """
    #     object tracking이 가능한 상태인 지 확인하고, bbox를 반환합니다.

    #     Returns:
    #         bbox (list, empty = False): object tracking이 가능한 상태면 bbox 좌표를 반환하고, 아니면 False를 반환합니다.
    #     """
    #     fn = self.dd.frame_number
    #     label_list = self.dd.frame_label_check(fn - 1)
    #     next_label_list = self.dd.frame_label_check(fn)
    #     bbox = []
    #     print(label_list, next_label_list, self.annotation)
    #     if self.dd.file_mode == 'mp4' and label_list and self.annotation:
    #         for annotation in self.annotation:
    #             label = annotation.get_label()
    #             if label not in next_label_list:
    #                 coord_list = self.dd.frame_label_dict[fn -
    #                                                       1]['rectangle'][label]['coords']
    #                 color = self.dd.frame_label_dict[fn -
    #                                                  1]['rectangle'][label]['color']
    #                 x = coord_list[0][0]
    #                 y = coord_list[0][1]
    #                 w = coord_list[1]
    #                 h = coord_list[2]
    #                 bbox.append(
    #                     (label, [int(x), int(y), int(w), int(h)], color))
    #                 # print(f"{label}의 bbox:", bbox)
    #         print("현재 프레임의 bbox들 좌표:", bbox)
    #     else:
    #         self.stop_playing()
    #         print("bbox error")
    #     return bbox

    # def stop_playing(self):
    #     self.gui.is_tracking = False
    #     self.gui.playButtonClicked()

    # def object_tracking(self, oldframe, newframe, bbox, init=False):
    #     """ 주어진 frame이미지에 tracking한 물체에 bbox를 그리고 정보를 저장합니다.

    #     Args:
    #         frame (ndarray): frame이미지
    #         bbox (List): bounding box의 좌표 리스트
    #         init (bool, optional): True일때, tracker를 생성합니다. Defaults to False.
    #     """

    #     if init:
    #         print(f"multitracker 초기화")
    #         self.multitracker = cv2.legacy.MultiTracker_create()
    #         # ok = self.tracker[label].init(frame, label_bbox)
    #         for label_bbox in bbox:
    #             tracker = cv2.legacy.TrackerCSRT_create()
    #             self.multitracker.add(tracker, oldframe, label_bbox[1])

    #     ok, new_bboxes = self.multitracker.update(newframe)

    #     if ok:
    #         # print(f"기존 bbox {bbox}" )
    #         # print(f"object tracking한 bbox {new_bboxes}")
    #         # print(f"선택된 annotation {self.annotation}")
    #         for i, new_bbox in enumerate(new_bboxes):
    #             # 새로운 라벨 저장을 위해 필요한 데이터들
    #             # bbox_ = ((new_bbox[0], new_bbox[1]), new_bbox[2], new_bbox[3])
    #             bbox_ = ((int(new_bbox[0]), int(new_bbox[1])), int(
    #                 new_bbox[2]), int(new_bbox[3]))
    #             if not self.is_roi_within_bounds(bbox_, self.dd.frame_width, self.dd.frame_height):
    #                 print("화면 벗어남")
    #                 self.stop_playing()
    #                 return
    #             if self.compare_image(oldframe, newframe, bbox[i][1], bbox_, 0.7):
    #                 # print(self.dd.frame_label_check(self.dd.frame_number - 1))
    #                 # label = self.annotation[0].get_label()
    #                 color = bbox[i][2]
    #                 label = bbox[i][0]
    #                 print(*bbox_, color, label)
    #                 # 라벨 그리기 및 저장
    #                 self.pop_annotation(label)
    #                 new_annotation = self.ax.add_patch(
    #                     Rectangle(*bbox_,
    #                               fill=False, picker=True, label=label, edgecolor=color))
    #                 self.select_current_edge(new_annotation)
    #                 # print("현재 선택된 label들:", self.annotation)
    #                 self.dd.add_label('rectangle', label, bbox_, color,
    #                                   frame_number=self.dd.frame_number)
    #                 # print(self.dd.frame_label_dict)
    #             else:
    #                 self.stop_playing()
    #                 print("유사도 떨어짐 감지")
    #     else:
    #         self.stop_playing()
    #         print("object tracking failed")

    # def compare_image(self, oldframe, newframe, oldbox, newbox, similarity_threshold):
    #     print(f"old : {oldbox}, new: {newbox}")
    #     # print(np.array_equal(oldframe, newframe))
    #     roi1 = oldframe[oldbox[1]:oldbox[1] +
    #                     oldbox[3], oldbox[0]:oldbox[0]+oldbox[2]]
    #     roi2 = newframe[newbox[0][1]:newbox[0][1] +
    #                     newbox[2], newbox[0][0]:newbox[0][0]+newbox[1]]
    #     similarity = self.similarity_score('hsv', roi1, roi2)

    #     if similarity <= similarity_threshold:
    #         return False
    #     else:
    #         return True

    # def similarity_score(self, mode, previous_roi, current_roi):
    #     if mode == 'hsv':
    #         previous_hsv = cv2.cvtColor(previous_roi, cv2.COLOR_BGR2HSV)
    #         current_hsv = cv2.cvtColor(current_roi, cv2.COLOR_BGR2HSV)

    #         # histogram
    #         previous_hist = cv2.calcHist(
    #             [previous_hsv], [0], None, [256], [0, 256])
    #         current_hist = cv2.calcHist(
    #             [current_hsv], [0], None, [256], [0, 256])

    #         # normalize
    #         previous_hist = previous_hist / previous_hist.sum()
    #         current_hist = current_hist / current_hist.sum()

    #         # comapre histogram
    #         score = cv2.compareHist(
    #             previous_hist, current_hist, cv2.HISTCMP_BHATTACHARYYA)
    #         print('similarity score:', 1 - score)

    #         return 1 - score

    # def is_roi_within_bounds(self, bbox, screen_width, screen_height, max_ratio=0.8):
    #     roi_x = bbox[0][0]
    #     roi_y = bbox[0][1]
    #     roi_width = bbox[1]
    #     roi_height = bbox[2]
    #     roi_right = roi_x + roi_width
    #     roi_bottom = roi_y + roi_height
    #     # print(bbox)
    #     # print(roi_right, roi_bottom)

    #     if roi_x < 0 or roi_y < 0 or roi_right > screen_width or roi_bottom > screen_height:
    #         return False

    #     roi_area = roi_width * roi_height
    #     screen_area = screen_width * screen_height
    #     roi_ratio = roi_area / screen_area

    #     return roi_ratio <= max_ratio
