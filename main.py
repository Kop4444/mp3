import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QSlider
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent
from PyQt5.QtCore import QUrl, QFileInfo, Qt, QTimer


class MusicPlayer(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Музыкальный проигрыватель")
        self.setGeometry(100, 100, 400, 250)

        self.layout = QVBoxLayout()

        self.player = QMediaPlayer()
        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)

        self.player.stateChanged.connect(self.print_state)

        self.btn_select_files = QPushButton("Выбрать аудиофайл(ы)")
        self.btn_select_files.clicked.connect(self.select_files)
        self.layout.addWidget(self.btn_select_files)

        self.btn_play = QPushButton("▶️")
        self.btn_play.clicked.connect(self.play)
        self.btn_play.setStyleSheet("font-size: 24px;")
        self.layout.addWidget(self.btn_play)

        self.btn_pause = QPushButton("❚❚")
        self.btn_pause.clicked.connect(self.player.pause)
        self.btn_pause.setStyleSheet("font-size: 12px;")
        self.layout.addWidget(self.btn_pause)

        self.btn_forward = QPushButton("+ 10")
        self.btn_forward.clicked.connect(self.forward)
        self.layout.addWidget(self.btn_forward)

        self.btn_backward = QPushButton("- 10")
        self.btn_backward.clicked.connect(self.backward)
        self.layout.addWidget(self.btn_backward)

        self.btn_next_track = QPushButton(">")
        self.btn_next_track.clicked.connect(self.next_track)
        self.layout.addWidget(self.btn_next_track)

        self.btn_previous_track = QPushButton("<")
        self.btn_previous_track.clicked.connect(self.previous_track)
        self.layout.addWidget(self.btn_previous_track)

        self.slider_volume = QSlider(Qt.Horizontal)
        self.slider_volume.setMinimum(0)
        self.slider_volume.setMaximum(100)
        self.slider_volume.setValue(50)
        self.slider_volume.setTickInterval(10)
        self.slider_volume.setTickPosition(QSlider.TicksBelow)
        self.slider_volume.sliderMoved.connect(self.change_volume)
        self.layout.addWidget(self.slider_volume)

        self.label_status = QLabel()
        self.label_status.setStyleSheet("font-size: 18px;")
        self.layout.addWidget(self.label_status)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)

        self.setLayout(self.layout)

    def select_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Выберите аудиофайлы", "", "Audio Files (*.mp3)")
        if file_paths:
            for file_path in file_paths:
                if QFileInfo(file_path).exists():
                    self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
                    self.label_status.setText("Выбрано файлов: " + str(self.playlist.mediaCount()))
                else:
                    self.label_status.setText("Файлы не найдены")

    def play(self):
        if self.player.state() == QMediaPlayer.StoppedState:
            self.player.play()
            self.timer.start(1000)
        else:
            self.player.play()

    def stop(self):
        self.player.stop()
        self.timer.stop()

    def backward(self):
        self.player.setPosition(self.player.position() - 10000)

    def forward(self):
        self.player.setPosition(self.player.position() + 10000)

    def previous_track(self):
        self.playlist.previous()

    def next_track(self):
        self.playlist.next()

    def change_volume(self):
        volume = self.slider_volume.value()
        self.player.setVolume(volume)

    def update_time(self):
        current_time = self.player.position() / 1000
        self.label_status.setText(f"Прошло времени: {current_time} сек")

    def print_state(self, state):
        print("Состояние проигрывателя изменилось:", state)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec_())