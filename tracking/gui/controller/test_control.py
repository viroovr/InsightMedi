import matplotlib.pyplot as plt
import numpy as np
import cv2
import sys
import threading

import copy
from time import sleep
from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from matplotlib.patches import Rectangle
from gui.data.test_data import DcmData
import random


class Controller():
    def __init__(self, dd: DcmData, canvas: FigureCanvas, gui) -> None:
        self.canvas = canvas
        self.dd = dd
        self.gui = gui
        self.fig = canvas.figure
        self.ax = self.fig.add_subplot(111, aspect='auto')

        # canvas fig 색상 변경
        self.fig.patch.set_facecolor('#303030')
        self.ax.patch.set_facecolor("#3A3A3A")
        self.ax.axis("off")
        # self.ax.tick_params(axis = 'x', colors = 'gray')
        # self.ax.tick_params(axis = 'y', colors = 'gray')

        self.annotation_mode = None
        self.annotation = []
        self.current_annotation = None
        self.selector_mode = None
        self.cid = []

        self.start = None
        self.end = None
        self.is_drawing = False
        self.is_move = False

        self.press = None

        self.tracker = {}
        self.is_tracking = False
        self.toggle = False
    # mpl connect & disconnect
    def set_mpl_connect(self, *args):
        """다음순서로 args받아야 합니다. button_press_event, motion_notify_event, button_release_event"""
        cid1 = self.canvas.mpl_connect('button_press_event', args[0])
        cid2 = self.canvas.mpl_connect('motion_notify_event', args[1])
        cid3 = self.canvas.mpl_connect('button_release_event', args[2])
        self.cid.extend([cid1, cid2, cid3])

    def set_mpl_disconnect(self):
        if self.cid:
            for cid in self.cid:
                self.canvas.mpl_disconnect(cid)
        self.cid = []

    # init functions
    def init_draw_mode(self, mode, label):
        # 직선 그리기 기능 구현
        self.label_name = label
        self.start = None
        self.end = None
        self.is_drawing = False
        self.selector_mode = "drawing"
        self.annotation_mode = mode
        print(f"Drawing mode : {mode}")
        self.set_mpl_disconnect()
        self.set_mpl_connect(self.on_mouse_press,
                             self.on_draw_mouse_move, self.on_draw_mouse_release)

    def init_selector(self, mode):
        self.set_mpl_disconnect()
        self.start = None
        self.end = None
        self.is_move = False
        if mode == "delete":
            self.selector_mode = 'selector'
            self.annotation_mode = mode
        elif mode == 'selector':
            self.selector_mode = mode
            self.annotation_mode = None
        else:
            print("Unexpected mode name")
            return

        cid0 = self.canvas.mpl_connect('pick_event', self.selector_on_pick)
        self.cid.append(cid0)
        self.set_mpl_connect(self.selector_on_press,
                             self.selector_on_move, self.selector_on_release)

    # color, thickness

    def get_color(self, annotation):
        # rectangle, circle
        return annotation.get_edgecolor()

    def set_edge_color(self, annotation, color):
        # rectangle, circle
        annotation.set_edgecolor(color)

    def set_edge_thick(self, annotation, line_width=1):
        annotation.set_linewidth(line_width)

    def random_bright_color(self):
        # 랜덤한 RGB 값을 생성합니다.
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)

        # 밝기 조정을 위한 랜덤한 계수를 생성합니다.
        brightness_factor = random.uniform(0.5, 1.0)  # 0.5부터 1.0 사이의 값을 가집니다.

        # RGB 값에 밝기 조정을 적용합니다.
        red = int(red * brightness_factor)
        green = int(green * brightness_factor)
        blue = int(blue * brightness_factor)

        # RGB 값을 16진수 색상 코드로 변환합니다.
        hex_color = "#{:02x}{:02x}{:02x}".format(red, green, blue)

        return hex_color

    # selector events
    def selector_on_pick(self, event):
        if self.selector_mode == 'selector':
            modifier = event.mouseevent.modifiers
            # 현재 선택된 artist를 self.artist로 저장시켜 다른 함수에서 접근 가능하게 합니다.
            if 'ctrl' in modifier and len(modifier) == 1:
                print('ctrl + click')
                self.gui.is_tracking = False
                if event.artist in self.annotation:
                    # print("annotation에 이미 있을 경우 해제합니다.")
                    self.set_edge_thick(event.artist)
                    self.annotation.remove(event.artist)
                    self.canvas.draw()
                else:
                    # print("annotation에 없을 경우 annotation에 추가합니다.")
                    self.select_current_edge(event.artist)

            elif len(self.annotation) <= 1:
                self.select_current_edge(event.artist, isOff=True)

    def selector_on_press(self, event):
        """
        선택된 라벨이 self.annotation에 저장되어있어야 하며
        선택한 라벨의 x, y데이터를 self.press에 저장하는 기능입니다.
        """
        if not self.annotation and self.selector_mode != 'selector':
            print("annotation is none")
            return
        # if event.inaxes != self.annotation.axes:
        #     # print("not in axes")
        #     self.select_off_all()
        #     return
        if event.button == 1:
            self.start = []
            # print(self.annotation)
            for an in self.annotation:
                # contains, attrd = an.contains(event)
                # if not contains:
                #     # print("not contatins")
                #     return
                self.start.append((an.xy, (event.xdata, event.ydata)))

            self.is_move = True
        # print(f"self press is {self.press}")

    def selector_on_move(self, event):
        """마우스로 드래그하면 self.annotation를 움직일 수 있게 합니다."""
        if not self.start or self.selector_mode != 'selector' or not self.is_move:
            # print(self.start, self.selector_mode, self.is_move)
            # print("selector_on_move fail")
            return

        for i, an in enumerate(self.annotation):
            # print(self.start[i])
            (x0, y0), (xpress, ypress) = self.start[i]
            # print(x0, y0, xpress, ypress)
            dx = event.xdata - xpress
            dy = event.ydata - ypress

            an.set_x(x0 + dx)
            an.set_y(y0 + dy)

        self.canvas.draw()

    def selector_on_release(self, event):
        if not self.annotation and not self.is_move:
            return
        if event.button == 1:
            self.is_move = False
            for an in self.annotation:
                self.modify_label_data(an)
            self.start = None
            self.end = None

    # draw annotation events
    def on_mouse_press(self, event):
        if event.button == 1:
            self.is_drawing = True
            self.select_off_all()
            if event.inaxes:
                self.start = (event.xdata, event.ydata)
                self.color = self.random_bright_color()
            else:
                print("Clicked outside the axes!")

    def on_draw_mouse_move(self, event):
        if self.is_drawing and event.inaxes:
            if self.start is None:
                self.start = (event.xdata, event.ydata)
                self.color = self.random_bright_color()
            self.end = (event.xdata, event.ydata)
            self.draw_annotation(self.color)

    def on_draw_mouse_release(self, event):
        if event.button == 1:
            self.is_drawing = False
            if event.inaxes:
                self.end = (event.xdata, event.ydata)
            else:
                print("Clicked outside the axes!")

            if self.start and self.end:
                self.draw_annotation(self.color)
                self.gui.selector()

    def draw_annotation(self, color="red"):
        if self.start and self.end and self.selector_mode == "drawing":
            if self.current_annotation:
                # 연속적인 라벨의 그림을 보여주기 위해 이전 annotation을 제거해줍니다.
                self.current_annotation.remove()

            label_class = self.label_name

            if self.annotation_mode == "rectangle":
                width = abs(self.start[0] - self.end[0])
                height = abs(self.start[1] - self.end[1])
                x = min(self.start[0], self.end[0])
                y = min(self.start[1], self.end[1])
                self.current_annotation = self.ax.add_patch(
                    Rectangle((x, y), width, height, fill=False, picker=True, label=label_class, edgecolor=color))
                if self.is_drawing is False:
                    self.annotation.append(self.current_annotation)
                    self.dd.add_label("rectangle", label_class,
                                      ((x, y), width, height), color)

            # self.artist = self.annotation
            self.set_edge_thick(self.current_annotation, line_width=3)
            self.canvas.draw()

    # delete or remove functions
    def remove_annotation(self):
        """
        self.annotation을 지웁니다.
        """
        if self.annotation is None:
            return
        for an in self.annotation:
            an.remove()
            self.delete_label(an.get_label())
        self.annotation = []
        self.canvas.draw()

    def pop_annotation(self, label_name):
        if not self.annotation:
            return
        for an in self.annotation:
            if an.get_label() == label_name:
                self.annotation.remove(an)
    
    def delete_label(self, label_name):
        """ contorls -> Viewer_GUI -> dcm_data순으로 버튼을 비활성화하고 데이터를 지웁니다."""
        # 모든 frame에 label_name 이름을 가진 label의 개수
        count = 0
        for frame in self.dd.frame_label_dict.values():
            for data in frame.values():
                if label_name in data:
                    count += 1
            # 모든 for문을 돌지 않고 2개 이상일 때 break 합니다.
            if count > 1:
                break

        # GUI에서 모든 프레임에 라벨이 1개만 존재하면 버튼 비활성화
        if count == 1:
            self.gui.disable_label_button(label_name)

        # data에서 현재 frame의 해당 라벨이름 정보 제거하기
        self.dd.delete_label(label_name)

    def erase_annotation(self, _label_name):
        """현재 self.ax에 _label_name의 patch들과 선들을 제거합니다.

        Args:
            _label_name(string): 주어진 라벨이름의 annotation을 제거합니다.
        """
        for patch in self.ax.patches:
            # print(dir(patch))
            if patch.get_label() == _label_name:
                patch.remove()
        for patch in self.ax.lines:
            if patch.get_label() == _label_name:
                patch.remove()
        self.canvas.draw()

    def erase_all_annotation(self):
        """현재 self.ax에 있는 모든 patch들과 선들을 제거합니다."""
        for patch in self.ax.patches:
            patch.remove()
        for patch in self.ax.lines:
            patch.remove()
        self.annotation = []
        self.canvas.draw()

    # modify functions
    def modify_label_data(self, ar):
        """
        변경된 객체의 좌표값들을 읽어와 self.dd에 저장합니다.

        Args:
            ar(annotation): annotation 객체를 인자로 주어야 합니다.
        """
        ret_points = (ar.get_xy(), ar.get_width(), ar.get_height())
        color = self.get_color(ar)
        self.dd.modify_label_data(ar.get_label(), ret_points, color)

    # select functions
    def select_current_edge(self, annotation, isOff=False):
        """
        현재 self.ax에서 선택한 annotation만 두께를 강조합니다.

        Args:
            annotataion(annotation): 선 또는 도형 객체입니다.
            isOff(bool): True일 때, 다른 모든 라벨들의 강조를 끕니다.
        """
        if isOff:
            # ctrl click이 아닐 시 다른 강조들을 해제합니다.
            # print("모두 해제")
            self.select_off_all()
        self.annotation.append(annotation)
        self.set_edge_thick(annotation, line_width=3)
        self.canvas.draw()

    def select_off_all(self):
        """
        현재 self.ax에서 모든 annotation들의 강조를 풉니다.
        """
        for patch in self.ax.patches:
            self.set_edge_thick(patch)
        for patch in self.ax.lines:
            self.set_edge_thick(patch)
        self.canvas.draw()
        self.current_annotation = None
        self.is_tracking = False
        self.annotation = []

    def label_clicked(self, frame, _label_name=[]):
        """
        go버튼 클릭 시 모든 annotation을 지우고 해당 frame으로 이동한 뒤 캔버스에 plot을 그려줍니다.

        Args:
            _label_name(string or empty list): 해당 라벨의 두께를 두껍게 합니다.
                                        empty list일 경우, self.annotation 라벨들의 강조를 유지합니다.
        """
        if not _label_name and self.annotation:
            _label_name = [an.get_label() for an in self.annotation]
            # print(f"{sys._getframe(0).f_code.co_name}: _label_name : {_label_name}")
        self.erase_all_annotation()

        frame_directory = self.dd.frame_label_dict[frame]
        print(f"frame_directory : {frame_directory}")
        for drawing_type in frame_directory:
            label_directory = frame_directory[drawing_type]
            for label in label_directory:
                ld = label_directory[label]
                coords = ld["coords"]
                color = ld["color"]

                if drawing_type == "rectangle":
                    # print("현재 label은 사각형임", ld['rectangle'])
                    annotation = self.ax.add_patch(Rectangle(coords[0], coords[1], coords[2], fill=False,
                                                             picker=True, label=label, edgecolor=color))

                if label in _label_name:
                    # print(f"label : {label}, _label_name : {_label_name}")
                    self.select_current_edge(annotation)
        # print(f"{sys._getframe(0).f_code.co_name}: {self.annotation}")

        self.canvas.draw()

    def img_show(self, img, cmap='viridis', init=False, clear=False):
        """
        img를 보여줍니다.

        Args:
            img (ndarray): self.ax에 보여줄 이미지 입니다.
            cmap (cmap): 이미지의 color map을 설정합니다.
            init (bool): self.ax를 생성합니다.
            clear (bool): self.ax를 clear하고 이미지를 보여줍니다.
        """
        if init:
            self.ax = self.canvas.figure.subplots()
        if clear:
            self.ax.clear()
        self.ax.imshow(img, cmap=cmap)
        self.ax.axis("off")
        self.canvas.draw()

    # object tracking
    # def toggle_object_tracking(self):
    #     if not self.toggle:
    #         self.toggle = True
    #         self.thread = threading.Thread(target=self.init_object_tracking)
    #         # self.init_object_tracking()
    #         self.thread.start()
    #     else:
    #         self.toggle = False
    #         # self.thread.join()
    
    def init_object_tracking(self, oldframe, newframe):
        bbox = self.check_bbox()   # object tracking이 가능한 상태인 지 확인하는 함수
        if bbox:
            # print(np.array_equal(self.dd.image, frame))
            # self.gui.slider.setValue(
            #     self.dd.frame_number + 1)   # 다음 frame으로 업데이트
            # print(np.array_equal(self.dd.image, frame))
            if not self.is_tracking:
                # object tracking 한 결과 나온 라벨링 그리기
                self.object_tracking(oldframe, newframe, bbox, init=True)
                self.is_tracking = True
            else:
                # object tracking 한 결과 나온 라벨링 그리기
                self.object_tracking(oldframe, newframe, bbox)
        else:
            print("No bbox")
            

    def check_bbox(self):
        """
        object tracking이 가능한 상태인 지 확인하고, bbox를 반환합니다.

        Returns:
            bbox (list, empty = False): object tracking이 가능한 상태면 bbox 좌표를 반환하고, 아니면 False를 반환합니다.
        """
        fn = self.dd.frame_number
        label_list = self.dd.frame_label_check(fn - 1)
        next_label_list = self.dd.frame_label_check(fn)
        bbox = []
        print(label_list, next_label_list, self.annotation)
        if self.dd.file_mode == 'mp4' and label_list and self.annotation:
            for annotation in self.annotation:
                label = annotation.get_label()
                if label not in next_label_list:
                    coord_list = self.dd.frame_label_dict[fn - 1]['rectangle'][label]['coords']
                    color = self.dd.frame_label_dict[fn - 1]['rectangle'][label]['color']
                    x = coord_list[0][0]
                    y = coord_list[0][1]
                    w = coord_list[1]
                    h = coord_list[2]
                    bbox.append(
                        (label, [int(x), int(y), int(w), int(h)], color))
                    # print(f"{label}의 bbox:", bbox)
            print("현재 프레임의 bbox들 좌표:", bbox)
        else:
            self.stop_playing()
            print("bbox error")
        return bbox

    def stop_playing(self):
        self.gui.is_tracking = False
        self.gui.playButtonClicked()
    
    def object_tracking(self, oldframe, newframe, bbox, init=False):
        """ 주어진 frame이미지에 tracking한 물체에 bbox를 그리고 정보를 저장합니다.

        Args:
            frame (ndarray): frame이미지
            bbox (List): bounding box의 좌표 리스트
            init (bool, optional): True일때, tracker를 생성합니다. Defaults to False.
        """

        if init:
            print(f"multitracker 초기화")
            self.multitracker = cv2.legacy.MultiTracker_create()
            # ok = self.tracker[label].init(frame, label_bbox)
            for label_bbox in bbox:
                tracker = cv2.legacy.TrackerCSRT_create()
                self.multitracker.add(tracker, oldframe, label_bbox[1])

        ok, new_bboxes = self.multitracker.update(newframe)

        if ok:
            # print(f"기존 bbox {bbox}" )
            # print(f"object tracking한 bbox {new_bboxes}")
            # print(f"선택된 annotation {self.annotation}")
            with open(f'{self.dd.label_dir}/bbox_log.txt', 'a') as log_file:
                for i, new_bbox in enumerate(new_bboxes):
                    # 새로운 라벨 저장을 위해 필요한 데이터들
                    # bbox_ = ((new_bbox[0], new_bbox[1]), new_bbox[2], new_bbox[3])
                    bbox_ = self.refine_bbox(new_bbox, self.dd.frame_width, self.dd.frame_height)
                    if not self.is_roi_within_bounds(new_bbox, bbox_):
                        print("화면 벗어남")
                        self.stop_playing()
                        return 
                    if self.compare_image(oldframe, newframe, bbox[i][1], bbox_, 0.7, 50):
                        # print(self.dd.frame_label_check(self.dd.frame_number - 1))
                        # label = self.annotation[0].get_label()
                        color = bbox[i][2]
                        label = bbox[i][0]
                        log_file.write(f"Frame: {self.dd.frame_number}, Label: {label}, Bbox: {new_bbox}\n")
                        print(*bbox_, color, label)
                        # 라벨 그리기 및 저장
                        self.pop_annotation(label)
                        new_annotation = self.ax.add_patch(
                            Rectangle(*bbox_,
                                      fill=False, picker=True, label=label, edgecolor=color))
                        self.select_current_edge(new_annotation)
                        # print("현재 선택된 label들:", self.annotation)
                        self.dd.add_label('rectangle', label, bbox_, color,
                                          frame_number=self.dd.frame_number)
                        # print(self.dd.frame_label_dict)
                    else:
                        self.stop_playing()
                        print("유사도 떨어짐 감지")
        else:
            self.stop_playing()
            print("object tracking failed")

    def compare_image(self, oldframe, newframe, oldbox, newbox, similarity_threshold, coords_threshold):
        print(f"old : {oldbox}, new: {newbox}")
        # print(np.array_equal(oldframe, newframe))
        roi1 = oldframe[oldbox[1]:oldbox[1] +
                       oldbox[3], oldbox[0]:oldbox[0]+oldbox[2]]
        roi2 = newframe[newbox[0][1]:newbox[0][1] +
                        newbox[2], newbox[0][0]:newbox[0][0]+newbox[1]]

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
            previous_hist = cv2.calcHist([previous_hsv], [0], None, [256], [0,256])
            current_hist = cv2.calcHist([current_hsv], [0], None, [256], [0,256])

            # normalize
            previous_hist = previous_hist / previous_hist.sum()
            current_hist = current_hist / current_hist.sum()

            # comapre histogram
            score = cv2.compareHist(previous_hist, current_hist, cv2.HISTCMP_BHATTACHARYYA)
            print('similarity score:', 1 - score)

            return 1 - score
    
    def is_roi_within_bounds(self, bbox, refined_bbox, max_ratio=0.5):
        # roi_x = bbox[0]
        # roi_y = bbox[1]
        roi_width = bbox[2]
        roi_height = bbox[3]
        # roi_right = roi_x + roi_width
        # roi_bottom = roi_y + roi_height
        # print(bbox)
        # print(roi_right, roi_bottom)
        # print("roix",roi_x, "roiy", roi_y)
        refined_roi_width = refined_bbox[1]
        refined_roi_height = refined_bbox[2]

        roi_area = roi_width * roi_height
        refined_roi_area = refined_roi_width * refined_roi_height
        roi_ratio = refined_roi_area / roi_area
        print("roi ratio:", roi_ratio)

        return roi_ratio >= max_ratio

        # if roi_x < 0 or roi_y < 0 or roi_right > screen_width or roi_bottom > screen_height:
        #     return False
 
        # roi_area = roi_width * roi_height
        # screen_area = screen_width * screen_height
        # roi_ratio = roi_area / screen_area

        # return roi_ratio <= max_ratio

    def refine_bbox(self, bbox, screen_width, screen_height):
        x = max(int(bbox[0]), 0)
        y = max(int(bbox[1]), 0)
        w = min(int(bbox[2]), screen_width - x)
        h = min(int(bbox[3]), screen_height - y)
        print('refined:',x,y,w,h)

        return ((x,y),w,h)