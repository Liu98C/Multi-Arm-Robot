# # -*- coding: utf-8 -*-

import imp
import os
import time
from turtle import right
import PySide2
from matplotlib.pyplot import cla

dirname = os.path.dirname(PySide2.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

import cv2
from PySide2.QtCore import QRect, QTimer,QPoint,QLine
from PySide2.QtGui import QPainter, QColor, Qt, QPixmap, QImage, QFont, QBrush, QPen, QStaticText,QIcon,QCursor,QPolygon,QRadialGradient 
from PySide2.QtWidgets import (QLineEdit, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,QSlider,
                               QWidget, QApplication, QDesktopWidget, QStyle, QLabel,QGridLayout,QGraphicsOpacityEffect,QStackedWidget,QAction,QTextEdit,QStatusBar)
from grpc import server
from numpy.lib.function_base import select
from settings_dialog import SettingsDialog
import msg_box
from gb import thread_runner, YOLOGGER
import numpy as np
import cv2
import json
import threading
import mmap, contextlib
import rospy
import gb
class state_widget(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = SettingsDialog() #初始化setting按钮
        self.label_robotpower = QPushButton()
        self.label_robotpower.setStyleSheet("QPushButton{border-image: url(img/robotPower.png)}")
        self.label_robotpower.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.label_robotpower.setFixedHeight(30) # 将QPushButton设置为固定的大小
        self.label_robotpower.setFixedWidth(50) # 将QPushButton设置为固定的大小

        self.label_carpower = QPushButton()
        self.label_carpower.setStyleSheet("QPushButton{border-image: url(img/carpower.png)}")
        self.label_carpower.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.label_carpower.setFixedHeight(30) # 将QPushButton设置为固定的大小
        self.label_carpower.setFixedWidth(50) # 将QPushButton设置为固定的大小

        self.label_signal = QPushButton()
        self.label_signal.setStyleSheet("QPushButton{border-image: url(img/signal.png)}")
        self.label_signal.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.label_signal.setFixedHeight(30) # 将QPushButton设置为固定的大小
        self.label_signal.setFixedWidth(60) # 将QPushButton设置为固定的大小

        self.label_title = QLabel("多臂苹果采摘机器人")
        self.label_title.setStyleSheet("font-size:40px")
        self.label_title.setFont(QFont("Roman times",40))
        self.label_title.setAlignment(Qt.AlignCenter)

        self.label_title2 = QLabel("Multi-arm Harvesting Robot for Apple")
        self.label_title2.setStyleSheet("font-size:20px")
        self.label_title2.setFont(QFont("Roman times",20))
        self.label_title2.setAlignment(Qt.AlignCenter)

        self.btn_setting = QPushButton()
        self.btn_setting.setStyleSheet("QPushButton{border-image: url(img/setting.png)}")
        # self.btn_setting.clicked.connect(self.settings.exec)#设置setting按钮的槽和信号
        self.btn_setting.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_setting.setFixedHeight(50) # 将QPushButton设置为固定的大小
        self.btn_setting.setFixedWidth(50) # 将QPushButton设置为固定的大小

        self.btn_lock = QPushButton()
        self.btn_lock.setStyleSheet("QPushButton{border-image: url(img/unlock-altGreen.png)}")
        self.btn_lock.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_lock.setFixedHeight(50) # 将QPushButton设置为固定的大小
        self.btn_lock.setFixedWidth(50) # 将QPushButton设置为固定的大小

        self.btn_power = QPushButton()
        self.btn_power.setStyleSheet("QPushButton{border-image: url(img/power.png)}")
        self.btn_power.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_power.setFixedHeight(50) # 将QPushButton设置为固定的大小
        self.btn_power.setFixedWidth(50) # 将QPushButton设置为固定的大小
        self.btn_power.clicked.connect(self.power_control) # 如果摄像头的按键被点击，响应相应的信号

        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.label_robotpower)
        self.hbox.addWidget(self.label_carpower)
        self.hbox.addWidget(self.label_signal)
        self.hbox.addWidget(self.label_title)
        self.hbox.addWidget(self.btn_setting)
        self.hbox.addWidget(self.btn_lock)
        self.hbox.addWidget(self.btn_power)
        self.hbox.setAlignment(Qt.AlignTop)


        self.vbox = QVBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.vbox.addWidget(self.label_title2)

        self.setFixedHeight(100)
        self.setLayout(self.vbox)
        self.cameraOption = False
        
    def power_control(self):
        if not gb.CONFIG_order[:10].any():
            for i in range(10):
                gb.record_order(i, 15)
        elif (gb.CONFIG_order[:10] == np.ones(10, dtype=np.uint8)*15).all():
            for i in range(10):
                gb.record_order(i, 6)
            for j in range(10,15):
                gb.record_order(j, 0) 
        elif (gb.CONFIG_order[:10] == np.ones(10, dtype=np.uint8)*6).all():
            for i in range(10):
                gb.record_order(i, 15)

