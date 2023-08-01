import os
import matplotlib
import cv2
import json

matplotlib.use("Qt5Agg")


class DcmData():
    def __init__(self) -> None:
        # file_mode가 'dcm'이면 dcm또는 DCM파일. file_mode가 'mp4' mp4파일을 가리킵니다.
        self.file_mode = None

        self.label_dir = None
        # {"frame_number”: {”type”: {”label id1”: {coords: [], color : “” }}, “label id2”: [coords]}
        self.frame_label_dict = {}

        self.ds = None
        self.image = None

        self.video_player = None
        self.frame_number = 0
        self.total_frame = 0

    def open_file(self, fname, *args, **kwargs):
        file_extension = fname[0].split('/')[-1].split(".")[-1]
        file_name = fname[0].split('/')[-1].split(".")[0]
        file_dir = os.path.dirname(fname[0])
        self.label_dir = file_dir + f"/{file_name}"
        self.frame_label_dict.clear()
        self.image = None

        try:
            os.mkdir(self.label_dir)
        except FileExistsError:
            pass

        if file_extension == "mp4":
            self.file_mode = 'mp4'
            self.open_mp4_file(fname)

    # text 파일로부터 현재 label dictionary를 불러옴
    def load_label_dict(self, custom_range=None):
        for file_name in os.listdir(self.label_dir):
            frame_number = int(file_name.split(".")[0])
            frame_dict = {}
            if file_name.endswith('.txt'):
                try:
                    filepath = os.path.join(self.label_dir, file_name)
                    with open(filepath, "r") as f:
                        t = json.load(f)
                        for key in t:
                            frame_dict[key] = t[key]
                        self.frame_label_dict[frame_number] = frame_dict

                except FileNotFoundError:
                    pass

    def save_label(self):
        for key in self.frame_label_dict:
            with open(f"{self.label_dir}/{key}.txt", 'w') as f:
                f.write(json.dumps(self.frame_label_dict[key]))

    def add_label(self, drawing_type, label_name, coords, color="red", frame_number=None):
        if frame_number is None:
            frame_number = self.frame_number
        try:
            frame_dict = self.frame_label_dict[frame_number]
        except KeyError:
            self.frame_label_dict[frame_number] = {}
            frame_dict = self.frame_label_dict[frame_number]   # {}

        try:
            label_type_dict = frame_dict[drawing_type]
        except KeyError:
            frame_dict[drawing_type] = {}
            label_type_dict = frame_dict[drawing_type]

        # frame_label_dict에 label data 저장
        label_data_dict = {}
        label_data_dict['coords'] = coords
        label_data_dict['color'] = color

        label_type_dict[label_name] = label_data_dict

    def open_mp4_file(self, fname):
        self.frame_number = 0
        self.video_player = cv2.VideoCapture()
        self.video_player.open(fname[0])
        self.total_frame = int(self.video_player.get(cv2.CAP_PROP_FRAME_COUNT))
        
        ret, self.frame = self.video_player.read()
        if ret:
            self.image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)

    def delete_label_file(self, file_name):
        file_path = f"{self.label_dir}/{file_name}.txt"
        print("file_path:", file_path)

        try:
            os.remove(file_path)
            print(f"file '{file_name}' has been deleted successfully")
        except FileNotFoundError:
            print(f"file '{file_name}' not found")

    def delete_label(self, _label_name, frame=None):
        print(self.frame_label_dict)
        print(f"frame : {frame}")

        if frame is not None:
            frame_number = int(frame)
        else:
            frame_number = self.frame_number

        frame_dict = self.frame_label_dict[frame_number]
        for label_dict in frame_dict.values():
            if _label_name in label_dict:
                label_dict.pop(_label_name)
                break
        print(f"라벨 정보 제거 후: {self.frame_label_dict}")

    def modify_label_data(self, _label_name, _coor, _color):
        frame_dict = self.frame_label_dict[self.frame_number]
        for label_dict in frame_dict.values():
            if _label_name in label_dict:
                label_dict[_label_name]['coords'] = _coor
                label_dict[_label_name]['color'] = _color
                break

    def frame_label_check(self, frame):
        try:
            frame_dict = self.frame_label_dict[frame]
            label_list = []
            for _, label_dict in frame_dict.items():
                for label in label_dict:
                    label_list.append(label)

            if label_list:
                return label_list

        except KeyError:
            pass
        return False