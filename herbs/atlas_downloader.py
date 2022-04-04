import urllib.request

import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import queue
import requests


# class GeeksforGeeks(QWidget):
#
#     def __init__(self):
#         super().__init__()
#
#         # calling a defined method to initialize UI
#         self.init_UI()
#
#     # method for creating UI widgets
#     def init_UI(self):
#         # creating progress bar
#         self.progressBar = QProgressBar(self)
#
#         # setting its size
#         self.progressBar.setGeometry(25, 45, 210, 30)
#
#         # creating push button to start download
#         self.button = QPushButton('Start', self)
#
#         # assigning position to button
#         self.button.move(50, 100)
#
#         # assigning activity to push button
#         self.button.clicked.connect(self.Download)
#
#         # setting window geometry
#         self.setGeometry(310, 310, 280, 170)
#
#         # setting window action
#         self.setWindowTitle("GeeksforGeeks")
#
#         # showing all the widgets
#         self.show()
#
#     # when push button is pressed, this method is called
#     def Handle_Progress(self, blocknum, blocksize, totalsize):
#         ## calculate the progress
#         readed_data = blocknum * blocksize
#
#         if totalsize > 0:
#             download_percentage = readed_data * 100 / totalsize
#             self.progressBar.setValue(download_percentage)
#             QApplication.processEvents()
#
#     # method to download any file using urllib
#     def Download(self):
#         # specify the url of the file which is to be downloaded
#         down_url = "https://www.nitrc.org/frs/download.php/12261/WHS_SD_rat_atlas_v4.label"
#
#         # specify save location where the file is to be saved
#         save_loc = str(QFileDialog.getExistingDirectory(self, "Select Folder to Save Atlas"))
#
#         # Downloading using urllib
#         if save_loc != '':
#             urllib.request.urlretrieve(down_url, save_loc, self.Handle_Progress)
#
#
# # main method to call our app
# if __name__ == '__main__':
#     # create app
#     App = QApplication(sys.argv)
#
#     # create the instance of our window
#     window = GeeksforGeeks()
#
#     # start the app
#     sys.exit(App.exec())


class DownloadThread(QThread):
    download_proess_signal = pyqtSignal(int)

    def __init__(self, url, filesize, fileobj, buffer):
        super(DownloadThread, self).__init__()
        self.url = url
        self.filesize = filesize
        self.fileobj = fileobj
        self.buffer = buffer

    def run(self):
        try:
            rsp = requests.get(self.url, stream=True)
            offset = 0
            for chunk in rsp.iter_content(chunk_size=self.buffer):
                if not chunk: break
                self.fileobj.seek(offset)
                self.fileobj.write(chunk)
                offset = offset + len(chunk)
                proess = offset / int(self.filesize) * 100
                self.download_proess_signal.emit(int(proess))
            self.fileobj.close()
            self.exit(0)

        except Exception as e:
            print(e)


class AtlasDownloader(QDialog):
    def __init__(self, *args, **kwargs):
        super(AtlasDownloader, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(self)

        self.setWindowTitle("Atlas Downloader")

        self.label_url = "https://www.nitrc.org/frs/download.php/12261/WHS_SD_rat_atlas_v4.label"
        self.data_url = "https://www.nitrc.org/frs/downloadlink.php/9423/WHS_SD_rat_T2star_v1.01.nii.gz"
        self.mask_url = "https://www.nitrc.org/frs/downloadlink.php/9425/WHS_SD_rat_brainmask_v1.01.nii.gz"
        self.segmentation_url = "https://www.nitrc.org/frs/download.php/12260/WHS_SD_rat_atlas_v4.nii.gz"

        self.label_local = "WHS_SD_rat_atlas_v4.label"
        self.data_local = "WHS_SD_rat_T2star_v1.01.nii.gz"
        self.mask_local = "WHS_SD_rat_brainmask_v1.01.nii.gz"
        self.segmentation_local = "WHS_SD_rat_atlas_v4.nii.gz"

        self.finish = [False, False, False, False]

        self.label_bar = QProgressBar()
        self.label_bar.setMinimumWidth(400)
        self.label_bar.setValue(0)

        self.data_bar = QProgressBar()
        self.data_bar.setMinimumWidth(400)
        self.data_bar.setValue(0)

        self.mask_bar = QProgressBar()
        self.mask_bar.setMinimumWidth(400)
        self.mask_bar.setValue(0)

        self.segmentation_bar = QProgressBar()
        self.segmentation_bar.setMinimumWidth(400)
        self.segmentation_bar.setValue(0)

        self.download_btn = QPushButton()
        self.download_btn. setMinimumWidth(100)
        self.download_btn.setText("Download")

        # ok button, used to close window
        ok_btn = QDialogButtonBox(QDialogButtonBox.Ok)
        ok_btn.accepted.connect(self.accept)

        layout.addWidget(self.label_bar)
        layout.addWidget(self.data_bar)
        layout.addWidget(self.mask_bar)
        layout.addWidget(self.segmentation_bar)
        layout.addWidget(self.download_btn)
        layout.addWidget(ok_btn)

        # Binding Button Event
        self.download_btn.clicked.connect(self.download_start)

    # Download button event
    def download_start(self):
        self.saving_folder = str(QFileDialog.getExistingDirectory(self, "Select Folder to Save Atlas"))

        if self.saving_folder != '':
            self.start_thread(self.label_url, self.label_local, self.set_label_bar_value)
            self.start_thread(self.data_url, self.data_local, self.set_data_bar_value)
            self.start_thread(self.mask_url, self.mask_local, self.set_mask_bar_value)
            self.start_thread(self.segmentation_url, self.segmentation_local, self.set_segmentation_bar_value)

    #
    def start_thread(self, url, local, func):
        file_size = requests.get(url, stream=True).headers['Content-Length']
        file_obj = open(os.path.join(self.saving_folder, local), 'wb')

        self.da_thread = DownloadThread(url, file_size, file_obj, buffer=1024)
        self.da_thread.download_proess_signal.connect(func)
        self.da_thread.start()

    # Setting progress bar
    def set_label_bar_value(self, value):
        self.label_bar.setValue(value)
        if value == 100:
            self.finish[0] = True
            return

    def set_data_bar_value(self, value):
        self.data_bar.setValue(value)
        if value == 100:
            self.finish[1] = True
            return

    def set_mask_bar_value(self, value):
        self.mask_bar.setValue(value)
        if value == 100:
            self.finish[2] = True
            return

    def set_segmentation_bar_value(self, value):
        self.segmentation_bar.setValue(value)
        if value == 100:
            self.finish[3] = True
            return

    def accept(self) -> None:
        self.close()




