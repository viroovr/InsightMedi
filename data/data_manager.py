import os
from typing import List, Tuple
import matplotlib
from data.video_manager import VideoManager
from data.label_manager import LabelManager
from data.dcm_manager import DcmManager
matplotlib.use("Qt5Agg")


class DataManager():
    def __init__(self, get) -> None:
        self.get = get

        # 'dcm' for DICOM files, 'mp4' for MP4 files.
        self.file_mode = None
        self.label_dir = None

        self.vm = VideoManager()
        self.dm = DcmManager()
        self.lm = LabelManager()

    def init_instance_member(self):
        pass

    def reset_env(self):
        self.lm.reset_label()
        self.vm.reset_video()
        self.dm.reset_dcm()

    def open_file(self, fname):
        file_name, file_extension = os.path.splitext(
            os.path.basename(fname[0]))
        file_dir = os.path.dirname(fname[0])
        self.label_dir = file_dir + f"/{file_name}"

        self.reset_env()
        os.makedirs(self.label_dir, exist_ok=True)
        if file_extension == ".mp4":
            self.file_mode = 'mp4'
            self.vm.open_file(fname[0])

        elif file_extension == ".DCM" or file_extension == ".dcm":
            self.file_mode = 'dcm'
            self.dm.open_dcm_file(fname)

        self.lm.load_label_dict(self.label_dir)

    def load_all_label(self):
        return self.lm.load_all_label()

    def is_label_exist(self, label_name):
        return self.lm.is_label_exist(label_name, self.get_frame_number())

    def save_label(self):
        self.lm.save_label(self.label_dir)

    def add_label(self, drawing_type, label_name, coords, color, frame_number=None):
        frame_number = self.get_frame_number() if frame_number is None else frame_number
        self.lm.add_label(drawing_type, label_name,
                          coords, color, frame_number)

    def delete_label_file(self, file_name):
        self.lm.delete_label_file(self.label_dir, file_name)

    def delete_label(self, label_name, frame=None):
        frame_number = int(
            frame) if frame is not None else self.vm.get_frame_number()
        self.lm.delete_label(label_name, frame_number)

    def modify_label_data(self, label_name, coor, color):
        self.lm.modify_label_data(
            self.get_frame_number(), label_name, coor, color)

    def frame_label_check(self, frame) -> List:
        return self.lm.frame_label_check(frame)

    def get_file_path(self):
        return f"{self.label_dir}.{self.file_mode}"

    def get_frame_label_str(self):
        """
        f"{프레임} / {전체프레임}" 형식의 str을 반환합니다.
        """
        if self.file_mode == 'dcm':
            return ""
        elif self.file_mode == "mp4":
            return self.vm.get_frame_label_str()

    def get_image(self):
        if self.file_mode == 'mp4':
            return self.vm.get_frame()
        elif self.file_mode == 'dcm':
            return self.dm.get_image()

    def get_total_frame_number(self):
        return self.vm.total_frame

    def label_count(self, label_name):
        return self.lm.label_count(label_name)

    def get_frame_label_info(self, frame) -> List[Tuple[str, str, Tuple, str]]:
        """
        frame_label_dict에서 주어진 frame key값의 label data를 반환합니다
        [(drawing_type, label_name, coords, color)]형식으로 반환합니다
        """
        return self.lm.get_frame_label_info(frame)

    def update_frame(self):
        return self.vm.updateFrame()

    def set_frame(self, value):
        self.vm.set_frame(value)

    def get_first_frame(self, label):
        return self.lm.get_first_frame(label)

    def get_frame_number(self):
        if self.file_mode == 'mp4':
            return self.vm.frame_number
        elif self.file_mode == 'dcm':
            return 0

    def get_mp4_info(self):
        """
        Returns:
            (frame_width, frame_height)
        """
        return self.vm.get_mp4_info()

    def get_tracking_num(self, text):
        return self.vm.get_tracking_num(text)

    def check_log_path(self):
        log_path = f"{self.label_dir}/log"
        os.makedirs(log_path, exist_ok=True)
        return log_path

    def get_windwoing_value(self):
        return self.dm.get_windwoing_value()

    def dcm_windowing_change(self, start, end):
        return self.dm.dcm_windowing_change(start, end)

    def is_last_frame(self):
        return self.vm.is_last_frame()

    def get_color_by_type_and_name(self, drawing_type, label_name):
        return self.lm.get_color_by_type_and_name(drawing_type, label_name)

    def get_dcm_meta(self, meta):
        return self.dm.get_dem_meta(meta)
