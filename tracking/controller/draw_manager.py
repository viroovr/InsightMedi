
from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from controller.util_annotation import *
from matplotlib.patches import Rectangle
from data.data_manager import DataManager


class DrawManager():
    def __init__(self, canvas: FigureCanvas, get) -> None:
        self.get = get
        self.dd: DataManager = self.get('data')
        self.annotation_mode = None
        self.annotation = []
        self.selector_mode = None

        self.canvas = canvas
        self.label_name = None
        self.current_annotation = None
        self.is_drawing = False
        self.is_move = False
        self.cid = []

        self.start = self.end = None
        self.drag = []

    def init_figure(self):
        self.annotation_ax = self.canvas.figure.add_subplot(111, aspect='auto', zorder=1, facecolor="#3A3A3A")
        self.annotation_ax.patch.set_facecolor("#3A3A3A")
        self.annotation_ax.axis("off")

        self.frame_ax = self.canvas.figure.add_subplot(111, aspect='auto', facecolor="#3A3A3A")
        self.frame_ax.axis("off")

    # mpl connect & disconnect
    def set_mpl_connect(self, *args):
        """args순서 : button_press_event, motion_notify_event, button_release_event, pick_event"""
        self.set_mpl_disconnect()
        events = ['button_press_event', 'motion_notify_event',
                  'button_release_event', 'pick_event']
        self.cid.extend(self.canvas.mpl_connect(event, handler)
                        for event, handler in zip(events, args))

    def set_mpl_disconnect(self):
        for cid in self.cid:
            self.canvas.mpl_disconnect(cid)
        self.cid.clear()

    def init_draw_mode(self, mode, label):
        self.start = self.end = None

        self.selector_mode = 'drawing'

        self.label_name = label

        self.annotation_mode = mode
        self.set_mpl_connect(self.on_mouse_press,
                             self.on_draw_mouse_move, self.on_draw_mouse_release)

    def init_selector(self, mode):
        self.drag.clear()
        self.start = self.end = None

        self.selector_mode = 'selector'

        self.annotation_mode = mode if mode == "delete" else None
        if mode != "delete" and mode != "selector":
            print("Unexpected mode name")
            return
        self.set_mpl_connect(self.selector_on_press, self.selector_on_move,
                             self.selector_on_release, self.selector_on_pick)

    # selector events
    def selector_on_pick(self, event):
        if self.is_move or self.selector_mode != 'selector':
            return
        modifier = event.mouseevent.modifiers

        if 'ctrl' in modifier and len(modifier) == 1:
            # print('ctrl + click')
            if event.artist in self.annotation:
                set_edge_thick(event.artist)
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
        if not self.annotation or self.selector_mode != 'selector':
            return
        for an in self.annotation:
            self.drag.append((an.xy, (event.xdata, event.ydata)))
        print(self.drag)
        self.is_move = True

    def selector_on_move(self, event):
        """마우스로 드래그하면 self.annotation를 움직일 수 있게 합니다."""
        if not self.drag or not self.is_move or self.selector_mode != 'selector':
            return

        for i, an in enumerate(self.annotation):
            (x0, y0), (xpress, ypress) = self.drag[i]
            dx = event.xdata - xpress
            dy = event.ydata - ypress

            an.set_x(x0 + dx)
            an.set_y(y0 + dy)

        self.canvas.draw()

    def selector_on_release(self, event):
        if not self.annotation or not self.is_move or self.selector_mode != 'selector':
            return
        self.is_move = False
        for an in self.annotation:
            self.modify_label_data(an)
        self.drag.clear()

    # draw annotation events
    def on_mouse_press(self, event):
        if event.button != 1 or self.is_drawing:
            return
        self.is_drawing = True
        self.select_off_all()
        if event.inaxes:
            self.start = (event.xdata, event.ydata)
            self.color = random_bright_color()
        else:
            print("Clicked outside the axes!")

    def on_draw_mouse_move(self, event):
        if not self.is_drawing or not event.inaxes:
            return
        if self.start is None:
            self.start = (event.xdata, event.ydata)
            self.color = random_bright_color()
        self.end = (event.xdata, event.ydata)
        self.draw_annotation()

    def on_draw_mouse_release(self, event):
        if event.button == 1:
            self.is_drawing = False
            if event.inaxes:
                self.end = (event.xdata, event.ydata)
            else:
                print("Clicked outside the axes!")

            if self.start and self.end:
                self.draw_annotation()
                self.add_annotation(self.label_name, self.color)
                self.init_selector("selector")

    def draw_annotation(self):
        if self.end is None or self.start is None or self.selector_mode != "drawing":
            return
        if self.current_annotation:
            # 연속적인 라벨의 그림을 보여주기 위해 이전 annotation을 제거해줍니다.
            self.current_annotation.remove()

        if self.annotation_mode == "rectangle":
            self.current_annotation = self.annotation_ax.add_patch(
                Rectangle(*get_rectangle_coords(self.start, self.end), fill=False, picker=True,
                          label=self.label_name, edgecolor=self.color))

        set_edge_thick(self.current_annotation, line_width=3)
        self.canvas.draw()

    def add_annotation(self, label_name, color):
        print(self.current_annotation)
        self.annotation.append(self.current_annotation)
        self.dd.add_label("rectangle", label_name,
                          get_rectangle_coords(self.start, self.end), color)

    # select functions
    def select_current_edge(self, annotation, isOff=False):
        """
        현재 self.ax에서 선택한 annotation만 두께를 강조합니다.

        Args:
            annotataion(annotation): 선 또는 도형 객체입니다.
            isOff(bool): True일 때, 다른 모든 라벨들의 강조를 끕니다.
        """
        if isOff:
            self.select_off_all()
        self.annotation.append(annotation)
        self.set_edge_thick(annotation, line_width=3)
        self.canvas.draw()

    def select_off_all(self):
        """
        현재 self.ax에서 모든 annotation들의 강조를 풉니다.
        """
        for patch in self.annotation:
            set_edge_thick(patch)
        self.current_annotation = None
        self.annotation.clear()
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
        self.annotation.clear()
        self.canvas.draw()

    def erase_annotation(self, _label_name):
        """현재 self.ax에 _label_name의 patch들과 선들을 제거합니다.

        Args:
            _label_name(string): 주어진 라벨이름의 annotation을 제거합니다.
        """
        (patch.remove()
         for patch in self.annotation_ax.patches if patch.get_label() == _label_name)
        (patch.remove()
         for patch in self.annotation_ax.lines if patch.get_label() == _label_name)
        self.canvas.draw()

    def erase_all_annotation(self):
        """현재 self.ax에 있는 모든 patch들과 선들을 제거합니다."""
        (patch.remove() for patch in self.annotation_ax.patches)
        (patch.remove() for patch in self.annotation_ax.lines)
        self.annotation.clear()
        self.canvas.draw()

    def pop_annotation(self, label_name):
        self.annotation = [
            an for an in self.annotation if an.get_label() != label_name]

    # modify functions
    def modify_label_data(self, ar):
        """
        변경된 객체의 좌표값들을 읽어와 self.dd에 저장합니다.

        Args:
            ar(annotation): annotation 객체를 인자로 주어야 합니다.
        """
        ret_points = (ar.get_xy(), ar.get_width(), ar.get_height())
        color = get_color(ar)
        self.dd.modify_label_data(ar.get_label(), ret_points, color)

    def go_to_frame(self, frame, _label_name=[]):
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
        annotations_to_select = []
        info = self.dd.get_frame_label_info(frame)
        for drawing_type, label, coords, color in info:
            if drawing_type == "rectangle":
                annotation = Rectangle(coords[0], coords[1], coords[2], fill=False,
                                       picker=True, label=label, edgecolor=color)
                self.annotation_ax.add_patch(annotation)

            if label in _label_name:
                annotations_to_select.append(annotation)
        for annotation in annotations_to_select:
            self.select_current_edge(annotation)
        self.canvas.draw()

    def frame_show(self, frame, cmap, clear=False):
        """
        img를 보여줍니다.

        Args:
            frame (ndarray): self.ax에 보여줄 이미지 입니다.
            cmap (cmap): 이미지의 color map을 설정합니다.
            clear (bool): self.ax를 clear하고 이미지를 보여줍니다.
        """
        if clear:
            self.annotation_ax.clear()
            self.frame_ax.clear()
        self.frame_ax.imshow(frame, cmap=cmap)
        self.frame_ax.axis("off")
        self.canvas.draw()