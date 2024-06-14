from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QFileDialog, \
    QMessageBox, QLabel, QListWidget, QListWidgetItem, QStyledItemDelegate, QStyle, QStyleOptionButton, QLineEdit
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import Qt, QUrl, QTimer, QRect, QSize, QEvent
from PyQt5.QtGui import QPainter, QColor, QFont, QIcon
import sys
import json
import random


class PlaylistItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()

        if option.state & QStyle.State_Selected:
            painter.setBrush(QColor(60, 60, 60))
        else:
            painter.setBrush(QColor(40, 40, 40))
        painter.drawRect(option.rect)

        file_path = index.data()
        file_name = file_path.split('/')[-1]
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont('Arial', 12))
        text_rect = QRect(option.rect.left() + 10, option.rect.top() + 5, option.rect.width() - 50, option.rect.height() - 10)
        painter.drawText(text_rect, Qt.AlignVCenter, file_name)

        delete_button_rect = QRect(option.rect.right() - 40, option.rect.top() + 5, 30, 30)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(200, 0, 0))
        painter.drawEllipse(delete_button_rect)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(delete_button_rect, Qt.AlignCenter, '❌')

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            mouse_event = event
            delete_button_rect = QRect(option.rect.right() - 40, option.rect.top() + 5, 30, 30)
            if delete_button_rect.contains(mouse_event.pos()):
                file_path = index.data()
                model.removeRow(index.row())
                QApplication.instance().player.removeTrackFromPlaylist(file_path)
                return True
        return super().editorEvent(event, model, option, index)

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 40)


class AudioPlayer(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Музыкальный проигрыватель")
        self.setFixedSize(800, 600)
        self.setWindowIcon(QIcon('player.ico'))
        self.setStyleSheet("background-color: #282828; color: white;")
        QApplication.instance().player = self
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.StreamPlayback)
        self.playlist = []

        layout = QVBoxLayout()

        self.playlistWidget = QListWidget()
        self.playlistWidget.setAutoScroll(True)
        self.playlistWidget.setStyleSheet("background-color: #404040; color: white;")
        self.playlistWidget.setItemDelegate(PlaylistItemDelegate(self.playlistWidget))
        self.playlistWidget.itemDoubleClicked.connect(self.playSelectedAudio)
        self.playlistWidget.setMinimumHeight(400)
        layout.addWidget(self.playlistWidget)

        controlLayout = QHBoxLayout()

        button_style = """
                    QPushButton {
                        background-color: #404040;
                        color: white;
                        border: 1px solid black;
                        border-radius: 10px;
                        padding: 8px;
                    }
                    QPushButton:hover {
                        background-color: #606060;
                    }
                    QPushButton:pressed {
                        background-color: #808080;
                    }
        """
        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText("Найти песню...")
        self.searchBar.textChanged.connect(self.filterPlaylist)
        self.searchBar.setStyleSheet("""
                   QLineEdit {
                       border: 2px solid #4F4F4F;
                       border-radius: 10px;
                       padding: 5px;
                       font-size: 16px;
                       color: #FFFFFF;
                       background-color: #333333;
                       min-height: 40px;  
                   }
                   QLineEdit:focus {
                       border: 2px solid #0078D7;  
                   }
               """)
        self.searchBar.setMinimumWidth(300)
        layout.addWidget(self.searchBar)

        self.openButton = QPushButton("Открыть")
        self.openButton.clicked.connect(self.openAudio)
        self.openButton.setStyleSheet(button_style)
        controlLayout.addWidget(self.openButton)

        self.playButton = QPushButton("▶️")
        self.playButton.clicked.connect(self.playPauseAudio)
        self.playButton.setStyleSheet(button_style)
        controlLayout.addWidget(self.playButton)

        self.stopButton = QPushButton("⏹")
        self.stopButton.clicked.connect(self.stopAudio)
        self.stopButton.setStyleSheet(button_style)
        controlLayout.addWidget(self.stopButton)

        self.shuffleButton = QPushButton("🔀")
        self.shuffleButton.clicked.connect(self.shufflePlaylist)
        self.shuffleButton.setStyleSheet(button_style)
        controlLayout.addWidget(self.shuffleButton)

        self.repeatButton = QPushButton("🔁")
        self.repeatButton.setCheckable(True)
        self.repeatButton.clicked.connect(self.toggleRepeatMode)
        self.repeatButton.setStyleSheet(button_style)
        controlLayout.addWidget(self.repeatButton)

        self.prevButton = QPushButton("⏮")
        self.prevButton.clicked.connect(self.prevAudio)
        self.prevButton.setStyleSheet(button_style)
        controlLayout.addWidget(self.prevButton)

        self.nextButton = QPushButton("⏭")
        self.nextButton.clicked.connect(self.nextAudio)
        self.nextButton.setStyleSheet(button_style)
        controlLayout.addWidget(self.nextButton)

        self.muteButton = QPushButton("🔊")
        self.muteButton.clicked.connect(self.muteUnmute)
        self.muteButton.setStyleSheet(button_style)
        controlLayout.addWidget(self.muteButton)

        self.volumeSlider = QSlider(Qt.Horizontal)
        self.volumeSlider.setMinimum(0)
        self.volumeSlider.setMaximum(100)
        self.volumeSlider.setValue(50)
        self.volumeSlider.valueChanged.connect(self.setVolume)
        self.volumeSlider.setStyleSheet("QSlider {width: 100px; height: 15px;}")
        controlLayout.addWidget(self.volumeSlider)


        layout.addLayout(controlLayout)

        self.seekSlider = QSlider(Qt.Horizontal)
        self.seekSlider.setRange(0, 0)
        self.seekSlider.sliderMoved.connect(self.setPosition)
        layout.addWidget(self.seekSlider)

        timerLayout = QHBoxLayout()

        self.timerLabel = QLabel("00:00")
        self.timerLabel.setAlignment(Qt.AlignCenter)
        timerLayout.addWidget(self.timerLabel)

        self.durationLabel = QLabel("Длительность: 00:00")
        self.durationLabel.setAlignment(Qt.AlignCenter)
        timerLayout.addWidget(self.durationLabel)

        layout.addLayout(timerLayout)

        self.setLayout(layout)

        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTimer)
        self.timer.start(1000)

        self.repeatMode = 0
        self.mediaPlayer.stateChanged.connect(self.checkRepeat)

        self.json_playlist_file = 'playlist.json'
        self.loadPlaylist()

    def filterPlaylist(self, text):
        self.playlistWidget.clear()
        for file in self.playlist:
            if text.lower() in file.lower().split('/')[-1]:
                self.addPlaylistItem(file)
    def openAudio(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Открыть", "",
                                                "Audio Files (*.mp3 *.wav *.ogg *.flac *.aac)")
        if files:
            for file in files:
                if file not in self.playlist:
                    self.playlist.append(file)
                    self.addPlaylistItem(file)
            if self.mediaPlayer.state() != QMediaPlayer.PlayingState:
                self.playAudio(self.playlist[0])
            self.savePlaylist()

    def removeTrackFromPlaylist(self, file_path):
        if file_path in self.playlist:
            self.playlist.remove(file_path)
            self.savePlaylist()
    def loadPlaylist(self):
        try:
            with open(self.json_playlist_file, 'r') as file:
                self.playlist = json.load(file)
            for file in self.playlist:
                self.addPlaylistItem(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.playlist = []

    def savePlaylist(self):
        with open(self.json_playlist_file, 'w') as file:
            json.dump(self.playlist, file)

    def addPlaylistItem(self, file):
        item = QListWidgetItem(file)
        self.playlistWidget.addItem(item)

    def playSelectedAudio(self, item):
        file = item.text()
        self.playAudio(file)

    def playPauseAudio(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
            self.playButton.setText("▶️")
        else:
            self.mediaPlayer.play()
            self.playButton.setText("⏸")

    def prevAudio(self):
        current_index = self.playlistWidget.currentRow()
        if current_index > 0:
            prev_index = current_index - 1
            self.playlistWidget.setCurrentRow(prev_index)
            self.playSelectedAudio(self.playlistWidget.item(prev_index))

    def nextAudio(self):
        current_index = self.playlistWidget.currentRow()
        if current_index < self.playlistWidget.count() - 1:
            next_index = current_index + 1
            self.playlistWidget.setCurrentRow(next_index)
            self.playSelectedAudio(self.playlistWidget.item(next_index))

    def stopAudio(self):
        self.mediaPlayer.stop()

    def setVolume(self, value):
        self.mediaPlayer.setVolume(value)
        self.updateMuteButtonIcon(value)

    def updateMuteButtonIcon(self, volume):
        if self.mediaPlayer.isMuted() or volume == 0:
            self.muteButton.setText("🔇")
        elif volume < 30:
            self.muteButton.setText("🔈")
        elif volume < 70:
            self.muteButton.setText("🔉")
        else:
            self.muteButton.setText("🔊")

    def muteUnmute(self):
        if self.mediaPlayer.isMuted():
            self.mediaPlayer.setMuted(False)
            self.updateMuteButtonIcon(self.mediaPlayer.volume())
        else:
            self.mediaPlayer.setMuted(True)
            self.muteButton.setText("🔇")

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def positionChanged(self, position):
        self.seekSlider.setValue(position)
        self.updateDurationLabel()

    def durationChanged(self, duration):
        self.seekSlider.setRange(0, duration)
        self.updateDurationLabel()

    def playAudio(self, file):
        try:
            url = QUrl.fromLocalFile(file)
            content = QMediaContent(url)
            self.mediaPlayer.setMedia(content)
            self.mediaPlayer.play()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не могу проиграть аудио: {e}")

    def shufflePlaylist(self):
        if self.playlist:
            random.shuffle(self.playlist)
            self.updatePlaylistUI()
            self.savePlaylist()
            self.playlistWidget.setCurrentRow(0)
            self.playSelectedAudio(self.playlistWidget.item(0))

    def updatePlaylistUI(self):
        self.playlistWidget.clear()
        for file in self.playlist:
            self.addPlaylistItem(file)

    def toggleRepeatMode(self):
        self.repeatMode += 1
        if self.repeatMode > 2:
            self.repeatMode = 0

        if self.repeatMode == 0:
            self.repeatButton.setText("🔁") #Зациклить
        elif self.repeatMode == 1:
            self.repeatButton.setText("🔂")  #Повторить все песни
        elif self.repeatMode == 2:
            self.repeatButton.setText("🔁1")  #Повторить один раз

    def checkRepeat(self, state):
        if state == QMediaPlayer.StoppedState and self.repeatMode != 0:
            if self.repeatMode == 1:
                current_index = self.playlistWidget.currentRow()
                next_index = (current_index + 1) % self.playlistWidget.count()
                self.playlistWidget.setCurrentRow(next_index)
                self.playSelectedAudio(self.playlistWidget.item(next_index))
            elif self.repeatMode == 2:
                self.mediaPlayer.play()

    def handleError(self):
        error = self.mediaPlayer.errorString()
        QMessageBox.critical(self, "Ошибка", f"Ошибка аудиоплеера: {error}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super(AudioPlayer, self).keyPressEvent(event)

    def updateTimer(self):
        if self.mediaPlayer.duration() > 0:
            current_time = self.mediaPlayer.position() / 1000
            duration = self.mediaPlayer.duration() / 1000
            self.timerLabel.setText("{}/{}".format(self.formatTime(current_time), self.formatTime(duration)))

    def updateDurationLabel(self):
        if self.mediaPlayer.duration() > 0:
            duration = self.mediaPlayer.duration() / 1000
            self.durationLabel.setText("Длительность: {}".format(self.formatTime(duration)))

    def formatTime(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%02d:%02d:%02d" % (h, m, s)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = AudioPlayer()
    player.show()
    sys.exit(app.exec_())