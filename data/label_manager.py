import os
import json
# from copy import deepcopy
from typing import List


class LabelManager():
    def __init__(self) -> None:
        # Structure: {"frame_number": {"type": {"label name": {"coords": [], "color": ""}}}}
        self.frame_label_dict = {}

    def reset_label(self):
        self.frame_label_dict.clear()

    def load_label_dict(self, label_dir: str):
        """
        text 파일로부터 현재 label dictionary를 불러옵니다
        """
        for file_name in os.listdir(label_dir):
            if file_name.endswith('.txt'):
                frame_number = int(os.path.splitext(file_name)[0])
                file_path = os.path.join(label_dir, file_name)
                try:
                    with open(file_path, "r") as f:
                        try:
                            label_data = json.load(f)
                            self.frame_label_dict[frame_number] = label_data
                        except json.JSONDecodeError as e:
                            print(f"Error decoding JSON in {file_path}: {e}")
                except FileNotFoundError:
                    print(f"File not found: {file_path}")

    def load_all_label(self):
        all_labels = set()
        for frame in self.frame_label_dict:
            all_labels.update(self.frame_label_check(frame))

        return all_labels

    def frame_label_check(self, frame) -> List[str]:
        """
        frame에 존재하는 라벨이름 리스트를 반환합니다.

        Args:
            frame(int): frame 번호

        Returns:
            label_list(list): 라벨명 리스트
        """
        drawing_types = ['rectangle', 'circle', 'line', 'freehand']
        frame_dict = self.frame_label_dict.get(frame, {})
        return [label for dt in drawing_types for label in frame_dict.get(dt, {})]

    def save_label(self, label_dir):
        print(self.frame_label_dict)
        for key in self.frame_label_dict:
            with open(f"{label_dir}/{key}.txt", 'w') as f:
                f.write(json.dumps(self.frame_label_dict[key]))

    def add_label(self, drawing_type, label_name, coords, color, frame_number):
        frame_dict = self.frame_label_dict.setdefault(frame_number, {})
        label_type_dict = frame_dict.setdefault(drawing_type, {})

        label_type_dict[label_name] = {'coords': coords, 'color': color}

    def delete_label_file(self, label_dir, file_name):
        try:
            os.remove(f"{label_dir}/{file_name}.txt")
        except FileNotFoundError:
            pass

    def delete_label(self, label_name: str, frame_number: int):
        """
        주어진 frame에서 해당하는 라벨이름을 가진 라벨을 frame_dict에서 제거합니다.
        """
        if frame_number in self.frame_label_dict:
            label_dict = self.frame_label_dict[frame_number]
            for label_data_dict in label_dict.values():
                label_data_dict.pop(label_name, None)
        print("라벨 정보 제거")

    def modify_label_data(self, frame_number, label_name, _coor, _color):
        """주어진 라벨 이름의 좌표값과 컬러값을 변경합니다.

        Args:
            label_name (string): 라벨 이름
            _coor (tuple): 객체의 좌표 정보
            _color (string or tuple): 컬러 값 (#ffffff)
        """
        frame_dict = self.frame_label_dict.get(frame_number, {})
        for label_data_dict in frame_dict.values():
            if label_name in label_data_dict:
                label_data_dict[label_name]['coords'] = _coor
                label_data_dict[label_name]['color'] = _color
                break

    def label_count(self, label_name):
        """
        모든 frame에 label_name 이름을 가진 label의 개수
        """
        return sum(1 for frame in self.frame_label_dict.values() for data in frame.values() if label_name in data)

    def get_frame_label_info(self, frame):
        frame_directory = self.frame_label_dict.get(frame, {})
        ret = []
        for drawing_type, label_directory in frame_directory.items():
            for label_name, label_data in label_directory.items():
                coords = label_data["coords"]
                color = label_data["color"]
                ret.append((drawing_type, label_name, coords, color))

        return ret

    def is_label_exist(self, label_name, frame_number):
        frame_labels = self.frame_label_check(frame_number)
        if label_name in frame_labels:
            return True
        return False

    def get_first_frame(self, label):
        for frame in self.frame_label_dict:
            if label in self.frame_label_check(frame):
                return True, frame
        return False, frame
