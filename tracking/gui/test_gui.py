from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QTimer
import copy
import cv2
import matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from matplotlib.figure import Figure
from functools import partial
import static.stylesheet as style
from controller.test_control import Controller
from data.data_manager import DataManager


class Gui(QMainWindow):
    def __init__(self, get):
        super().__init__()
        self.get = get
        self.initUI()

    def initUI(self):
        self.setWindowTitle("InsightMedi Viewer")
        self.setGeometry(100, 100, 1280, 720)    # 초기 window 위치, size

        # main widget
        self.main_widget = QWidget()
        self.main_widget.setStyleSheet(style.MAIN)
        self.setCentralWidget(self.main_widget)

        self.init_canvas()

        # label list
        self.label_layout = QVBoxLayout()
        self.set_buttons()

        # slider
        self.slider_layout = QHBoxLayout()
        self.slider = QSlider(Qt.Horizontal)
        self.slider_layout.addWidget(self.slider)

        # Frame label
        self.frame_label = QLabel("")
        self.frame_label.setStyleSheet(style.LIGHTFONT)
        self.slider_layout.addWidget(self.frame_label)

        # play button
        self.play_button = QPushButton("Play")
        self.play_button.setStyleSheet(style.PLAY_BUTTON)
        self.play_button.setFocusPolicy(Qt.NoFocus)

        # GUI Layout
        self.set_gui_layout()

        # 창 중앙 정렬
        screen_geometry = QApplication.desktop().availableGeometry()
        center_x = (screen_geometry.width() - self.width()) // 2
        center_y = (screen_geometry.height() - self.height()) // 2
        self.move(center_x, center_y)

        self.is_tracking = False
        self.video_status = None
        self.timer = None

        # Create a toolbar
        toolbar = self.addToolBar("Toolbar")

        # Create actions
        self.create_actions(toolbar)

    def init_canvas(self):
        self.canvas = FigureCanvas(Figure(figsize=(4, 3)))
        fig = self.canvas.figure
        ax = fig.add_subplot(111, aspect='auto')

        # canvas fig 색상 변경
        fig.patch.set_facecolor('#303030')
        ax.patch.set_facecolor("#3A3A3A")
        ax.axis("off")
        # self.ax.tick_params(axis = 'x', colors = 'gray')
        # self.ax.tick_params(axis = 'y', colors = 'gray')

    def init_instance_member(self):
        self.dm: DataManager = self.get('data')   # dcm_data.py의 DcmData()
        self.cl: Controller = self.get('control')  # control.py의 Controller()

    def closeEvent(self, event):
        # mainWindow종료시 할당된 메모리 해제하기
        self.release_resources()
        event.accept()

    def release_resources(self):
        # 동영상 플레이어 메모리 해제
        print("release resource start..")
        self.dm.reset_env()
        print("release resource end..")

    def set_frame_label(self):
        self.frame_label.setText(self.dm.get_frame_label_str())

    def open_file(self):
        # 파일 열기 기능 구현
        fname = QFileDialog.getOpenFileName(
            self, "Open File", "", "Video Files (*.mp4);;All Files (*)", options=QFileDialog.Options())

        if fname[0]:   # 새로운 파일 열기 한 경우
            self.reset_env()
            self.dm.open_file(fname)
            # viewer 설정 초기화
            self.load_label_button()

            if self.dm.file_mode == "mp4":
                self.init_mp4_ui()
            else:    # viewer에 호환되지 않는 확장자 파일
                print("Not accepted file format")
        else:
            print("Open fail")

    def reset_env(self):
        self.setCursor(Qt.ArrowCursor)
        self.disable_total_label()
        self.canvas.figure.clear()
        self.slider.setValue(0)   # slider value 초기화

    def init_mp4_ui(self):
        self.timer = QTimer()
        self.cl.img_show(self.dm.image, init=True)

        if self.dm.frame_label_check(self.dm.frame_number):
            self.cl.label_clicked(self.dm.frame_number)

        # slider 설정
        self.slider.setMaximum(dm.total_frame - 1)
        self.slider.setTickPosition(
            QSlider.TicksBelow)  # 눈금 위치 설정 (아래쪽)
        self.slider.setTickInterval(10)  # 눈금 간격 설정
        self.slider.valueChanged.connect(self.sliderValueChanged)
        self.play_button.clicked.connect(self.playButtonClicked)

    def load_label_button(self):
        # frame_label_dict에 있는 label 정보 버튼에 반영하기
        # open한 파일에 이미 저장되어 있는 label button 활성화하는 함수
        all_labels = self.dm.load_all_label()

        for label_name in self.buttons:
            temp_label_buttons = self.buttons[label_name]
            if label_name in all_labels:
                temp_label_buttons[0].setStyleSheet(style.BOLD_LABEL_BUTTON)
                temp_label_buttons[1].setStyleSheet(style.BOLD_GO_BUTTON)

        self.label_layout.update()
        self.set_frame_label()

    def label_button_clicked(self, label):
        button_list = self.buttons[label]
        # print(f"self.buttons : {self.buttons}")
        button_list[0].setStyleSheet(style.BOLD_LABEL_BUTTON)
        button_list[1].setStyleSheet(style.BOLD_GO_BUTTON)

        for frame in self.dm.frame_label_dict:
            frame_labels = self.dm.frame_label_check(frame)
            if frame_labels and label in frame_labels:
                self.dm.delete_label(label, frame)
                self.cl.erase_annotation(label)

        self.cl.is_tracking = False

        if self.cl.annotation_mode == "line":
            self.draw_straight_line(label)
        else:
            self.draw_rectangle(label)

    def go_button_clicked(self, label):
        found_label = False

        for frame in self.dm.frame_label_dict:
            labels = self.dm.frame_label_check(frame)
            if labels and label in labels:
                first_frame = frame
                found_label = True
                break

        if found_label:
            self.frame_label_show(first_frame, label)

    def frame_label_show(self, frame, label):
        # go 버튼 클릭시 frame값을 전달받고 이동 후 선택된 label은 두껍게 보여짐
        self.setCursor(Qt.ArrowCursor)
        if self.dm.file_mode == "mp4":
            self.dm.frame_number = frame
            self.slider.setValue(frame)

        self.cl.label_clicked(frame, label)

    def disable_total_label(self):
        # 해당 프레임에 있는 전체 label 버튼 비활성화
        button_list = self.buttons.values()
        for button in button_list:
            button[0].setStyleSheet(style.NORMAL_LABEL_BUTTON)
            button[1].setStyleSheet(style.NORMAL_GO_BUTTON)
        self.label_layout.update()

    def disable_label_button(self, _label_name):
        # 특정 label 버튼 볼드체 풀기 (비활성화)
        if _label_name in self.buttons:
            button_list = self.buttons[_label_name]
            button_list[0].setStyleSheet(
                "color: gray; font-weight: normal; height: 30px; width: 120px;")
            button_list[1].setStyleSheet(
                "color: gray; font-weight: normal; height: 30px; width: 50px;")
        else:
            print(f"{_label_name} 라벨에 대한 버튼을 찾을 수 없음")
        self.label_layout.update()

    def save(self):
        # 저장 기능 구현
        self.dm.save_label()
        print("Save...")

    def sliderValueChanged(self, value):
        # 슬라이더 값에 따라 frame 보여짐
        if not self.timer.isActive():    # 영상 재생 중인 경우
            self.dm.frame_number = value
            self.dm.video_player.set(
                cv2.CAP_PROP_POS_FRAMES, self.dm.frame_number)
            self.updateFrame()
        elif self.timer.isActive() and value != self.dm.frame_number:
            # 영상이 정지 중이거나 사용자가 slider value를 바꾼 경우
            self.dm.frame_number = value
            self.dm.video_player.set(
                cv2.CAP_PROP_POS_FRAMES, self.dm.frame_number)

    def playButtonClicked(self):
        # 영상 재생 버튼의 함수
        if not self.timer:    # timer 없으면 새로 생성하고 updateFrame을 callback으로 등록
            self.timer = self.canvas.new_timer(interval=16)  # 60FPS
            # self.timer.add_callback(self.updateFrame)

        if not self.timer.isActive():   # 재생 시작
            self.play_button.setText("Pause")
            self.timer.start()
            self.timer.timeout.connect(self.updateFrame)
            self.timer.start(16)
        else:    # 영상 정지
            self.play_button.setText("Play")
            self.timer.timeout.disconnect(self.updateFrame)
            self.set_frame_label()   # 현재 frame 상태 화면에 update
            self.timer.stop()
            self.dm.frame_number = int(
                self.dm.video_player.get(cv2.CAP_PROP_POS_FRAMES)) - 1

    def updateFrame(self):
        # frame update
        prev_frame = copy.deepcopy(self.dm.image)
        ret, frame = self.dm.video_player.read()
        if ret:
            self.dm.frame_number = int(
                self.dm.video_player.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            self.set_frame_label()  # 현재 frame 상태 화면에 update
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.cl.img_show(rgb_frame, clear=True)
            self.dm.image = rgb_frame
            # frame에 라벨이 존재하면 라벨을 보여줍니다.
            if self.is_tracking:
                self.cl.init_object_tracking(prev_frame, rgb_frame)
            if self.dm.frame_number in self.dm.frame_label_dict:
                self.cl.label_clicked(self.dm.frame_number)

            if self.timer.isActive():   # 영상 재생 중
                self.slider.setValue(self.dm.frame_number)

        print("update Frame 호출, 현재 frame: ", self.dm.frame_number)

    def selector(self):
        self.setCursor(Qt.ArrowCursor)
        self.cl.init_selector("selector")

    def draw_rectangle(self, label=None):
        if label or self.cl.selector_mode == "drawing":
            self.setCursor(Qt.CrossCursor)
            self.cl.init_draw_mode("rectangle", label)
        else:
            self.cl.annotation_mode = "rectangle"
            QMessageBox.information(
                self, 'Message', 'Click label button before drawing')

    def delete(self):
        self.cl.init_selector("delete")

    def delete_all(self):
        # print("erase")
        reply = QMessageBox.question(self, 'Message', 'Do you erase all?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.cl.erase_all_annotation()    # canvas 위에 그려진 label 삭제
            # self.disable_total_label()    # label 버튼 비활성화
            for label_name in self.dm.frame_label_check(self.dm.frame_number):
                self.cl.delete_label(label_name)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_T:
            print("t 키 눌림")
            if not self.is_tracking:
                self.is_tracking = True
                self.playButtonClicked()
            else:
                self.is_tracking = False
                self.playButtonClicked()

        elif event.key() == Qt.Key_Delete:
            print("delete 키 눌림")
            self.cl.remove_annotation()

        elif event.key() == Qt.Key_Escape:
            print('esc키 눌림')
            self.cl.select_off_all()

        if event.key() == Qt.Key_Space:
            print("space bar 눌림")
            self.playButtonClicked()

    def set_buttons(self):
        self.buttons = {}
        for i in range(8):
            button_layout = QHBoxLayout()
            label_name = "label %d" % (i + 1)
            label_button = QPushButton(label_name)
            label_button.setStyleSheet(style.NORMAL_LABEL_BUTTON)
            label_button.clicked.connect(
                partial(self.label_button_clicked, label_name))
            label_button.setFocusPolicy(Qt.NoFocus)

            go_button = QPushButton("GO")
            go_button.setStyleSheet(style.NORMAL_GO_BUTTON)
            go_button.clicked.connect(
                partial(self.go_button_clicked, label_name))
            go_button.setFocusPolicy(Qt.NoFocus)

            button_layout.addWidget(label_button)
            button_layout.addWidget(go_button)
            self.label_layout.addLayout(button_layout)

            label_go_buttons = [label_button, go_button]
            self.buttons[label_name] = label_go_buttons

    def set_gui_layout(self):
        grid_box = QGridLayout(self.main_widget)
        grid_box.setColumnStretch(0, 4)   # column 0 width 4
        # grid_box.setColumnStretch(1, 1)   # column 1 width 1

        # column 0
        grid_box.addWidget(self.canvas, 0, 0, 8, 1)
        grid_box.addLayout(self.slider_layout, 8, 0)

        # column 1
        # grid_box.addWidget(self.frame_label, 8, 1)

        # column 2
        grid_box.addLayout(self.label_layout, 0, 1)
        grid_box.addWidget(self.play_button, 1, 1)

    def create_actions(self, toolbar):
        # Open file action
        actions = ["open", "save", "selector", "rectangle", "delete", "clear"]
        func = [self.open_file, self.save, self.selector,
                self.draw_rectangle, self.delete, self.delete_all]
        icon_dir = 'gui/icon'
        pack = zip(actions, func)
        for x in pack:
            action = QAction(
                QIcon(f'{icon_dir}/{x[0]}_icon.png'), x[0].title(), self)
            action.triggered.connect(x[1])
            toolbar.addAction(action)
