import os
from typing import List
import matplotlib
from data.video_manager import VideoManger
from data.label_manager import LabelManager
from data.dcm_manager import DcmManager
matplotlib.use("Qt5Agg")


class DataManager():
    def __init__(self, get) -> None:
        self.get = get

        # 'dcm' for DICOM files, 'mp4' for MP4 files.
        self.file_mode = None
        self.label_dir = None

        self.vm = VideoManger()
        self.dm = DcmManager()
        self.lm = LabelManager()

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

        if file_extension == "mp4":
            self.file_mode = 'mp4'
            self.vm.open_file(fname[0])

        self.lm.load_label_dict(self.label_dir)

    def load_all_label(self):
        self.lm.load_all_label()

    def save_label(self):
        self.lm.save_label(self.label_dir)

    def add_label(self, drawing_type, label_name, coords, color, frame_number=None):
        frame_number = self.vm.get_frame_number() if frame_number is None else frame_number
        self.lm.add_label(drawing_type, label_name,
                          coords, color, frame_number)

    def delete_label_file(self, file_name):
        self.lm.delete_label_file(self.label_dir, file_name)

    def delete_label(self, _label_name, frame=None):
        frame_number = int(frame) if frame is not None else self.frame_number
        self.lm.delete_label(_label_name, frame_number)

    def modify_label_data(self, _label_name, _coor, _color):
        self.lm.modify_label_data(
            self.vm.get_frame_number(), _label_name, _coor, _color)

    def frame_label_check(self, frame) -> List:
        return self.lm.frame_label_check(frame)

    def get_frame_label_str(self):
        return self.vm.get_frame_label_str()

    def get_image(self):
        if self.file_mode == 'mp4':
            return self.vm.get_frame()
