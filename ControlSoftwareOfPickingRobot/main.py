# -*- coding: utf-8 -*-
"""
Author: Cheng Liu
Email: liucheng3666@163.com
Date: 2022/11/10
"""
import os
import PySide2
import cv2
import mmap, contextlib
import numpy as np
import sys
import threading
import datetime
from PySide2.QtCore import QSize, Signal,QTimer,QProcess
from PySide2.QtGui import QPainter, QColor, Qt, QPixmap, QImage, QFont, QBrush, QPen, QStaticText,QIcon,QCursor,QPolygon,QRadialGradient,QMovie
from PySide2.QtWidgets import (QLineEdit, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,QSlider,
                               QWidget, QApplication, QDesktopWidget, QStyle, QLabel,QGridLayout,QGraphicsOpacityEffect,QStackedWidget,QAction,QTextEdit,QStatusBar)

import msg_box
import gb
from gb import YOLOGGER
from settings_dialog import SettingsDialog
from widget_camera import WidgetCamera
from PySide2 import QtCore
import gb
import time
from StateWidget import state_widget
from basktWindow import basketMainwindow
from drawApple import WidgetAppleXY,WidgetAppleYZ

from dictionary import armDict, errorDict, motorDict, deviceDict, motorID


dirname = os.path.dirname(PySide2.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path


class MainWindow(QMainWindow):  
    signal_config_error = Signal(str)

    def __init__(self):
        super().__init__()

        gb.init_logger()#初始化一个日志
        gb.clean_log()#清理日志信息
        gb.init_config()#初始化配置
        self.camera = WidgetCamera()  # 初始化摄像头
        self.settings = SettingsDialog() #初始化setting按钮
        # self.control = ControlWidget()
        self.state = state_widget()
        self.stackedWidget = QStackedWidget()
        self.vboxStackedWidget = QStackedWidget()
        self.stateStackedWidget = QStackedWidget()
        self.status = QStatusBar()
        self.process = QProcess() 
        self.basket = basketMainwindow()

        self.send = True
        self.mainMode = True
        
        # --------------------------------------设备状态反馈-------------------------------------       
        
        self.motorPre = np.zeros((10, 20), dtype=np.uint8)
        self.devicePre = np.zeros((5, 4), dtype=np.int32)
        self._state = np.zeros(400)
        
        # --------------------------------------setting-------------------------------------

        self.GridControl = QGridLayout()
        
        self.camereSetting = QPushButton()  # 开启或关闭摄像头，初始化开关摄像头的按键
        self.camereSetting.setStyleSheet("QPushButton{border-image: url(img/sensor.png)}")
        self.camereSetting.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.camereSetting.clicked.connect(self.oc_camera) # 如果摄像头的按键被点击，响应相应的信号
        self.camereSetting.setFixedHeight(150) # 将QPushButton设置为固定的大小
        self.camereSetting.setFixedWidth(200) # 将QPushButton设置为固定的大小
        self.GridControl.addWidget(self.camereSetting,1,1,1,1,Qt.AlignCenter)
        
        self.lightSetting = QPushButton()
        self.lightSetting.setStyleSheet("QPushButton{border-image: url(img/light.png)}")
        self.lightSetting.setFixedHeight(180) # 将QPushButton设置为固定的大小
        self.lightSetting.setFixedWidth(180) # 将QPushButton设置为固定的大小
        self.lightSetting.clicked.connect(self.lightControl)
        self.GridControl.addWidget(self.lightSetting,1,2,1,1,Qt.AlignCenter)
        
        self.powerSetting = QPushButton()
        self.powerSetting.setStyleSheet("QPushButton{border-image: url(img/robotPower.png)}")
        self.powerSetting.setFixedHeight(100) # 将QPushButton设置为固定的大小
        self.powerSetting.setFixedWidth(180) # 将QPushButton设置为固定的大小
        self.GridControl.addWidget(self.powerSetting,1,3,1,1,Qt.AlignCenter)
        
        self.basketControl = QPushButton()
        self.basketControl.setStyleSheet("QPushButton{border-image: url(img/baskerControl.png)}")
        self.basketControl.setFixedHeight(180) # 将QPushButton设置为固定的大小
        self.basketControl.setFixedWidth(180) # 将QPushButton设置为固定的大小
        self.basketControl.clicked.connect(self.basket.show)
        self.GridControl.addWidget(self.basketControl,1,4,1,1,Qt.AlignCenter)

        self.camereLabel = QLabel("传感器控制")  # 开启或关闭摄像头，初始化开关摄像头的按键
        self.camereLabel.setStyleSheet("font-size:30px")
        self.camereLabel.setAlignment(Qt.AlignCenter)
        self.camereLabel.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.camereLabel.setFixedWidth(200) # 将QPushButton设置为固定的大小
        self.GridControl.addWidget(self.camereLabel,2,1,1,1,Qt.AlignCenter)
        
        self.lightLabel = QLabel("灯光控制")
        self.lightLabel.setStyleSheet("font-size:30px")
        self.lightLabel.setAlignment(Qt.AlignCenter)
        self.lightLabel.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.lightLabel.setFixedWidth(200) # 将QPushButton设置为固定的大小
        self.GridControl.addWidget(self.lightLabel,2,2,1,1,Qt.AlignCenter)

        self.powerLabel = QLabel("电源设置")
        self.powerLabel.setStyleSheet("font-size:30px")
        self.powerLabel.setAlignment(Qt.AlignCenter)
        self.powerLabel.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.powerLabel.setFixedWidth(200) # 将QPushButton设置为固定的大小
        self.GridControl.addWidget(self.powerLabel,2,3,1,1,Qt.AlignCenter)

        self.basketLabel = QLabel("作业统计")
        self.basketLabel.setStyleSheet("font-size:30px")
        self.basketLabel.setAlignment(Qt.AlignCenter)
        self.basketLabel.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.basketLabel.setFixedWidth(200) # 将QPushButton设置为固定的大小
        self.GridControl.addWidget(self.basketLabel,2,4,1,1,Qt.AlignCenter)

        self.manipulatorControl = QPushButton()
        self.manipulatorControl.setStyleSheet("QPushButton{border-image: url(img/manipulator.png)}")
        # self.manipulatorControl.setGeometry(100,1000,200,150)
        self.manipulatorControl.setFixedHeight(200) # 将QPushButton设置为固定的大小
        self.manipulatorControl.setFixedWidth(150) # 将QPushButton设置为固定的大小
        self.GridControl.addWidget(self.manipulatorControl,3,1,1,1,Qt.AlignCenter)
        self.manipulatorControl.clicked.connect(self.manipulatorAction) # 如果摄像头的按键被点击，响应相应的信号

        self.beltControl = QPushButton()
        self.beltControl.setStyleSheet("QPushButton{border-image: url(img/beltControl.png)}")
        self.beltControl.setFixedHeight(180) # 将QPushButton设置为固定的大小
        self.beltControl.setFixedWidth(150) # 将QPushButton设置为固定的大小
        self.beltControl.clicked.connect(self.beltAction)
        self.GridControl.addWidget(self.beltControl,3,2,1,1,Qt.AlignCenter)

        self.handControl = QPushButton()
        self.handControl.setStyleSheet("QPushButton{border-image: url(img/handSetting.png)}")
        self.handControl.setFixedHeight(180) # 将QPushButton设置为固定的大小
        self.handControl.setFixedWidth(150) # 将QPushButton设置为固定的大小
        self.handControl.clicked.connect(self.handAction)
        self.GridControl.addWidget(self.handControl,3,3,1,1,Qt.AlignCenter)

        self.otherSetting = QPushButton()  # 开启或关闭摄像头，初始化开关摄像头的按键
        self.otherSetting.setStyleSheet("QPushButton{border-image: url(img/otherSetting.png)}")
        self.otherSetting.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.otherSetting.setFixedHeight(200) # 将QPushButton设置为固定的大小
        self.otherSetting.setFixedWidth(200) # 将QPushButton设置为固定的大小
        self.otherSetting.clicked.connect(self.settings.exec)#设置setting按钮的槽和信号,exec阻塞旧窗口保持新窗口在最前面，而show可以切换新窗口和主窗口
        self.GridControl.addWidget(self.otherSetting,3,4,1,1,Qt.AlignCenter)

        self.manipulatorLabel = QLabel("机械臂控制")
        self.manipulatorLabel.setStyleSheet("font-size:30px")
        self.manipulatorLabel.setAlignment(Qt.AlignCenter)
        self.manipulatorLabel.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.manipulatorLabel.setFixedWidth(200) # 将QPushButton设置为固定的大小
        self.GridControl.addWidget(self.manipulatorLabel,4,1,1,1,Qt.AlignCenter)

        self.beltLabel = QLabel("传送带控制")
        self.beltLabel.setStyleSheet("font-size:30px")
        self.beltLabel.setAlignment(Qt.AlignCenter)
        self.beltLabel.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.beltLabel.setFixedWidth(200) # 将QPushButton设置为固定的大小
        self.GridControl.addWidget(self.beltLabel,4,2,1,1,Qt.AlignCenter)

        self.handLabel = QLabel("执行器设置")
        self.handLabel.setStyleSheet("font-size:30px")
        self.handLabel.setAlignment(Qt.AlignCenter)
        self.handLabel.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.handLabel.setFixedWidth(200) # 将QPushButton设置为固定的大小
        self.GridControl.addWidget(self.handLabel,4,3,1,1,Qt.AlignCenter)

        self.otherLabel = QLabel("其他设置")  # 开启或关闭摄像头，初始化开关摄像头的按键
        self.otherLabel.setStyleSheet("font-size:30px")
        self.otherLabel.setAlignment(Qt.AlignCenter)
        self.otherLabel.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.otherLabel.setFixedWidth(200) # 将QPushButton设置为固定的大小
        self.GridControl.addWidget(self.otherLabel,4,4,1,1,Qt.AlignCenter)       

        self.widget_setting = QWidget()
        self.widget_setting.setLayout(self.GridControl)

        # ----------------------------------------主界面---------------------------------------------#
        self.tips = [True,True,True]
        self.btn_auto = QPushButton()  # 开启或关闭摄像头，初始化开关摄像头的按键
        self.btn_auto.setStyleSheet("QPushButton{border-image: url(img/font.png)}")
        self.btn_auto.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_auto.setFixedHeight(150) # 将QPushButton设置为固定的大小
        self.btn_auto.setFixedWidth(150) # 将QPushButton设置为固定的大小
        self.btn_auto.clicked.connect(self.automode) # 如果摄像头的按键被点击，响应相应的信号

        self.label_auto = QLabel("无人化\n作业")
        self.label_auto.setFixedWidth(150)
        self.label_auto.setStyleSheet("background-color:rgb(192,192,192,0);font-size:30px")
        self.label_auto.setFont(QFont("Roman times",30))
        self.label_auto.setAlignment(Qt.AlignCenter)

        self.btn_help = QPushButton()  # 开启或关闭摄像头，初始化开关摄像头的按键
        self.btn_help.setStyleSheet("QPushButton{border-image: url(img/steam.png)}")
        self.btn_help.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_help.setFixedHeight(150) # 将QPushButton设置为固定的大小
        self.btn_help.setFixedWidth(150) # 将QPushButton设置为固定的大小
        self.btn_help.clicked.connect(self.helpmode) # 如果摄像头的按键被点击，响应相应的信号

        self.label_help = QLabel("半自动\n作业")
        self.label_help.setFixedWidth(150)
        self.label_help.setStyleSheet("background-color:rgb(192,192,192,0);font-size:30px")
        self.label_help.setFont(QFont("Roman times",30))
        self.label_help.setAlignment(Qt.AlignCenter)

        self.btn_manual = QPushButton()  # 开启或关闭摄像头，初始化开关摄像头的按键
        self.btn_manual.setStyleSheet("QPushButton{border-image: url(img/hand-stop-o.png)}")
        self.btn_manual.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_manual.setFixedHeight(150) # 将QPushButton设置为固定的大小
        self.btn_manual.setFixedWidth(150) # 将QPushButton设置为固定的大小
        self.btn_manual.clicked.connect(self.manualmode) # 如果摄像头的按键被点击，响应相应的信号

        self.label_manual = QLabel("人工\n操作")
        self.label_manual.setFixedWidth(150)
        self.label_manual.setStyleSheet("background-color:rgb(192,192,192,0);font-size:30px")
        self.label_manual.setFont(QFont("Roman times",30))
        self.label_manual.setAlignment(Qt.AlignCenter)

        self.btn_visual = QPushButton()  # 开启或关闭摄像头，初始化开关摄像头的按键
        self.btn_visual.setStyleSheet("QPushButton{border-image: url(img/visual.png)}")
        self.btn_visual.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_visual.setFixedHeight(150) # 将QPushButton设置为固定的大小
        self.btn_visual.setFixedWidth(150) # 将QPushButton设置为固定的大小
        self.btn_visual.clicked.connect(self.rviz)

        self.label_visual = QLabel("可视\n化")
        self.label_visual.setFixedWidth(150)
        self.label_visual.setStyleSheet("background-color:rgb(192,192,192,0);font-size:30px")
        self.label_visual.setFont(QFont("Roman times",30))
        self.label_visual.setAlignment(Qt.AlignCenter)

        self.hbox_modeSelect = QHBoxLayout()
        self.hbox_modeSelect.addWidget(self.btn_auto)
        self.hbox_modeSelect.addWidget(self.label_auto)
        self.hbox_modeSelect.addWidget(self.btn_help)
        self.hbox_modeSelect.addWidget(self.label_help)
        self.hbox_modeSelect.addWidget(self.btn_manual)
        self.hbox_modeSelect.addWidget(self.label_manual)
        self.hbox_modeSelect.addWidget(self.btn_visual)
        self.hbox_modeSelect.addWidget(self.label_visual)
        # self.hbox_modeSelect.setContentsMargins(0, 0, 0, 0)

        self.widget_modeSelect = QWidget()
        self.widget_modeSelect.setLayout(self.hbox_modeSelect)
        self.widget_modeSelect.setMaximumHeight(200)
        self.widget_modeSelect.setStyleSheet("background-color:rgb(192,192,192,140);font-size:30px")
        
        self.title = QLabel()
        sw, sh = self.title.width(), self.title.height()  # 图像窗口宽高
        self.path_car = QMovie("img/gif-Harvester.gif")
        self.title.setMovie(self.path_car)
        self.path_car.start()
        self.ratio = 1920 / 1289

        self.mainwindowtitle = cv2.imread("img/car.jpg")
        ih, iw, _ = self.mainwindowtitle.shape
        qimage_car = QImage(self.mainwindowtitle.data, iw, ih, 3 * iw, QImage.Format_BGR888)  
        self.qpixmap_car = QPixmap.fromImage(qimage_car.scaled(sw, sh, Qt.KeepAspectRatio))  # 保持指定长宽比转QPixmap
        
        # self.title.setPixmap(self.qpixmap_car)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("background-color:rgb(128,138,135);font-size:20px;color:black")
        
        self.vbox_title = QVBoxLayout()
        self.vbox_title.addWidget(self.title,3)
        self.vbox_title.addWidget(self.widget_modeSelect,1)
        self.widget_title = QWidget()
        self.widget_title.setLayout(self.vbox_title)
        # -------------------------------------侧切换栏---------------------------------------#
        self.btn_side_auto = QPushButton()
        self.btn_side_auto.setStyleSheet("QPushButton{border-image: url(img/steamSide.png)}")
        self.btn_side_auto.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_side_auto.setFixedHeight(80) # 将QPushButton设置为固定的大小
        self.btn_side_auto.setFixedWidth(80) # 将QPushButton设置为固定的大小
        self.btn_side_auto.clicked.connect(self.side1)

        self.btn_side_help = QPushButton()
        self.btn_side_help.setStyleSheet("QPushButton{border-image: url(img/hand-stop-oSide.png)}")
        self.btn_side_help.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_side_help.setFixedHeight(80) # 将QPushButton设置为固定的大小
        self.btn_side_help.setFixedWidth(80) # 将QPushButton设置为固定的大小
        self.btn_side_help.clicked.connect(self.side2)

        self.btn_return = QPushButton()
        self.btn_return.setStyleSheet("QPushButton{border-image: url(img/homeSide.png)}")
        self.btn_return.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_return.setFixedHeight(80) # 将QPushButton设置为固定的大小
        self.btn_return.setFixedWidth(80) # 将QPushButton设置为固定的大小
        self.btn_return.clicked.connect(self.return_main)

        self.btn_side_visual = QPushButton()
        self.btn_side_visual.setStyleSheet("QPushButton{border-image: url(img/visualSide.png)}")
        self.btn_side_visual.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_side_visual.setFixedHeight(80) # 将QPushButton设置为固定的大小
        self.btn_side_visual.setFixedWidth(80) # 将QPushButton设置为固定的大小
        self.btn_side_visual.clicked.connect(self.rviz)

        self.vbox_side = QVBoxLayout()
        self.vbox_side.addWidget(self.btn_side_auto)
        self.vbox_side.addWidget(self.btn_side_help)
        self.vbox_side.addWidget(self.btn_return)
        self.vbox_side.addWidget(self.btn_side_visual)
        self.vbox_side.addStretch()

        # -------------------------------------自动模式 --------------------------------------#
        self.btn_auto_prepare = QPushButton('准备')  # 开启或关闭摄像头，初始化开关摄像头的按键
        self.btn_auto_prepare.setStyleSheet("background-color:rgb(46,142,206);font-size:30px;color:white;border-radius: 30px")
        self.btn_auto_prepare.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_auto_prepare.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.btn_auto_prepare.clicked.connect(self.prepare)

        self.btn_auto_start = QPushButton('开启')  # 开启或关闭摄像头，初始化开关摄像头的按键
        self.btn_auto_start.setStyleSheet("background-color:rgb(46,142,206);font-size:30px;color:white;border-radius: 30px")
        self.btn_auto_start.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_auto_start.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.btn_auto_start.clicked.connect(self.startPick)

        self.btn_stop = QPushButton('停止')  # 开启或关闭摄像头，初始化开关摄像头的按键
        self.btn_stop.setStyleSheet("background-color:rgb(46,142,206);font-size:30px;color:white;border-radius: 30px")
        self.btn_stop.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_stop.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.btn_stop.clicked.connect(self.close_mode)

        self.btn_auto_end = QPushButton('复位')  # 开启或关闭摄像头，初始化开关摄像头的按键
        self.btn_auto_end.setStyleSheet("background-color:rgb(46,142,206);font-size:30px;color:white;border-radius: 30px")
        self.btn_auto_end.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_auto_end.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.btn_auto_end.clicked.connect(self.restore)

        self.hbox_auto = QHBoxLayout()
        self.hbox_auto.addWidget(self.btn_auto_prepare)
        self.hbox_auto.addWidget(self.btn_auto_start)
        self.hbox_auto.addWidget(self.btn_stop)
        self.hbox_auto.addWidget(self.btn_auto_end)

        self.autoTitle = QLabel("无人化作业")
        self.autoTitle.setStyleSheet("font-size:20px")

        self.cameraPick1 = QPushButton("1")
        self.cameraPick2 = QPushButton("2")
        self.cameraPick3 = QPushButton("3")
        self.cameraPick4 = QPushButton("4")
        self.cameraPick5 = QPushButton("A")
        self.cameraPick1.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
        self.cameraPick2.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
        self.cameraPick3.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
        self.cameraPick4.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
        self.cameraPick5.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
        self.cameraPick1.setMaximumWidth(60)
        self.cameraPick1.setMaximumHeight(60)
        self.cameraPick2.setMaximumWidth(60)
        self.cameraPick2.setMaximumHeight(60)
        self.cameraPick3.setMaximumWidth(60)
        self.cameraPick3.setMaximumHeight(60)
        self.cameraPick4.setMaximumWidth(60)
        self.cameraPick4.setMaximumHeight(60)
        self.cameraPick5.setMaximumWidth(60)
        self.cameraPick5.setMaximumHeight(60)
        self.cameraPick1.clicked.connect(lambda: self.selectImage(1))
        self.cameraPick2.clicked.connect(lambda: self.selectImage(2))
        self.cameraPick3.clicked.connect(lambda: self.selectImage(3))
        self.cameraPick4.clicked.connect(lambda: self.selectImage(4))
        self.cameraPick5.clicked.connect(lambda: self.selectImage(5))
        

        self.hbox_camera = QHBoxLayout()
        self.hbox_camera.addWidget(self.cameraPick1)
        self.hbox_camera.addWidget(self.cameraPick2)
        self.hbox_camera.addWidget(self.cameraPick3)
        self.hbox_camera.addWidget(self.cameraPick4)
        self.hbox_camera.addWidget(self.cameraPick5)
 
        

        # ------------------------------------右侧控制栏-----------------------------------#

        self.label_manipulator1 = QPushButton()
        self.label_manipulator1.setStyleSheet("QPushButton{border-image: url(img/1.png)}")
        self.label_manipulator1.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.label_manipulator1.setFixedHeight(30) # 将QPushButton设置为固定的大小
        self.label_manipulator1.setFixedWidth(30) # 将QPushButton设置为固定的大小

        self.label_manipulator2 = QPushButton()
        self.label_manipulator2.setStyleSheet("QPushButton{border-image: url(img/2.png)}")
        self.label_manipulator2.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.label_manipulator2.setFixedHeight(30) # 将QPushButton设置为固定的大小
        self.label_manipulator2.setFixedWidth(30) # 将QPushButton设置为固定的大小

        self.label_manipulator3 = QPushButton()
        self.label_manipulator3.setStyleSheet("QPushButton{border-image: url(img/3.png)}")
        self.label_manipulator3.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.label_manipulator3.setFixedHeight(30) # 将QPushButton设置为固定的大小
        self.label_manipulator3.setFixedWidth(30) # 将QPushButton设置为固定的大小

        self.label_manipulator4 = QPushButton()
        self.label_manipulator4.setStyleSheet("QPushButton{border-image: url(img/4.png)}")
        self.label_manipulator4.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.label_manipulator4.setFixedHeight(30) # 将QPushButton设置为固定的大小
        self.label_manipulator4.setFixedWidth(30) # 将QPushButton设置为固定的大小

        self.btn_manipulator1 = QPushButton()
        self.btn_manipulator1.setStyleSheet("QPushButton{border-image: url(img/manipulator.png)}")
        self.btn_manipulator1.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_manipulator1.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.btn_manipulator1.setFixedWidth(30) # 将QPushButton设置为固定的大小

        self.btn_manipulator2 = QPushButton()
        self.btn_manipulator2.setStyleSheet("QPushButton{border-image: url(img/manipulator.png)}")
        self.btn_manipulator2.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_manipulator2.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.btn_manipulator2.setFixedWidth(30) # 将QPushButton设置为固定的大小

        self.btn_manipulator3 = QPushButton()
        self.btn_manipulator3.setStyleSheet("QPushButton{border-image: url(img/manipulator.png)}")
        self.btn_manipulator3.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_manipulator3.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.btn_manipulator3.setFixedWidth(30) # 将QPushButton设置为固定的大小

        self.btn_manipulator4 = QPushButton()
        self.btn_manipulator4.setStyleSheet("QPushButton{border-image: url(img/manipulator.png)}")
        self.btn_manipulator4.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_manipulator4.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.btn_manipulator4.setFixedWidth(30) # 将QPushButton设置为固定的大小

        self.label_pickNum1 = QLabel('0')
        self.label_pickNum2 = QLabel('0')
        self.label_pickNum3 = QLabel('0')
        self.label_pickNum4 = QLabel('0')
        self.label_pickNum1.setStyleSheet("font-size:20px")
        self.label_pickNum2.setStyleSheet("font-size:20px")
        self.label_pickNum3.setStyleSheet("font-size:20px")
        self.label_pickNum4.setStyleSheet("font-size:20px")
        
        self.grid_manipulator = QGridLayout()
        self.grid_manipulator.addWidget(self.label_manipulator1,1,1,1,1)
        self.grid_manipulator.addWidget(self.label_manipulator2,1,2,1,1)
        self.grid_manipulator.addWidget(self.label_manipulator3,1,3,1,1)
        self.grid_manipulator.addWidget(self.label_manipulator4,1,4,1,1)
        self.grid_manipulator.addWidget(self.btn_manipulator1,2,1,1,1)
        self.grid_manipulator.addWidget(self.btn_manipulator2,2,2,1,1)
        self.grid_manipulator.addWidget(self.btn_manipulator3,2,3,1,1)
        self.grid_manipulator.addWidget(self.btn_manipulator4,2,4,1,1)
        self.grid_manipulator.addWidget(self.label_pickNum1,3,1,1,1)
        self.grid_manipulator.addWidget(self.label_pickNum2,3,2,1,1)
        self.grid_manipulator.addWidget(self.label_pickNum3,3,3,1,1)
        self.grid_manipulator.addWidget(self.label_pickNum4,3,4,1,1)

        self.bnt_basket = QPushButton()
        self.bnt_basket.setStyleSheet("QPushButton{border-image: url(img/shopping-basket.png)}")
        self.bnt_basket.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.bnt_basket.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.bnt_basket.setFixedWidth(60) # 将QPushButton设置为固定的大小
        
        self.label_basket = QLabel("0")
        self.label_basket.setStyleSheet("font-size:20px")
        self.label_basket.setMaximumWidth(50)
        self.label_basket.setAlignment(Qt.AlignCenter)

        self.bnt_clock = QPushButton()
        self.bnt_clock.setStyleSheet("QPushButton{border-image: url(img/clock-o1.png)}")
        self.bnt_clock.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.bnt_clock.setFixedHeight(60) # 将QPushButton设置为固定的大小
        self.bnt_clock.setFixedWidth(60) # 将QPushButton设置为固定的大小
        
        self.label_clock = QLabel()
        self.label_clock.setStyleSheet("font-size:20px")
        self.label_clock.setMaximumWidth(50)
        self.label_clock.setAlignment(Qt.AlignCenter)
        thread = threading.Thread(target=self.timeUpdate)
        thread.start()
        
        self.hbox_basket = QHBoxLayout()
        self.hbox_basket.addWidget(self.bnt_basket)
        self.hbox_basket.addWidget(self.label_basket)
        self.hbox_basket.addSpacing(30)
        self.hbox_basket.addWidget(self.bnt_clock)
        self.hbox_basket.addWidget(self.label_clock)
        self.hbox_basket.setAlignment(Qt.AlignCenter)

        self.btn_light = QPushButton()
        self.btn_light.setStyleSheet("QPushButton{border-image: url(img/灯光关闭.png)}")
        self.btn_light.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_light.setFixedHeight(80) # 将QPushButton设置为固定的大小
        self.btn_light.setFixedWidth(80) # 将QPushButton设置为固定的大小
        self.btn_light.clicked.connect(self.lightControl)

        self.btn_belt = QPushButton()
        self.btn_belt.setStyleSheet("QPushButton{border-image: url(img/传送带停止.png)}")
        self.btn_belt.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_belt.setFixedHeight(80) # 将QPushButton设置为固定的大小
        self.btn_belt.setFixedWidth(80) # 将QPushButton设置为固定的大小
        self.btn_belt.clicked.connect(self.beltAction)
        

        self.btn_hand = QPushButton()
        self.btn_hand.setStyleSheet("QPushButton{border-image: url(img/爪子张开.png)}")
        self.btn_hand.setEnabled(True) # 总开关：设置成false ，按钮就不可点击，设置成true，按钮就可以点击，按钮是灰色的，无论是否可点击（即使将setClickable()设置成true），都无法响应任何触发事件。
        self.btn_hand.setFixedHeight(80) # 将QPushButton设置为固定的大小
        self.btn_hand.setFixedWidth(80) # 将QPushButton设置为固定的大小
        self.btn_hand.clicked.connect(self.handAction)
        

        self.hbox_light = QHBoxLayout()
        self.hbox_light.addWidget(self.btn_light)
        self.hbox_light.addWidget(self.btn_belt)
        self.hbox_light.addWidget(self.btn_hand)

        self.infoAuto = QTextEdit("【置顶消息】点击【准备】，机器人就绪")
        self.infoAuto.append("【置顶消息】点击【开启】，自动作业") 
        self.infoAuto.append("【置顶消息】点击【停止】，停止作业")                        
        self.infoAuto.append("【置顶消息】点击【复位】，机械臂复位")
        self.infoAuto.append("")
        self.infoAuto.setStyleSheet("background-color:rgb(255,242,204);border-radius: 15px")
        
        thread = threading.Thread(target=self.infoUpdate)
        thread.start()
        vbox_auto = QVBoxLayout()#初始化垂直布局
        vbox_auto.setContentsMargins(0, 0, 0, 0)#设置左侧，顶部，右侧，底部的边距
        vbox_auto.addLayout(self.grid_manipulator)
        vbox_auto.addLayout(self.hbox_basket)
        vbox_auto.addLayout(self.hbox_light)
        vbox_auto.addWidget(self.infoAuto)

        #------------------------布局整个window，用QWidget放入所有布局或空间--------------------#
        right_widget = QWidget()#初始化一个控件,所有控件啥的都显示在控件（与window不同），QWidget类是所有用户界面对象的基类，这个QWidget负责右侧窗口的容纳
        right_widget.setMaximumWidth(500)#设置它的最大窗口值，即图形显示界面右面的宽度值
        right_widget.setLayout(vbox_auto)#把右侧垂直布局放入这个窗口内


        self.vbox_XYZ = QVBoxLayout()
        self.widget_XY = WidgetAppleXY()
        self.widget_YZ = WidgetAppleYZ()

        self.vbox_XYZ.addWidget(self.widget_XY)
        self.vbox_XYZ.addWidget(self.widget_YZ)
        self.widget_XYZ = QWidget()
        self.widget_XYZ.setLayout(self.vbox_XYZ)
        self.grid_btnCamera = QGridLayout()


        self.hbox = QHBoxLayout()#初始化水平布局
        self.hbox.addLayout(self.vbox_side,1)
        self.hbox.addLayout(self.grid_btnCamera, 3)#在水平布局中增加摄像头控件
        self.hbox.addWidget(right_widget, 1)#在水平布局中增加一个窗口
        self.widget = QWidget()
        self.widget.setLayout(self.hbox)

        self.stackedWidget.addWidget(self.widget_title)
        self.stackedWidget.addWidget(self.widget)
        self.stackedWidget.addWidget(self.widget_setting)

        self.main_grid = QVBoxLayout()
        self.main_grid.addWidget(self.state,1)
        self.main_grid.addWidget(self.stackedWidget,4)
        self.mainWidget = QWidget()
        self.mainWidget.setLayout(self.main_grid)
        self.setCentralWidget(self.mainWidget)#在中心窗口部署QWidget
        self.state.btn_setting.clicked.connect(self.control)
        # ----------------------------------- 自适应不同大小的屏幕  --------------------------------------- #
        screen = QDesktopWidget().screenGeometry(self)#screenGeometry（）函数提供有关可用屏幕几何的信息
        available = QDesktopWidget().availableGeometry(self)#availableGeometry是返回的不包含任务栏的矩形区域
        title_height = self.style().pixelMetric(QStyle.PM_TitleBarHeight    )
        if screen.width() < 1280 or screen.height() < 768:
            self.setWindowState(Qt.WindowMaximized)  # 窗口最大化显示
            self.setFixedSize(
                available.width(),
                available.height() - title_height)  # 固定窗口大小
        else:
            self.setMinimumSize(QSize(1100, 850))  # 最小宽高
        self.setStyleSheet("background-color:rgb(218,227,243)")
        self.setWindowTitle("苹果采摘机器人控制软件")
        self.setWindowIcon(QIcon(self.qpixmap_car))
        self.show()  # 显示窗口
        
            
    def timeUpdate(self):
        min = 0
        sec = 0 
        while True:
            self.label_clock.setText(" {}’{}”".format(min,sec))
            if sec < 59: 
                sec = sec + 1 
            else:
                sec = 0
                min = min + 1
            time.sleep(1)
        
    def handAction(self):
        if gb.CONFIG_order[0] == 15:
            if gb.CONFIG_order[15] == 0:
                gb.record_order(15,1)
                self.btn_hand.setStyleSheet("QPushButton{border-image: url(img/爪子关闭.png)}")
            else:
                gb.record_order(15,0)
                self.btn_hand.setStyleSheet("QPushButton{border-image: url(img/爪子张开.png)}")
        else:
            self.slot_msg_dialog("设备已关机")

    def restore(self):
        if gb.CONFIG_order[0] == 15:
            gb.record_order(11,1)
        else:
            self.slot_msg_dialog("设备已关机")

    def infoUpdate(self):
        if gb.CONFIG_order[0] == 15:
            while True:
                with open('config/state.dat', 'r') as f:
                    with contextlib.closing(mmap.mmap(f.fileno(), 20*20, access=mmap.ACCESS_READ)) as m:
                        self._state = m.read(400)
                motorCur = np.frombuffer(self._state[0:200], dtype=np.uint8).reshape((10, 20))
                deviceCur = np.frombuffer(self._state[300:380], dtype=np.int32).reshape((5, 4))
                errorIDX = np.where(motorCur[:, 4:20] - self.motorPre[:, 4:20]==1) 
                motor_event = motorCur[:, 0:4] - self.motorPre[:, 0:4]
                device_event = deviceCur - self.devicePre
                robot_event = self._state[240]
                if robot_event == 1:
                    self.infoAuto.append(datetime.datetime.now().strftime('[%H:%M] ')+'已到达观测位！！')
                    with open('config/state.dat', 'r+') as f:
                        with contextlib.closing(mmap.mmap(f.fileno(), 20*20, access=mmap.ACCESS_WRITE)) as m:
                            m.seek(240)
                            m.write(b'\x00')    
                if robot_event == 2:
                    self.infoAuto.append(datetime.datetime.now().strftime('[%H:%M] ')+'电机全到原点！！')
                    with open('config/state.dat', 'r+') as f:
                        with contextlib.closing(mmap.mmap(f.fileno(), 20*20, access=mmap.ACCESS_WRITE)) as m:
                            m.seek(240)
                            m.write(b'\x00')             
                if not len(errorIDX[0]) == 0:
                    for i in range(len(errorIDX[0])):   
                        self.infoAuto.append(datetime.datetime.now().strftime('[%H:%M] ')+'警告:{}电机{}'.format(motorID[errorIDX[0]], errorDict[errorIDX[1]]))
                # 每个电机的设备
                for i in range(10):
                    if motor_event[i,0] == 255:
                        self.infoAuto.append(datetime.datetime.now().strftime('[%H:%M] ')+'{}电机{}'.format(motorID[i], motorDict[0]))
                    if motor_event[i,2] == 255:
                        self.infoAuto.append(datetime.datetime.now().strftime('[%H:%M] ')+'{}电机{}'.format(motorID[i], motorDict[2]))
                    if motor_event[i,3] == 255:
                        self.infoAuto.append(datetime.datetime.now().strftime('[%H:%M] ')+'{}电机{}'.format(motorID[i], motorDict[3]))
                # 每个机械臂的设备
                for i in range(4):
                    if device_event[3, i] == 1:
                        print(device_event[4, 2])
                        self.infoAuto.append(datetime.datetime.now().strftime('[%H:%M] ')+'{}相机断开'.format(armDict[i]))
                    if device_event[0, i] == 1:
                        self.infoAuto.append(datetime.datetime.now().strftime('[%H:%M] ')+'{}手爪断开'.format(armDict[i]))
                self.motorPre = motorCur
                self.devicePre = deviceCur
                self.infoAuto.moveCursor(self.infoAuto.textCursor().End)  #文本框显示到底部
                time.sleep(0.5)

    def side1(self):
        if self.camera.autoMode:
            self.helpmode()
        elif self.camera.halfAutoMode:
            self.manualmode()
        elif self.camera.manualMode:
            self.automode()

    def side2(self):
        if self.camera.autoMode:
            self.manualmode()
        elif self.camera.halfAutoMode:
            self.automode()
        elif self.camera.manualMode:
            self.helpmode()

    def selectImage(self,id):
        if id == 1:
            self.camera.id = 1
            self.cameraPick1.setStyleSheet("font-size:30px;background-color:rgb(244,177,131);border-radius: 30px")
            self.cameraPick2.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
            self.cameraPick3.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
            self.cameraPick4.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
            self.cameraPick5.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")

        if id == 2:
            self.camera.id = 2
            self.cameraPick2.setStyleSheet("font-size:30px;background-color:rgb(244,177,131);border-radius: 30px")
            self.cameraPick1.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
            self.cameraPick3.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
            self.cameraPick4.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
            self.cameraPick5.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")

        if id == 3:
            self.camera.id = 3
            self.cameraPick3.setStyleSheet("font-size:30px;background-color:rgb(244,177,131);border-radius: 30px")
            self.cameraPick2.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
            self.cameraPick1.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
            self.cameraPick4.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
            self.cameraPick5.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")

        if id == 4:
            self.camera.id = 4
            self.cameraPick4.setStyleSheet("font-size:30px;background-color:rgb(244,177,131);border-radius: 30px")
            self.cameraPick2.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
            self.cameraPick3.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
            self.cameraPick1.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
            self.cameraPick5.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")

        if id == 5:
            self.camera.id = 5  
            self.cameraPick5.setStyleSheet("font-size:30px;background-color:rgb(244,177,131);border-radius: 30px")
            self.cameraPick2.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
            self.cameraPick3.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
            self.cameraPick4.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")
            self.cameraPick1.setStyleSheet("font-size:30px;background-color:rgb(255,255,255);border-radius: 30px")

    def control(self):
        if self.mainMode == True:
            self.stackedWidget.setCurrentIndex(2)
            self.mainMode = False
        else:
            self.stackedWidget.setCurrentIndex(0)
            self.mainMode = True

    def close_mode(self):
        if gb.CONFIG_order[0] == 15:
            if self.camera.cap == True:#如果摄像头开启
                self.camera.close_camera()  # 启动 关闭摄像头的程序，close_camera为其他module中的function
                self.infoAuto.append(datetime.datetime.now().strftime('[%H:%M] ')+'关闭彩色相机')
            gb.record_order(10,0)
            gb.record_order(11,5)
            gb.record_order(12,0)
        else:
            self.slot_msg_dialog("设备已关机")

    def prepare(self):#摄像头，这就是一个摄像头按键被点击后的操作，如果原来摄像头开启，那么点击后就关闭
        if gb.CONFIG_order[0] == 15:
            if self.camera.autoMode:
                gb.record_order(11,1)
                gb.record_order(11,0,write=False)
            elif self.camera.halfAutoMode or self.camera.manualMode:
                gb.record_order(11,0)
            if self.camera.cap == False:#如果摄像头开启
                self.infoAuto.append(datetime.datetime.now().strftime('[%H:%M] ')+'开启彩色相机')
                ret = self.camera.open_camera(selection = 1)
                #ischecked（）方法在选中和半选中状态下都返回True。检查复选框是否被选中
                #ret值只有0/1，摄像头开启就返回1 
                if ret:
                    fps = 0 
                    self.infoAuto.append(datetime.datetime.now().strftime('[%H:%M] ')+'显示画面线程1开始')
                    self.camera.show_camera(fps=fps)  # 显示画面

        else:
            self.slot_msg_dialog("设备已关机")

    def oc_camera(self):#摄像头，这就是一个摄像头按键被点击后的操作，如果原来摄像头开启，那么点击后就关闭
        if gb.CONFIG_order[0] == 15:
            if self.camera.cap == True:#如果摄像头开启
                self.camera.close_camera()  # 启动 关闭摄像头的程序，close_camera为其他module中的function
                self.infoAuto.append(datetime.datetime.now().strftime('[%H:%M] ')+'关闭彩色相机')
            else:
                self.infoAuto.append(datetime.datetime.now().strftime('[%H:%M] ')+'开启彩色相机')
                ret = self.camera.open_camera(selection = 1)
                #ischecked（）方法在选中和半选中状态下都返回True。检查复选框是否被选中
                #ret值只有0/1，摄像头开启就返回1 
                if ret:
                    fps = 0 
                    self.infoAuto.append(datetime.datetime.now().strftime('[%H:%M] ')+'显示画面线程开始')
                    self.camera.show_camera(fps=fps)  # 显示画面
        else:
            self.slot_msg_dialog("设备已关机")

    def paintEvent(self,event):
        self.path_car.setScaledSize(self.title.size())

    def addMessage(self):
        if self.camera.pickListAll and self.send:
            self.helpInfo.setText(str(self.camera.dict))
        elif self.send and not self.camera.pickListAll:
            self.helpInfo.setText('[]')

    def sendMessage(self):
        msg = msg_box.MsgWarning()
        msg.setText("已选择" + str(self.camera.dict) + "\n是否开始采摘？")
        msg.exec()
        with open('config/pick.dat', 'r+') as f:
            with contextlib.closing(mmap.mmap(f.fileno(), 300, access=mmap.ACCESS_WRITE)) as m:
                pickArray = np.asarray(self.camera.pickListAll).astype(np.uint16)
                m.seek(0)
                print(pickArray)
                m.write(pickArray.flatten().tobytes())
        # if msg.clickedButton() != msg.btn_noTips:
        self.camera.pickListAll = []
    
    def clearMessage(self):
        self.camera.pickListAll = []
        self.send = True
        self.slot_msg_dialog("当前无采摘序列，请添加！")
                
    def rviz(self):
        if gb.CONFIG_order[0] == 15:
            os.system("gnome-terminal -x bash -c 'source ~/home/arl/four_arms_robot/devel/setup.bash;roslaunch /home/arl/four_arms_robot/src/four_arm_apple_picking_robot/launch/display.launch'")
        else:
            self.slot_msg_dialog("设备已关机")
    def automode(self):
        self.infoAuto.clear()
        self.infoAuto.append("【置顶消息】点击【准备】，机器人就绪")
        self.infoAuto.append("【置顶消息】点击【开启】，自动作业") 
        self.infoAuto.append("【置顶消息】点击【停止】，停止作业")                        
        self.infoAuto.append("【置顶消息】点击【复位】，机械臂复位")
        self.infoAuto.append("")
        gb.record_order(11,0)
        self.btn_side_auto.setStyleSheet("QPushButton{border-image: url(img/steam.png)}")
        self.btn_side_help.setStyleSheet("QPushButton{border-image: url(img/hand-stop-oSide.png)}")
        self.widget_XY.setStyleSheet("background-color:rgb(255,255,255,0);font-size:30px")
        self.widget_YZ.setStyleSheet("background-color:rgb(255,255,255,0);font-size:30px")
        self.grid_btnCamera.addWidget(self.camera,0,0,2,2)
        self.grid_btnCamera.addLayout(self.hbox_camera,2,0,1,2)
        self.grid_btnCamera.addLayout(self.hbox_auto,3,0,1,2)
        self.widget_XY.setParent(None)
        self.grid_btnCamera.removeWidget(self.widget_XY)

        self.widget_YZ.setParent(None)
        self.grid_btnCamera.removeWidget(self.widget_YZ)
        self.state.label_title2.setText("Unmanned operation")
        self.state.label_title.setText("无人化作业")
        gb.record_order(10,1)
        self.stackedWidget.setCurrentIndex(1)
        self.camera.opened1 = True
        self.mainMode = False
        self.camera.autoMode = True
        self.camera.halfAutoMode = False
        self.camera.manualMode = False
        self.camera.detecting = True

    def helpmode(self):
        self.infoAuto.clear()
        self.infoAuto.append("【置顶消息】点击【准备】，机器人就绪")
        self.infoAuto.append("【置顶消息】在画面中右键选取或删除目标") 
        self.infoAuto.append("【置顶消息】点击【停止】，停止作业")                        
        self.infoAuto.append("【置顶消息】点击【复位】，机械臂复位")
        self.infoAuto.append("")
        gb.record_order(11,0)
        self.btn_side_auto.setStyleSheet("QPushButton{border-image: url(img/hand-stop-oSide.png)}")
        self.btn_side_help.setStyleSheet("QPushButton{border-image: url(img/font.png)}")
        self.widget_XY.setStyleSheet("background-color:rgb(255,255,255,0);font-size:30px")
        self.widget_YZ.setStyleSheet("background-color:rgb(255,255,255,0);font-size:30px")
        self.grid_btnCamera.addWidget(self.camera,0,0,2,2)
        self.grid_btnCamera.addLayout(self.hbox_camera,2,0,1,2)
        self.grid_btnCamera.addLayout(self.hbox_auto,3,0,1,2)
        self.widget_XY.setParent(None)
        self.grid_btnCamera.removeWidget(self.widget_XY)

        self.widget_YZ.setParent(None)
        self.grid_btnCamera.removeWidget(self.widget_YZ)
        self.state.label_title2.setText("Semi automatic operation")
        self.state.label_title.setText("半自动作业")
        self.stackedWidget.setCurrentIndex(1)
        self.camera.opened1 = True
        self.mainMode = False
        self.camera.autoMode = False
        self.camera.halfAutoMode = True
        self.camera.manualMode = False
        self.camera.detecting = True

    def manualmode(self):
        self.infoAuto.clear()
        self.infoAuto.append("【置顶消息】点击【准备】，机器人就绪")
        self.infoAuto.append("【置顶消息】点击【开启】，手柄通电") 
        self.infoAuto.append("【置顶消息】操纵手柄使其与瞄准器对齐")                        
        self.infoAuto.append("【置顶消息】点击【复位】，机械臂复位")
        self.infoAuto.append("")     
        
        gb.record_order(11,0)
        self.btn_side_auto.setStyleSheet("QPushButton{border-image: url(img/font.png)}")
        self.btn_side_help.setStyleSheet("QPushButton{border-image: url(img/steam.png)}")
        self.widget_XYZ.setStyleSheet("background-color:rgb(192,192,192,140);font-size:30px")
        self.grid_btnCamera.addWidget(self.camera,0,0,2,1)
        self.grid_btnCamera.addWidget(self.widget_XY,0,1,1,1)
        self.grid_btnCamera.addWidget(self.widget_YZ,1,1,1,1)
        self.grid_btnCamera.addLayout(self.hbox_camera,2,0,1,2)
        self.grid_btnCamera.addLayout(self.hbox_auto,3,0,1,2)

        self.state.label_title2.setText("Manual operation")
        self.state.label_title.setText("人工操作作业")
        gb.record_order(10,3)
        self.stackedWidget.setCurrentIndex(1)
        self.mainMode = False
        self.camera.autoMode = False
        self.camera.manualMode = True
        self.camera.halfAutoMode = False
        self.camera.detecting = False     

    def return_main(self):
        self.mainMode = True
        self.state.label_title.setText("多臂苹果采摘机器人")
        self.state.label_title2.setText("Multi-arm Harvesting Robot for Apple")
        self.stackedWidget.setCurrentIndex(0)

    def lightControl(self):
        if gb.CONFIG_order[0] == 15:
            if gb.CONFIG_order[13] == 0:
                gb.record_order(13,1)
                self.btn_light.setStyleSheet("QPushButton{border-image: url(img/灯光打开.png)}")
            else:
                gb.record_order(13,0)
                self.btn_light.setStyleSheet("QPushButton{border-image: url(img/灯光关闭.png)}")
        else:
            self.slot_msg_dialog("设备已关机")
        
    def manipulatorAction(self):
        if gb.CONFIG_order[0] == 15:
            gb.record_order(11,2)
        else:
            self.slot_msg_dialog("设备已关机")

    def beltAction(self):
        if gb.CONFIG_order[0] == 15:
            if gb.CONFIG_order[14] == 0:
                gb.record_order(14,1)
                self.btn_belt.setStyleSheet("QPushButton{border-image: url(img/传送带运行.png)}")
                self.beltControl.setStyleSheet("QPushButton{border-image: url(img/beltControl.png)}")

            else:
                gb.record_order(14,0)
                self.btn_belt.setStyleSheet("QPushButton{border-image: url(img/传送带停止.png)}")
                self.beltControl.setStyleSheet("QPushButton{border-image: url(img/beltControl.png)}")
        else:
            self.slot_msg_dialog("设备已关机")
        
    def startPick(self):
        if gb.CONFIG_order[0] == 15:
            if self.camera.halfAutoMode:
                self.sendMessage()
            elif self.camera.autoMode:
                gb.record_order(11,4)
            elif self.camera.manualMode:
                gb.record_order(12,1)
        else:
            self.slot_msg_dialog("设备已关机")
                

    def slot_msg_dialog(self, text):#警示框
        msg = msg_box.MsgWarning()
        msg.setText(text)
        msg.exec()

    def access_msg_dialog(self, title, text):#警示框
        if self.camera.autoMode:
            if self.tips[0] == True:
                self.msg = msg_box.MsgSuccess()
                self.msg.setWindowTitle(title)
                self.msg.setText(text)
                self.msg.exec()
        elif self.camera.halfAutoMode:
            if self.tips[1] == True:
                self.msg = msg_box.MsgSuccess()
                self.msg.setWindowTitle(title)
                self.msg.setText(text)
                self.msg.exec()
        elif self.camera.manualMode:
            if self.tips[2] == True:
                self.msg = msg_box.MsgSuccess()
                self.msg.setWindowTitle(title)
                self.msg.setText(text)
                self.msg.exec()

    def resizeEvent(self, event):
        # self.ratio = self.childWidget.width() / self.childWidget.height()
        self.update()

    def closeEvent(self, event):
        if self.camera.cap == True:
            self.camera.close_camera()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

