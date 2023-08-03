from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QTimer

import cv2
import matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from matplotlib.figure import Figure

from gui.data.test_data import DcmData
from gui.controller.test_control import Controller
from functools import partial


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.timer = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("InsightMedi Viewer")
        self.setGeometry(100, 100, 1280, 720)    # 초기 window 위치, size

        self.main_widget = QWidget()
        self.main_widget.setStyleSheet("background-color: #303030;")

        self.setCentralWidget(self.main_widget)

        self.canvas = FigureCanvas(Figure(figsize=(4, 3)))

        self.dd = DcmData()    # dcm_data.py의 DcmData()
        # control.py의 Controller()
        self.cl = Controller(self.dd, self.canvas, self)

        # label list
        self.label_list = QWidget()
        self.label_layout = QVBoxLayout()
        self.label_list.setLayout(self.label_layout)
        self.buttons = {}

        for i in range(5):
            self.button_layout = QHBoxLayout()
            label_name = "label %d" % (i + 1)
            self.label_button = QPushButton(label_name)
            self.label_button.setStyleSheet(
                "color: gray; height: 30px; width: 120px;")
            self.label_button.clicked.connect(
                partial(self.label_button_clicked, label_name))

            self.go_button = QPushButton("GO")
            self.go_button.setStyleSheet(
                "color: gray; height: 30px; width: 50px;")
            self.go_button.clicked.connect(
                partial(self.go_button_clicked, label_name))

            self.button_layout.addWidget(self.label_button)
            self.button_layout.addWidget(self.go_button)
            self.label_layout.addLayout(self.button_layout)

            self.label_go_buttons = [self.label_button, self.go_button]
            self.buttons[label_name] = self.label_go_buttons

        # slider and play button
        self.slider = QSlider(Qt.Horizontal)
        self.play_button = QPushButton("Play")
        self.play_button.setStyleSheet("color: lightgray; height: 20px")
        self.video_status = None

        self.label_scroll_area = QScrollArea()
        self.label_scroll_area.setWidget(self.label_list)
        self.label_scroll_area.setWidgetResizable(True)

        # Frame label
        self.frame_label = QLabel("")
        self.frame_label.setStyleSheet("color: lightgray;")

        # GUI Layout
        grid_box = QGridLayout(self.main_widget)
        grid_box.setColumnStretch(0, 4)   # column 0 width 4
        grid_box.setColumnStretch(1, 1)   # column 1 width 1

        # column 0
        grid_box.addWidget(self.canvas, 0, 0, 8, 2)
        grid_box.addWidget(self.slider, 8, 0)

        # column 1
        grid_box.addWidget(self.frame_label, 8, 1)

        # column 2
        grid_box.addWidget(self.label_scroll_area, 0, 2, 5, 1)
        grid_box.addWidget(self.play_button, 5, 2)

        # 창 중앙 정렬
        screen_geometry = QApplication.desktop().availableGeometry()
        center_x = (screen_geometry.width() - self.width()) // 2
        center_y = (screen_geometry.height() - self.height()) // 2
        self.move(center_x, center_y)

        '''
        Toolbar
        '''

        # Create a toolbar
        toolbar = self.addToolBar("Toolbar")
        # toolbar.setStyleSheet("background-color: #3e3e3e;")

        # Open file action
        open_action = QAction(
            QIcon('gui/icon/open_file_icon.png'), "Open File", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)

        # Save file action
        save_action = QAction(QIcon('gui/icon/save_icon.png'), "Save", self)
        save_action.triggered.connect(self.save)
        toolbar.addAction(save_action)

        # Selector action
        cursor_action = QAction(
            QIcon('gui/icon/cursor_icon.png'), "Selector", self)
        cursor_action.triggered.connect(self.selector)
        toolbar.addAction(cursor_action)

        # Rectangle action
        rectangle_action = QAction(
            QIcon('gui/icon/rectangle_icon.png'), "Rectangle", self)
        rectangle_action.triggered.connect(self.draw_rectangle)
        toolbar.addAction(rectangle_action)

        # delete action
        delete_action = QAction(
            QIcon('gui/icon/delete_icon.png'), "Delete", self)
        delete_action.triggered.connect(self.delete)
        toolbar.addAction(delete_action)

        # delete all action
        delete_all_action = QAction(
            QIcon('gui/icon/delete_all_icon.png'), "Delete All", self)
        delete_all_action.triggered.connect(self.delete_all)
        toolbar.addAction(delete_all_action)

        self.is_tracking = False

    def closeEvent(self, event):
        # mainWindow종료시 할당된 메모리 해제하기
        self.release_resources()
        event.accept()

    def release_resources(self):
        # 동영상 플레이어 메모리 해제
        print("release resource")
        if self.dd.video_player:
            self.video_status = None
            self.dd.video_player.release()

    def set_frame_label(self, init=False):
        if init:
            frame = 0
        else:
            frame = self.dd.frame_number

        total_frame = int(self.dd.total_frame) - 1
        self.frame_label.setText(f"{frame} / {total_frame}")

    def open_file(self):
        # 파일 열기 기능 구현
        options = QFileDialog.Options()
        fname = QFileDialog.getOpenFileName(
            self, "Open File", "", "Video Files (*.mp4);;All Files (*)", options=options)

        if fname[0]:   # 새로운 파일 열기 한 경우
            # 기존 파일 정보 삭제
            self.setCursor(Qt.ArrowCursor)
            self.canvas.figure.clear()
            self.release_resources()
            self.slider.setValue(0)    # slider value 초기화

            # 파일 열기
            dd = self.dd
            dd.open_file(fname)

            # viewer 설정 초기화
            # open한 파일에 이미 저장되어 있는 label button 활성화하는 함수
            self.load_label_button(dd.frame_label_dict)
            self.set_frame_label(init=True)

            if dd.file_mode == "mp4":  # mp4 파일인 경우
                self.timer = QTimer()
                self.set_frame_label()

                self.cl.img_show(dd.image, cmap=plt.cm.gray, init=True)
                if self.dd.frame_label_check(self.dd.frame_number):
                    self.cl.label_clicked(self.dd.frame_number)

                # slider 설정
                self.slider.setMaximum(dd.total_frame - 1)
                self.slider.setTickPosition(
                    QSlider.TicksBelow)  # 눈금 위치 설정 (아래쪽)
                self.slider.setTickInterval(10)  # 눈금 간격 설정
                self.slider.valueChanged.connect(self.sliderValueChanged)
                self.play_button.clicked.connect(self.playButtonClicked)

            else:    # viewer에 호환되지 않는 확장자 파일
                print("Not accepted file format")
        else:
            print("Open fail")

    def load_label_button(self, ld):    # frame_label_dict에 있는 label 정보 버튼에 반영하기
        all_labels = set()
        for frame in ld:
            labels = self.dd.frame_label_check(frame)
            if labels:
                for label in labels:
                    all_labels.add(label)

        for label_name in self.buttons:
            temp_label_buttons = self.buttons[label_name]
            if label_name in all_labels:
                temp_label_buttons[0].setStyleSheet(
                    "color: white; font-weight: bold; height: 30px; width: 120px;")
                temp_label_buttons[1].setStyleSheet(
                    "color: white; font-weight: bold; height: 30px; width: 50px;")
            else:
                temp_label_buttons[0].setStyleSheet(
                    "color: gray; font-weight: normal; height: 30px; width: 120px;")
                temp_label_buttons[1].setStyleSheet(
                    "color: gray; font-weight: normal; height: 30px; width: 50px;")

        self.label_layout.update()

    def label_button_clicked(self, label):
        button_list = self.buttons[label]
        # print(f"self.buttons : {self.buttons}")
        button_list[0].setStyleSheet(
            "color: white; font-weight: bold; height: 30px; width: 120px;")
        button_list[1].setStyleSheet(
            "color: white; font-weight: bold; height: 30px; width: 50px;")

        for frame in self.dd.frame_label_dict:
            frame_labels = self.dd.frame_label_check(frame)
            if frame_labels and label in frame_labels:
                self.dd.delete_label(label, frame)
                self.cl.erase_annotation(label)
        
        self.is_tracking = False

        if self.cl.annotation_mode == "line":
            self.draw_straight_line(label)
        else:
            self.draw_rectangle(label)

    def go_button_clicked(self, label):
        found_label = False

        for frame in self.dd.frame_label_dict:
            labels = self.dd.frame_label_check(frame)
            if labels and label in labels:
                first_frame = frame
                found_label = True
                break

        if found_label:
            self.frame_label_show(first_frame, label)

    def frame_label_show(self, frame, label):
        # go 버튼 클릭시 frame값을 전달받고 이동 후 선택된 label은 두껍게 보여짐
        self.setCursor(Qt.ArrowCursor)
        if self.dd.file_mode == "mp4":
            self.dd.frame_number = frame
            self.slider.setValue(frame)
        
        self.cl.label_clicked(frame, label)

    """ def disable_total_label(self):
        # 해당 프레임에 있는 전체 label 버튼 비활성화
        frame_labels = self.dd.frame_label_check(self.dd.frame_number)
        if frame_labels:
            for _label_name in frame_labels:
                button_list = self.buttons[_label_name]
                button_list[0].setStyleSheet(
                    "color: gray; font-weight: normal; height: 30px; width: 120px;")
                button_list[1].setStyleSheet(
                    "color: gray; font-weight: normal; height: 30px; width: 50px;")
                self.dd.delete_label(_label_name)
            self.label_layout.update()

        # data에서 해당 라벨 이름 정보 제거하기
        self.dd.delete_label(_label_name) """

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
        self.dd.save_label()
        print("Save...")

    def sliderValueChanged(self, value):
        # 슬라이더 값에 따라 frame 보여짐
        if not self.timer.isActive():    # 영상 재생 중인 경우
            self.dd.frame_number = value
            self.dd.video_player.set(
                cv2.CAP_PROP_POS_FRAMES, self.dd.frame_number)
            self.updateFrame()
        elif self.timer.isActive() and value != self.dd.frame_number:
            # 영상이 정지 중이거나 사용자가 slider value를 바꾼 경우
            self.dd.frame_number = value
            self.dd.video_player.set(
                cv2.CAP_PROP_POS_FRAMES, self.dd.frame_number)

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
            self.dd.frame_number = int(
                self.dd.video_player.get(cv2.CAP_PROP_POS_FRAMES)) - 1

    def updateFrame(self):
        # frame update
        self.ret, self.frame = self.dd.video_player.read()
        if self.ret:
            self.dd.frame_number = int(
                self.dd.video_player.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            self.set_frame_label()  # 현재 frame 상태 화면에 update
            rgb_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            self.cl.img_show(rgb_frame, clear=True)

            # frame에 라벨이 존재하면 라벨을 보여줍니다.
            if self.dd.frame_number in self.dd.frame_label_dict:
                self.cl.label_clicked(self.dd.frame_number)

            if self.timer.isActive():   # 영상 재생 중
                self.slider.setValue(self.dd.frame_number)

        print("update Frame 호출, 현재 frame: ", self.dd.frame_number)

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
            #self.disable_total_label()    # label 버튼 비활성화
            for label_name in self.dd.frame_label_check(self.dd.frame_number):
                self.cl.delete_label(label_name)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_T:
            print("t 키 눌림")
            bbox = self.cl.check_bbox()   # object tracking이 가능한 상태인 지 확인하는 함수
            if bbox:
                try:
                    frame = self.frame
                except AttributeError:
                    frame = self.dd.frame
                
                self.slider.setValue(self.dd.frame_number + 1)   # 다음 frame으로 업데이트
                if not self.is_tracking:
                    # object tracking 한 결과 나온 라벨링 그리기
                    self.cl.object_tracking(frame, bbox, init=True)
                    self.is_tracking = True
                else:
                    # object tracking 한 결과 나온 라벨링 그리기
                    self.cl.object_tracking(frame, bbox)

        elif event.key() == Qt.Key_R:
            print("r 키 눌림")
            self.is_tracking = False

        elif event.key() == Qt.Key_Delete:
            print("delete 키 눌림")
            self.cl.remove_annotation()
        
        elif event.key() == Qt.Key_Escape:
            print('esc키 눌림')
            self.cl.select_off_all()
