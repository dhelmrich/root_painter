"""
Copyright (C) 2020 Abraham George Smith

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# pylint: disable=C0111, I1101, E0611
import os

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtCore import Qt


class NavWidget(QtWidgets.QWidget):
    """ Shows next and previous buttons as well as image position in folder.
    """
    file_change = QtCore.pyqtSignal(str)
    save_image = QtCore.pyqtSignal()

    def __init__(self, all_fnames):
        super().__init__()
        self.image_path = None
        self.all_fnames = all_fnames
        self.initUI()

    def initUI(self):
        # container goes full width to allow contents to be center aligned within it.
        nav = QtWidgets.QWidget()
        nav_layout = QtWidgets.QHBoxLayout()

        # && to escape it and show single &
        self.prev_image_button = QtWidgets.QPushButton('< Previous')
        self.prev_image_button.setFocusPolicy(Qt.NoFocus)
        self.prev_image_button.clicked.connect(self.show_prev_image)
        nav_layout.addWidget(self.prev_image_button)
        self.nav_label = QtWidgets.QLabel()
        nav_layout.addWidget(self.nav_label)

        # lock button
        self.lock_button = QtWidgets.QCheckBox('Lock Annotation')
        self.lock_button.setFocusPolicy(Qt.NoFocus)
        self.lock_button.clicked.connect(self.lock_button_engaged)
        nav_layout.addWidget(self.lock_button)
        self.locking_enabled = False

        self.save_image_button = QtWidgets.QPushButton("Save")
        self.save_image_button.setFocusPolicy(Qt.NoFocus)
        self.save_image_button.clicked.connect(self.save_image_request)
        nav_layout.addWidget(self.save_image_button)

        # && to escape it and show single &
        self.next_image_button = QtWidgets.QPushButton('Save && Next >')
        self.next_image_button.setFocusPolicy(Qt.NoFocus)
        self.next_image_button.clicked.connect(self.show_next_image)
        nav_layout.addWidget(self.next_image_button)

        

        self.process_label = QtWidgets.QLabel("Initializing!")
        self.process_label.setFocusPolicy(Qt.NoFocus)
        nav_layout.addWidget(self.process_label)

        # left, top, right, bottom
        nav_layout.setContentsMargins(0, 0, 0, 5)
        nav.setLayout(nav_layout)
        nav.setMaximumWidth(2000)

        container_layout = QtWidgets.QHBoxLayout()
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(nav)
        self.setLayout(container_layout)
        container_layout.setContentsMargins(0, 0, 0, 0)

    def get_path_list(self, dir_path):
        all_files = self.all_fnames
        all_paths = [os.path.abspath(os.path.join(os.path.abspath(dir_path), a))
                     for a in all_files]
        return all_paths

    def lock_button_engaged(self, button_value) :
        self.locking_enabled = button_value

    def show_next_image(self):
        self.next_image_button.setEnabled(False)
        self.save_image_button.setEnabled(False)
        self.process_label.setText('Loading Image...')
        QtWidgets.QApplication.processEvents()
        dir_path, _ = os.path.split(self.image_path)
        all_paths = self.get_path_list(dir_path)
        cur_idx = all_paths.index(self.image_path)
        next_idx = cur_idx + 1
        if next_idx >= len(all_paths):
            next_idx = 0
        self.image_path = all_paths[next_idx]
        self.file_change.emit(self.image_path)
        self.update_nav_label()

    def save_image_request(self) :
        print("Received save image click")
        QtWidgets.QApplication.processEvents()
        self.save_image.emit()

    def show_prev_image(self):
        dir_path, _ = os.path.split(self.image_path)
        all_paths = self.get_path_list(dir_path)
        cur_idx = all_paths.index(self.image_path)
        next_idx = cur_idx - 1
        if next_idx <= 0:
            next_idx = 0
        self.image_path = all_paths[next_idx]
        self.file_change.emit(self.image_path)
        self.update_nav_label()

    def update_nav_label(self):
        dir_path, _ = os.path.split(self.image_path)
        all_paths = self.get_path_list(dir_path)
        cur_idx = all_paths.index(os.path.abspath(self.image_path))
        self.nav_label.setText(f'{cur_idx + 1} / {len(all_paths)}')
