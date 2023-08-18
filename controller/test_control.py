from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas

from data.data_manager import DataManager
from .draw_manager import DrawManager
from .tracker_manager import TrackerManager
# from gui.test_gui import Gui as gu


class Controller():
    def __init__(self, get) -> None:
        self.get = get

    def init_instance_member(self):
        self.dd: DataManager = self.get('data')
        self.gui = self.get('gui')
        self.canvas: FigureCanvas = self.gui.canvas
        self.dm = DrawManager(self.canvas, self.get)
        self.tm: TrackerManager = TrackerManager(self.get, self.dm)

    # init functions
    def init_draw_mode(self, mode, label):
        print(f"Drawing mode : {mode}, label : {label}")
        self.dm.init_draw_mode(mode, label)

    def init_selector(self, mode):
        self.dm.init_selector(mode)
        
    def delete_label(self, label_name):
        """ 현재 프레임에서 label_name 데이터를 지웁니다."""
        # data에서 현재 frame의 해당 라벨이름 정보 제거하기
        self.dd.delete_label(label_name)

    def update_frame(self, tracking_active=False):
        ret, frame_number, prev_frame, frame = self.dd.update_frame()
        if ret:
            if tracking_active:
                self.tm.init_object_tracking(prev_frame, frame)

                if not self.tm.get_tracking_status():
                    self.gui.trackingClicked()

            # frame에 라벨이 존재하면 라벨을 보여줍니다.
            self.frame_show(frame, clear=True)
            # if self.dd.frame_label_check(frame_number):
            self.go_clicked(frame_number)
            # else:
            #     self.erase_all_annotation()
        return ret, frame_number

    def select_off_all(self):
        self.dm.select_off_all()

    def remove_annotation(self):
        self.dm.remove_annotation()

    def erase_annotation(self, label_name):
        self.dm.erase_annotation(label_name)

    def erase_all_annotation(self):
        """현재 self.ax에 있는 모든 patch들과 선들을 제거합니다."""
        self.dm.erase_all_annotation()

    def go_clicked(self, frame_number, _label_name=[]):
        """
        go버튼 클릭 시 모든 annotation을 지우고 해당 frame의 annotation을 캔버스에 plot을 그려줍니다.

        Args:
            _label_name(string or empty list): 해당 라벨의 두께를 두껍게 합니다.
                                        empty list일 경우, self.annotation 라벨들의 강조를 유지합니다.
        """
        self.dm.go_clicked(frame_number, _label_name)

    def label_button_clicked(self, label_name):
        if self.dd.is_label_exist(label_name):
            self.delete_label(label_name)
            self.erase_annotation(label_name)

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

    def start_tracking_status(self):
        self.tm.start_tracking()

    def stop_tracking_status(self):
        self.tm.stop_tracking()
