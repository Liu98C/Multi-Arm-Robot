# -*- coding: utf-8 -*-
import imp
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
from PySide2.QtWidgets import (QDialog,QLineEdit, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,QSlider,
                               QWidget, QApplication, QDesktopWidget, QStyle, QLabel,QGridLayout,QGraphicsOpacityEffect,QStackedWidget,QAction,QTextEdit,QStatusBar)

import msg_box
import gb
from gb import YOLOGGER
from PySide2 import QtCore
import gb
import time
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import (FigureCanvas,NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import sip
class basketMainwindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('作业状态统计')#setting框的标题
        self.setWindowIcon(QIcon('img/baskerControl.png'))#setting框左上角图片
        self.setWindowFlags(Qt.WindowCloseButtonHint)#显示关闭按钮
        self.n = 1
        
        self.listT1 = []
        self.listT2 = []
        self.listT3 = []
        self.listT4 = []
        self.listY1 = []
        self.listY2 = []
        self.listY3 = []
        self.listY4 = []
        mpl.rcParams['font.sans-serif'] = ['AR PL UMing CN']
        mpl.rcParams['font.size'] = 12
        mpl.rcParams['axes.unicode_minus'] = False
        self.centerlayout = QVBoxLayout()
        self.__iniFigure()
        # self.__drawfFigure()
        self.ax1 = self.__fig.add_subplot(2,2,1)
        self.ax2 = self.__fig.add_subplot(2,2,2)
        self.ax3 = self.__fig.add_subplot(2,2,3)
        self.ax4 = self.__fig.add_subplot(2,2,4)
        self.setLayout(self.centerlayout)
        self.sum = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.__drawfFigure)
        self.timer.start(3000)

    def __iniFigure(self):
      self.__fig=Figure(figsize=(10, 8))    #单位尺寸，所有的绘制操作都由self.__fig完成
      self.__fig.suptitle("作业状态统计图")  #总的图标题
      figCanvas = FigureCanvas(self.__fig)  #创建FigureCanvas对象，必须传递一个Figure对象，用来承载self.__fig绘制的图像
      naviToolbar=NavigationToolbar(figCanvas, self)  #创建工具栏
      naviToolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)  
      self.centerlayout.addWidget(naviToolbar)  #添加工具栏到主窗口
      self.centerlayout.addWidget(figCanvas)  
    
    def __drawfFigure(self):
        with open('config/state.dat', 'r') as f:
            with contextlib.closing(mmap.mmap(f.fileno(), 20*20, access=mmap.ACCESS_READ)) as m:
                self._state = m.read(400)
        data = np.frombuffer(self._state[365:397], dtype=np.int32).reshape((2, 4))
        # print("data",data)
        if data[0, 0] != 0 or data[0, 1] != 0 or data[0, 2] != 0 or data[0, 3] != 0:

            # t1 = data[0,0]
            # t2 = data[0,1]
            # t3 = data[0,2]
            # t4 = data[0,3]
            t1 = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30]
            y1 = [0,1,1,2,2,3,4,5,6,7,8,8,9,10,11,12,12,13,13,14,15,16,17,18,19,20,20,21,22,23,24]
            
            t2 = [0,1,2,3,4,5,5,5,6,6,7,8,8,9,9,9,9,10,11,12,12,12,13,13,14,15,16,17,18,18,19]
            y2 = [0,1,1,2,3,4,4,4,4,4,5,6,6,6,6,6,6,7,7,8,8,8,9,9,10,11,12,13,14,14,15]
            
            t3 = [0,1,2,2,3,4,4,5,6,7,7,8,8,9,10,11,12,13,14,15,15,15,16,16,17,18,19,19,20,21,21]
            y3 = [0,1,1,1,2,3,3,4,5,5,5,6,6,7,8,9,10,11,12,13,13,13,13,13,14,15,15,15,16,17,17]
                      
            t4 = [0,1,1,2,2,3,3,4,4,5,6,7,7,8,8,9,10,11,12,12,13,13,14,15,16,16,16,17,18,19,20]
            y4 = [0,0,0,1,1,1,1,2,2,3,4,5,5,5,5,6,7,8,9,9,10,10,11,12,13,13,13,14,15,16,16]          

            # # self.sum = data[1,0] + data[1,1] + data[1,2] + data[1,3] + 4
            # self.sum = self.n
            
        
            if self.n != 1:
                self.ax1.clear()
                self.ax2.clear()
                self.ax3.clear()
                self.ax4.clear()
                
            self.__fig.canvas.draw_idle() # 有该行命令才能实时刷新
            print("self.listT1",self.listT1)
            print("self.listY1",self.listY1)
            
            self.ax1.plot(self.listT1,self.listY1,'r-o',label='机械臂1',linewidth = 1, markersize = 5)
            self.ax1.set_xlabel('抓取次数(次)')
            self.ax1.set_ylabel('成功率(%)',fontsize = 14)
            self.listT1.append(t1[self.n-1])
            if t1[self.n-1] != 0:
                self.listY1.append(y1[self.n-1]/t1[self.n-1] * 100)
            else:
                self.listY1.append(0)
            # self.ax1.set_xlim([0, 10])
            # self.ax1.set_ylim([-1.5, 1.5])
            self.ax1.legend()
            

            self.ax2.plot(self.listT2,self.listY2,'b-o',label='机械臂2',linewidth = 1, markersize = 5)
            self.ax2.set_xlabel('抓取次数')
            self.ax2.set_ylabel('成功率(%)',fontsize = 14)
            self.listT2.append(t2[self.n-1])
            if t2[self.n-1] != 0:
                self.listY2.append(y2[self.n-1]/t2[self.n-1] * 100)
            else:
                self.listY2.append(0)
            # self.ax2.set_xlim([0, 10])
            # self.ax2.set_ylim([-1.5, 1.5])
            self.ax2.legend()


            self.ax3.plot(self.listT3,self.listY3,'g-o',label='机械臂3',linewidth = 1, markersize = 5)
            self.ax3.set_xlabel('抓取次数')
            self.ax3.set_ylabel('成功率(%)',fontsize = 14)
            self.listT3.append(t3[self.n-1])
            if t3[self.n-1] != 0:
                self.listY3.append(y3[self.n-1]/t3[self.n-1] * 100)
            else:
                self.listY3.append(0)
            # self.ax3.set_xlim([0, 10])
            # self.ax3.set_ylim([-1.5, 1.5])
            self.ax3.legend()


            self.ax4.plot(self.listT4,self.listY4,'y-o',label='机械臂4',linewidth = 1, markersize = 5)
            self.ax4.set_xlabel('抓取次数')
            self.ax4.set_ylabel('成功率(%)',fontsize = 14)
            self.listT4.append(t4[self.n-1])
            if t4[self.n-1] != 0:
                self.listY4.append(y4[self.n-1]/t4[self.n-1] * 100)
            else:
                self.listY4.append(0)
            # self.ax4.set_xlim([0, 10])
            # self.ax4.set_ylim([-1.5, 1.5])
            self.ax4.legend()
            
            self.n = self.n + 1
            




