import cv2
from copy import deepcopy
# import numpy as np


class VideoManger():
    def __init__(self) -> None:
        self.video_player = None

        self.frame = None
        self.frame_number = 0

        self.video_status = None

        self.total_frame = 0
        self.frame_width = 0
        self.frame_height = 0

    def get_frame_number(self):
        return self.frame_number

    def get_frame(self):
        return self.frame

    def reset_video(self):
        if self.video_player is not None:
            self.video_player.release()

    def open_file(self, fname):
        self.frame_number = 0

        self.video_player = cv2.VideoCapture()
        self.video_player.open(fname)

        self.total_frame = int(self.video_player.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_width = int(self.video_player.get(
            cv2.CAP_PROP_FRAME_WIDTH))  # 프레임 폭
        self.frame_height = int(self.video_player.get(
            cv2.CAP_PROP_FRAME_HEIGHT))  # 프레임 높이

        ret, frame = self.video_player.read()
        if ret:
            self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def get_frame_label_str(self):
        return f"{self.frame_number} / {int(self.total_frame) - 1}"

    def updateFrame(self):
        # frame update
        prev_frame = deepcopy(self.frame)
        ret, frame = self.video_player.read()
        if ret:
            self.frame_number = int(
                self.video_player.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame = rgb_frame
            print("update Frame 호출, 현재 frame: ", self.frame_number)

        return ret, self.frame_number, prev_frame, rgb_frame

    def set_frame(self, value):
        self.frame_number = value
        self.video_player.set(cv2.CAP_PROP_POS_FRAMES, value)

    def get_mp4_info(self):
        return self.frame_width, self.frame_height