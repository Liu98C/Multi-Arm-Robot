# # -*- coding: utf-8 -*-

"""
Author: Cheng Liu
Email: liucheng3666@163.com
Date: 2022/11/10
"""
import os
from re import I
import time
import PySide2

dirname = os.path.dirname(PySide2.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

import cv2
from PySide2.QtCore import QRect, QTimer,QPoint,QLine
from PySide2.QtGui import QPainter, QColor, Qt, QPixmap, QImage, QFont, QBrush, QPen, QStaticText,QIcon,QCursor,QPolygon,QRadialGradient
from PySide2.QtWidgets import QWidget,QMenu,QLabel,QHBoxLayout,QPushButton

import msg_box
from gb import thread_runner, YOLOGGER

import pyrealsense2 as rs
import numpy as np
import cv2
import json
import threading
import mmap, contextlib

class WidgetAppleXY(QWidget):
    def __init__(self):
        super().__init__()
        self.apple = cv2.imread('img/apple.png')
        self.appleLabel = QLabel()
        self.appleLabel.setStyleSheet('QLabel{border-image: url(img/apple.png)}')
        self.appleLabel.setFixedHeight(50)
        self.appleLabel.setFixedWidth(50)
        self.appleLabel.setAlignment(Qt.AlignCenter)
        thread = threading.Thread(target=self.delta)
        thread.start()
        self.setMinimumHeight(200)
        self.setMinimumHeight(200)
        self.setMaximumHeight(350)
        self.setMaximumWidth(350)
        layout = QHBoxLayout()
        layout.addWidget(self.appleLabel,Qt.AlignCenter)
        self.setLayout(layout)
        self._delta = []
        # self.setStyleSheet("background-color:rgb(192,192,192,140)")

    def paintEvent(self, event):#通过self.update调用
        qp = QPainter() 
        qp.begin(self) # 一个painter被通过begin（）函数被激活并且使用一个QPainterDevice参数的构造函数进行构造，调用end（）函数和析构函数解除
        self.draw(qp)
        qp.end()

    def draw(self, qp):
        qp.setWindow(0, 0, self.width(), self.height())  # 设置窗口# widget长宽
        # print(self.width(),self.height())
        qp.setRenderHint(QPainter.SmoothPixmapTransform)
        pen = QPen()
        pen.setColor(QColor(0, 0, 0))
        pen.setStyle(Qt.DashLine)
        pen.setWidth(3)
        qp.setPen(pen)
        # print(self.height())
        qp.drawText(self.width()/2, 20, 'X')
        qp.drawText(0 , self.height()/2, 'Y')
        
        qp.drawLine(QLine(0, self.height() / 2 + self._delta[2]*100,self.width(), self.height() / 2 + self._delta[2]*100))
        qp.drawLine(QLine(self.width() / 2+ self._delta[0]*100, 0,self.width() / 2+ self._delta[0]*100, self.height()))
    
    def delta(self):
        while True:
            with open('config/state.dat', 'r') as f:
                with contextlib.closing(mmap.mmap(f.fileno(), 20*20, access=mmap.ACCESS_READ)) as m:
                    self._state = m.read(400)
                    self._delta = np.frombuffer(self._state[250:274], dtype=np.float64).tolist()
            self.update()
            time.sleep(0.5)
            


class WidgetAppleYZ(QWidget):
    def __init__(self):
        super().__init__()
        self.apple = cv2.imread('img/apple.png')
        self.appleLabel = QLabel()
        self.appleLabel.setStyleSheet('QLabel{border-image: url(img/apple.png)}')
        self.appleLabel.setFixedHeight(50)
        self.appleLabel.setFixedWidth(50)
        self.appleLabel.setAlignment(Qt.AlignCenter)# QLabel在布局居中，pushbutton没有这个
        thread = threading.Thread(target=self.delta)
        thread.start()
        self.setMinimumHeight(200)
        self.setMinimumHeight(200)
        self.setMaximumHeight(350)
        self.setMaximumWidth(350)
        layout = QHBoxLayout()
        layout.addWidget(self.appleLabel,Qt.AlignCenter) # 布局中控件居中
        self.setLayout(layout)
        self._delta = []
        # self.setStyleSheet("background-color:rgb(192,192,192,140)")

    def paintEvent(self, event):#通过self.update调用
        qp = QPainter() 
        qp.begin(self) # 一个painter被通过begin（）函数被激活并且使用一个QPainterDevice参数的构造函数进行构造，调用end（）函数和析构函数解除
        self.draw(qp)
        qp.end()

    def draw(self, qp):
        qp.setWindow(0, 0, self.width(), self.height())  # 设置窗口# widget长宽
        # print(self.width(),self.height())
        qp.setRenderHint(QPainter.SmoothPixmapTransform)
        pen = QPen()
        pen.setColor(QColor(0, 0, 0))
        pen.setStyle(Qt.DashLine)
        pen.setWidth(3)
        qp.setPen(pen)
        qp.drawText(self.width()/2, 20, 'Y')
        qp.drawText(0 , self.height()/2, 'Z')
        qp.drawLine(QLine(0, self.height() / 2 + self._delta[1]*100,self.width(), self.height() / 2 + self._delta[1]*100))
        qp.drawLine(QLine(self.width() / 2+ self._delta[2]*100, 0,self.width() / 2+ self._delta[2]*100, self.height()))
        
    def delta(self):
        while True:
            with open('config/state.dat', 'r') as f:
                with contextlib.closing(mmap.mmap(f.fileno(), 20*20, access=mmap.ACCESS_READ)) as m:
                    self._state = m.read(400)
                    self._delta = np.frombuffer(self._state[250:274], dtype=np.float64).tolist()
            self.update()
            time.sleep(0.5)