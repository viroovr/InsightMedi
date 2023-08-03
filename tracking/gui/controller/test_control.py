import matplotlib.pyplot as plt
import numpy as np
import cv2

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
                print(self.annotation)
                self.gui.is_tracking = False
                if event.artist in self.annotation:
                    # print("annotation에 이미 있을 경우 해제합니다.")
                    self.set_edge_thick(event.artist)
                    self.annotation.remove(event.artist)
                    self.canvas.draw()
                else:
                    # print("annotation에 없을 경우 annotation에 추가합니다.")
                    self.select_current_edge(event.artist, append=True)
                
            elif len(self.annotation) > 1:
                print('click')
                # self.select_current_edge(event.artist)
            else:
                print('click')
                self.select_current_edge(event.artist)

    def selector_on_press(self, event):
        """
        선택된 라벨이 self.annotation에 저장되어있어야 하며
        선택한 라벨의 x, y데이터를 self.press에 저장하는 기능입니다.
        """
        if not self.annotation and self.selector_mode != 'selector':
            # print("annotation is none")
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
        if self.start is None or self.selector_mode != 'selector' or not self.is_move:
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
            self.start = (event.xdata, event.ydata)
            self.color = self.random_bright_color()

    def on_draw_mouse_move(self, event):
        if self.is_drawing:
            self.end = (event.xdata, event.ydata)
            self.draw_annotation(self.color)

    def on_draw_mouse_release(self, event):
        if event.button == 1:
            self.is_drawing = False
            self.end = (event.xdata, event.ydata)
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
                self.current_annotation =  self.ax.add_patch(
                    Rectangle((x, y), width, height, fill=False, picker=True, label=label_class, edgecolor=color))
                if self.is_drawing is False:
                    self.annotation.append(self.current_annotation)
                    self.dd.add_label("rectangle", label_class,
                                      ((x, y), width, height), color)
                    
            #self.artist = self.annotation
            self.set_edge_thick(self.current_annotation, line_width=3)
            self.canvas.draw()

    # delete or remove functions
    def remove_annotation(self, annotation=None):
        """ annotation이 주어지면 annotation을 지우고 
            주어지지 않는 경우, self.annotation을 지웁니다.

        Args:
            annotation (Line2D or Rectangle): 선이나 도형 객체. Defaults to None.
        """
        if self.annotation is None:
            return
        if annotation is None:
            annotation = self.annotation
        annotation.remove()
        self.canvas.draw()
        self.delete_label(annotation.get_label())

    def delete_label(self, label_name):
        """ contorls > Viewer_GUI > dcm_data순으로 먼저 버튼을 비활성화하고 데이터 지우는 순차적 구조입니다."""
        count = 0
        gui = True
        for frame in self.dd.frame_label_dict.values():
            for data in frame.values():
                if label_name in data:
                    count += 1
                    """if count > 2:
                        gui = False
                        break """

        # GUI에서 모든 프레임에 라벨이 존재하지 않으면 버튼 비활성화
        if gui:
            label_exist = False
            for frame in self.dd.frame_label_dict.keys():
                if label_name in self.dd.frame_label_check(frame):
                    label_exist = True

            if not label_exist or count == 1:
                self.gui.disable_label_button(label_name)

        # data에서 현재 frame의 해당 라벨이름 정보 제거하기
        self.dd.delete_label(label_name)
    

    def erase_annotation(self, _label_name):
        """현재 self.ax에 _label_name의 patch들과 선들을 제거합니다."""
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
    def select_current_edge(self, annotation, append=False):
        """
        현재 self.ax에서 선택한 annotation만 두께를 강조합니다.

        Args:
            annotataion(annotation): 선 또는 도형 객체입니다.
        """
        if not append:
            # ctrl click이 아닐 시 다른 강조들을 해제합니다.
            print("모두 해제")
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
        self.annotation = []

    def label_clicked(self, frame, _label_name=None):
        """
        go버튼 클릭 시 모든 annotation을 지우고 해당 frame으로 이동한 뒤 캔버스에 plot을 그려줍니다.

        Args:
            _label_name(string): 해당 라벨의 두께를 두껍게 합니다.
        """
        annotation = self.annotation
        self.erase_all_annotation()
        frame_directory = self.dd.frame_label_dict[frame]
        if _label_name is None and annotation is not None:
            self.annotation = annotation
            _label_name = self.annotation.get_label()

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

                if _label_name == label:
                    self.set_edge_thick(annotation, line_width=3)

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

    def check_bbox(self):
        """
        object tracking이 가능한 상태인 지 확인하고, bbox를 반환합니다.

        Returns:
            bbox (list, empty = False): object tracking이 가능한 상태면 bbox 좌표를 반환하고, 아니면 False를 반환합니다.
        """
        label_list = self.dd.frame_label_check(self.dd.frame_number)
        next_label_list = self.dd.frame_label_check(self.dd.frame_number+ 1)
        bbox = []
        if self.dd.file_mode == 'mp4' and label_list and self.annotation:
            label = self.annotation.get_label()
            if label not in next_label_list:
                print("object tracking으로 선택된 label:",label)
                coord_list = self.dd.frame_label_dict[self.dd.frame_number]['rectangle'][label]['coords']
                x = coord_list[0][0]
                y = coord_list[0][1]
                w = coord_list[1]
                h = coord_list[2]
                bbox = [int(x), int(y), int(w), int(h)]
                print("bbox:", bbox)
        return bbox

    
    def object_tracking(self, frame, bbox, init=False):
        if init:
            print("tracker 초기화")
            self.tracker = cv2.TrackerCSRT_create()
            ok = self.tracker.init(frame, bbox)
    
        ok, bbox = self.tracker.update(frame)
        if ok:
            print("obect tracking한 bbox", bbox)

            # 새로운 라벨 저장을 위해 필요한 데이터들
            bbox_ = ((bbox[0], bbox[1]), bbox[2], bbox[3])
            print(self.dd.frame_label_check(self.dd.frame_number - 1))
            label = self.annotation.get_label()
            color = self.dd.frame_label_dict[self.dd.frame_number - 1]['rectangle'][label]['color']

            # 라벨 그리기 및 저장
            self.annotation = self.ax.add_patch(
                    Rectangle((bbox[0], bbox[1]), bbox[2], bbox[3], fill=False, picker=True, label=label, edgecolor=color))
            self.set_edge_thick(self.annotation, line_width=3)
            self.canvas.draw()
            self.dd.add_label('rectangle', label, bbox_, color,
                              frame_number=self.dd.frame_number)
            #print(self.dd.frame_label_dict)
