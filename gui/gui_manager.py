from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QTimer
# import sys

from matplotlib.backends.backend_qt5agg import FigureCanvas as FigureCanvas
from matplotlib.figure import Figure
from functools import partial
import static.stylesheet as style
from controller.controller import Controller as ct
from data.data_manager import DataManager


class GuiManager(QMainWindow):
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

        self.canvas = FigureCanvas(Figure(figsize=(4, 3), facecolor="#303030"))

        # label list
        self.label_layout = QVBoxLayout()
        self.set_buttons()

        # slider
        self.slider_layout = QHBoxLayout()
        self.slider = QSlider(Qt.Horizontal)
        self.slider_layout.addWidget(self.slider)

        self.set_dcm_header_widget()
        # WW, WL label

        # Tool status label
        self.tool_status_label = QLabel("Tool Status: None")
        self.tool_status_label.setFixedHeight(20)
        self.tool_status_label.setStyleSheet(style.STATUS_LABEL)

        # status widget
        self.status_widget = QWidget()
        self.status_layout = QVBoxLayout()

        self.status_layout.addWidget(self.tool_status_label)

        self.status_widget.setLayout(self.status_layout)
        self.status_widget.setStyleSheet(style.STATUS_WIDGET)

        # Frame label
        self.frame_label = QLabel("")
        self.frame_label.setStyleSheet(style.LIGHTFONT)
        self.slider_layout.addWidget(self.frame_label)

        # play button
        self.play_button = QPushButton("Play")
        self.play_button.setStyleSheet(style.PLAY_BUTTON)
        self.play_button.setFocusPolicy(Qt.NoFocus)

        self.set_tracking_layout()

        self.tracking_active = False
        # timer
        self.timer = QTimer()
        self.timer_active = None
        # GUI Layout
        self.set_gui_layout()

        # 창 중앙 정렬
        screen_geometry = QApplication.desktop().availableGeometry()
        center_x = (screen_geometry.width() - self.width()) // 2
        center_y = (screen_geometry.height() - self.height()) // 2
        self.move(center_x, center_y)

        # Create a toolbar
        toolbar = self.addToolBar("Toolbar")

        # Create actions
        self.actions = self.create_actions(toolbar)

        # Create a status bar
        self.statusBar().showMessage("")

    def init_instance_member(self):
        self.dm: DataManager = self.get('data')   # dcm_data.py의 DcmData()
        self.cl: ct = self.get('control')  # control.py의 Controller()

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

    def set_window_label(self):
        wl_value, ww_value = self.dm.get_windwoing_value()
        self.wl_label.setText(f"WL: {wl_value}")
        self.ww_label.setText(f"WW: {ww_value}")

        self.windowing_layout.update()

    def set_tool_status_label(self):
        sm = self.cl.get_selector_mode()
        am = self.cl.get_annotation_mode()
        smam = f"Tool Status: {sm} ({am})" if am else f"Tool Status: {sm}"
        self.tool_status_label.setText(smam)

    def open_file(self):
        # 파일 열기 기능 구현
        fname = QFileDialog.getOpenFileName(
            self, "Open File", "", "DCM Files (*.dcm *.DCM);;Video Files (*.mp4);;All Files (*)",
            options=QFileDialog.Options())

        if fname[0]:   # 새로운 파일 열기 한 경우
            self.reset_env()
            self.dm.open_file(fname)
            # viewer 설정 초기화
            self.reset_viewer()

            if self.dm.file_mode == "mp4":
                self.init_mp4_ui()
            elif self.dm.file_mode == 'dcm':
                self.init_dcm_ui()
            else:    # viewer에 호환되지 않는 확장자 파일
                print("Not accepted file format")
        else:
            print("Open fail")

    def reset_env(self):
        self.setCursor(Qt.ArrowCursor)
        self.disable_total_label()
        try:
            self.disconnect_actions()
            self.disconnect_buttons()
        except TypeError:
            pass
        self.video_disconnect_func()
        self.canvas.figure.clear()
        self.slider.setValue(0)   # slider value 초기화
        self.cl.init_figure()

    def reset_viewer(self):
        self.load_label_button()
        self.connect_buttons()
        self.connect_actions()
        self.set_status_bar()
        self.set_tool_status_label()

    def video_disconnect_func(self):
        try:
            self.timer.timeout.disconnect(self.updateFrame)
            self.slider.valueChanged.disconnect(self.sliderValueChanged)
            self.play_button.clicked.disconnect(self.playButtonClicked)
            self.tracking_button.clicked.disconnect(self.trackingClicked)
        except TypeError:
            pass

    def video_connect_func(self):
        self.timer.timeout.connect(self.updateFrame)
        self.slider.valueChanged.connect(self.sliderValueChanged)
        self.play_button.clicked.connect(self.playButtonClicked)
        self.tracking_button.clicked.connect(self.trackingClicked)

    def init_dcm_ui(self):
        self.set_window_label()
        self.set_dcm_header_label()
        self.cl.init_dcm_show()
        self.selector()
        # slider 설정
        self.slider.setMaximum(0)

    def init_mp4_ui(self):
        self.hide_dcm_header_widget()
        self.video_connect_func()
        self.timer_active = False
        self.cl.frame_show(frame=self.dm.get_image())
        self.cl.init_annotation_ax()
        if self.dm.frame_label_check(0):
            self.cl.go_clicked(0)
        self.selector()

        # slider 설정
        self.slider.setMaximum(self.dm.get_total_frame_number() - 1)
        self.slider.setTickPosition(
            QSlider.TicksBelow)  # 눈금 위치 설정 (아래쪽)
        self.slider.setTickInterval(10)  # 눈금 간격 설정

    def load_label_button(self):
        # frame_label_dict에 있는 label 정보 버튼에 반영하기
        # open한 파일에 이미 저장되어 있는 label button 활성화하는 함수
        all_labels = self.dm.load_all_label()
        for label_name in self.buttons:
            if label_name in all_labels:
                self.activate_buttons(label_name)

        self.label_layout.update()
        self.set_frame_label()

    def label_button_clicked(self, label):
        # GUI에서 모든 프레임에 라벨이 1개만 존재하면 버튼 비활성화
        self.activate_buttons(label)
        self.cl.label_button_clicked(label)
        self.draw_rectangle(label)

    def go_button_clicked(self, label):
        found, frame = self.dm.get_first_frame(label)
        if found:
            self.frame_label_show(frame, label)

    def frame_label_show(self, frame, label):
        # go 버튼 클릭시 frame값을 전달받고 이동 후 선택된 label은 두껍게 보여짐
        self.setCursor(Qt.ArrowCursor)
        if self.dm.file_mode == "mp4":
            self.slider.setValue(frame)
        self.cl.go_clicked(frame, label)

    def disable_total_label(self):
        # 전체 label 버튼 비활성화
        for label_name in self.buttons:
            self.deactivate_button(label_name)

    def deactivate_button(self, label_name):
        # 특정 label 버튼 볼드체 풀기 (비활성화)
        button_list = self.buttons.get(label_name, None)
        if button_list:
            normal_label_button, normal_go_button = button_list
            normal_label_button.setStyleSheet(style.NORMAL_LABEL_BUTTON)
            normal_go_button.setStyleSheet(style.NORMAL_GO_BUTTON)
        else:
            print(f"{label_name} 라벨에 대한 버튼을 찾을 수 없음")
        self.label_layout.update()

    def activate_buttons(self, label_name):
        # 특정 label 버튼 볼드체 풀기 (비활성화)
        button_list = self.buttons.get(label_name, None)
        if button_list:
            normal_label_button, normal_go_button = button_list
            normal_label_button.setStyleSheet(style.BOLD_LABEL_BUTTON)
            normal_go_button.setStyleSheet(style.BOLD_GO_BUTTON)
        else:
            print(f"{label_name} 라벨에 대한 버튼을 찾을 수 없음")
        self.label_layout.update()

    def save(self):
        # 저장 기능 구현
        self.dm.save_label()
        print("Save...")

    def start_timer(self):
        if not self.timer_active:
            self.timer_active = True
            self.timer.start(16)

    def stop_timer(self):
        if self.timer_active:
            self.timer_active = False
            self.timer.stop()

    def sliderValueChanged(self, value):
        # 슬라이더 값에 따라 frame 보여짐
        if not self.timer_active and self.dm.get_frame_number() != value:
            # 영상이 정지 중이거나 사용자가 slider value를 바꾼 경우
            self.dm.set_frame(value)
            self.updateFrame()
        # elif self.timer_active and self.dm.get_frame_number() != value:
        #     # 영상 재생 중인 경우
        #     self.dm.set_frame(value)

    def playButtonClicked(self):
        # 영상 재생 버튼의 함수
        # self.selector()
        print("play button clicked")
        if not self.timer_active:   # 재생 시작
            self.play_button.setText("Pause")
            self.start_timer()
        else:    # 영상 정지
            self.play_button.setText("Play")
            self.stop_timer()

    def updateFrame(self):
        # frame update
        if self.dm.is_last_frame():
            self.playButtonClicked()
            return
        ret, frame_number = self.cl.update_frame(self.tracking_active)
        if ret:
            self.set_frame_label()  # 현재 frame 상태 화면에 update
            if self.timer_active:   # 영상 재생 중
                self.slider.setValue(frame_number)

    def windowing(self):
        self.setCursor(Qt.OpenHandCursor)
        self.cl.init_windowing_mode()
        self.set_tool_status_label()

    def selector(self):
        self.setCursor(Qt.ArrowCursor)
        self.cl.init_selector("selector")
        self.set_tool_status_label()

    def get_empty_label(self):
        for key, buttons in self.buttons.items():
            if 'normal' in buttons[0].styleSheet():
                self.activate_buttons(key)
                return key
        return None

    def draw_shape(self, shape_type, label):
        label = label or self.cl.get_label_name() or self.get_empty_label()
        self.setCursor(Qt.CrossCursor)
        self.cl.init_draw_mode(shape_type, label)
        self.set_tool_status_label()

    def draw_rectangle(self, label=None):
        self.draw_shape("rectangle", label)

    def draw_line(self, label=None):
        self.draw_shape("line", label)

    def draw_circle(self, label=None):
        self.draw_shape("circle", label)

    def draw_freehand(self, label=None):
        self.draw_shape("freehand", label)

    def delete(self):
        self.setCursor(Qt.PointingHandCursor)
        self.cl.init_selector("delete")
        self.set_tool_status_label()

    def delete_all(self):
        # print("erase")
        reply = QMessageBox.question(self, 'Message', 'Do you erase all?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.setCursor(Qt.ArrowCursor)
            self.cl.erase_all_annotation()    # canvas 위에 그려진 label 삭제
            # self.disable_total_label()    # label 버튼 비활성화
            for label_name in self.dm.frame_label_check(self.dm.get_frame_number()):
                if self.dm.label_count(label_name) == 1:
                    self.deactivate_button(label_name)
                self.cl.delete_label(label_name)
            self.set_tool_status_label()

    def zoom_in(self):
        self.cl.init_zoom_mode("in")
        self.cl.zoom(0.9)
        self.set_tool_status_label()

    def zoom_out(self):
        self.cl.init_zoom_mode("out")
        self.cl.zoom(1.1)
        self.set_tool_status_label()

    def trackingClicked(self):
        input_frame_value = self.dm.get_tracking_num(
            self.tracking_textbox.text())
        print("object tracking 실행될 frame 수", input_frame_value)
        self.clear_focus()
        if not self.tracking_active:
            self.cl.start_tracking_status()
            self.tracking_active = True
            self.tracking_button.setStyleSheet(style.START_TRACKING)
            self.update_object_tracking(input_frame_value)
        else:
            self.cl.stop_tracking_status()
            self.tracking_active = False
            self.tracking_button.setStyleSheet(style.TRACKING_BUTTON)

    def update_object_tracking(self, input_frame_value):
        for _ in range(input_frame_value):
            print("실행되고 있냐...", self.tracking_active)
            if self.tracking_active:
                self.updateFrame()
                self.slider.setValue(self.dm.get_frame_number())
                QApplication.processEvents()
            else:
                self.cl.stop_tracking_status()
                self.tracking_active = False
                self.tracking_button.setStyleSheet(style.TRACKING_BUTTON)
                break

    def clear_focus(self):
        self.tracking_textbox.clearFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_T:
            print("t 키 눌림")
            if self.dm.file_mode == 'mp4':
                self.trackingClicked()

        if event.key() == Qt.Key_Delete:
            print("delete 키 눌림")
            for label_name in self.cl.remove_annotation():
                if self.dm.label_count(label_name) == 1:
                    self.deactivate_button(label_name)

        elif event.key() == Qt.Key_Escape:
            print('esc키 눌림')
            self.cl.select_off_all()
            self.clear_focus()
            self.selector()

        if event.key() == Qt.Key_Space:
            print("space bar 눌림")
            if self.dm.file_mode == 'mp4':
                self.playButtonClicked()

    def set_buttons(self):
        self.buttons = {}
        for i in range(8):
            label_name = f"label {i + 1}"

            label_button = self.create_button(
                label_name, style.NORMAL_LABEL_BUTTON,)
            go_button = self.create_button("GO", style.NORMAL_GO_BUTTON)

            button_layout = self.create_button_layout(label_button, go_button)
            self.label_layout.addLayout(button_layout)

            self.buttons[label_name] = [label_button, go_button]

    def create_button(self, label, style_sheet):
        button = QPushButton(label)
        button.setStyleSheet(style_sheet)
        button.setFocusPolicy(Qt.NoFocus)
        return button

    def connect_buttons(self):
        for label_name, buttons in self.buttons.items():
            buttons[0].clicked.connect(
                partial(self.label_button_clicked, label_name))
            buttons[1].clicked.connect(
                partial(self.go_button_clicked, label_name))

    def disconnect_buttons(self):
        for label_name, buttons in self.buttons.items():
            buttons[0].clicked.disconnect(
                partial(self.label_button_clicked, label_name))
            buttons[1].clicked.disconnect(
                partial(self.go_button_clicked, label_name))

    def create_textbox(self, validator, style_sheet):
        textbox = QLineEdit()
        textbox.setValidator(validator)
        textbox.setStyleSheet(style_sheet)
        return textbox

    def create_button_layout(self, *buttons):
        layout = QHBoxLayout()
        layout.addStretch()
        for button in buttons:
            layout.addWidget(button)
        return layout

    def set_gui_layout(self):
        grid_box = QGridLayout(self.main_widget)
        grid_box.setColumnStretch(1, 4)   # column 0 width 4
        grid_box.setColumnStretch(2, 1)   # column 1 width 1

        # column 0
        grid_box.addWidget(self.dcm_header_widget, 0, 0)

        # column 1
        grid_box.addWidget(self.canvas, 0, 1, 8, 1)
        grid_box.addLayout(self.slider_layout, 8, 1)

        # column 2
        grid_box.addLayout(self.label_layout, 0, 2)
        grid_box.addWidget(self.play_button, 1, 2)
        grid_box.addLayout(self.tracking_layout, 2, 2)
        grid_box.addWidget(self.status_widget, 3, 2)
        self.grid_box = grid_box
        self.hide_dcm_header_widget()

    def set_status_bar(self):
        file_path = self.dm.get_file_path()
        self.statusBar().showMessage(file_path)

    def create_actions(self, toolbar):
        actions = ["open", "save", "selector", "windowing", "line",
                   "rectangle", "circle", "freehand",
                   "zoomin", "zoomout", "delete", "clear"]

        icon_dir = 'gui/icon'
        ret_actions = []
        for act in actions:
            action = QAction(
                QIcon(f'{icon_dir}/{act}_icon.png'), act.title(), self)
            if act == "open":
                action.triggered.connect(self.open_file)
            else:
                ret_actions.append(action)
            toolbar.addAction(action)
        return ret_actions

    def connect_actions(self):
        func = [self.save, self.selector, self.windowing, self.draw_line,
                self.draw_rectangle, self.draw_circle, self.draw_freehand,
                self.zoom_in, self.zoom_out, self.delete, self.delete_all]
        for action, fun in zip(self.actions, func):
            action.triggered.connect(fun)

    def disconnect_actions(self):
        func = [self.save, self.selector, self.windowing, self.draw_line,
                self.draw_rectangle, self.draw_circle, self.draw_freehand,
                self.zoom_in, self.zoom_out, self.delete, self.delete_all]
        for action, fun in zip(self.actions, func):
            action.triggered.disconnect(fun)

    def set_tracking_layout(self):
        self.tracking_layout = QHBoxLayout()

        self.tracking_button = self.create_button(
            "Tracking", style.TRACKING_BUTTON)
        self.tracking_layout.addWidget(self.tracking_button)

        self.tracking_textbox = self.create_textbox(
            QIntValidator(1, 100, self), style.LIGHTFONT)
        self.tracking_layout.addWidget(self.tracking_textbox)

    def create_dcm_label(self, label_name):

        label = QLabel(label_name)
        label.setFixedHeight(20)
        label.setStyleSheet(style.WINDOWING_LABEL)

        info = QLabel("    ")
        info.setFixedHeight(20)
        info.setStyleSheet(style.WINDOWING_LABEL)

        return label, info

    def set_dcm_header_widget(self):
        self.dcm_header_widget = QWidget()

        self.dcm_header_layout = QGridLayout()
        self.meta = ["Patient Name", "PatientID", "Patient Birth Date", "Patient Sex",
                     "Patient Age", "Patient Weight", "Patient Address", "Study Date",
                     "Study Time", "Study ID", "Study Modality", "Study Description",
                     "Series Date", "Series Time", "Series Description"]
        for i, mt in enumerate(self.meta):
            name, info = self.create_dcm_label(mt)
            self.dcm_header_layout.addWidget(name, i, 0)
            self.dcm_header_layout.addWidget(info, i, 1)

        self.dcm_header_layout.setSpacing(10)
        self.set_windowing_label()
        self.dcm_header_layout.addWidget(self.wl_label, len(self.meta) + 1, 0)
        self.dcm_header_layout.addWidget(self.ww_label, len(self.meta) + 1, 1)

        self.dcm_header_widget.setLayout(self.dcm_header_layout)
        self.dcm_header_widget.setStyleSheet(style.STATUS_WIDGET)

    def set_windowing_label(self):
        self.windowing_layout = QHBoxLayout()

        self.wl_label = QLabel("WL:")
        self.wl_label.setFixedHeight(20)
        self.wl_label.setStyleSheet(style.WINDOWING_LABEL)

        self.ww_label = QLabel("WW:")
        self.ww_label.setFixedHeight(20)
        self.ww_label.setStyleSheet(style.WINDOWING_LABEL)

        self.windowing_layout.addWidget(self.wl_label)
        self.windowing_layout.addWidget(self.ww_label)

    def hide_dcm_header_widget(self):
        self.dcm_header_widget.hide()

    def set_dcm_header_label(self):
        value = self.dm.get_dcm_meta(self.meta)
        for i, v in enumerate(value):
            self.dcm_header_layout.itemAtPosition(
                i, 1).widget().setText(str(v))
        self.dcm_header_layout.update()
        self.dcm_header_widget.show()
