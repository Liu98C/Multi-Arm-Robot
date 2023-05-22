# # -*- coding: utf-8 -*-

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
from PySide2.QtWidgets import QWidget,QMenu,QAction

import msg_box
from gb import thread_runner, YOLOGGER

import pyrealsense2 as rs
import numpy as np
import cv2
import json
import threading
import mmap, contextlib

class WidgetCamera(QWidget):# 继承了QWidget类，所以可以直接在main中组织页面
    def __init__(self):
        super(WidgetCamera, self).__init__()
        self.opened1 = False  # 摄像头已打开
        self.opened2= False  # 摄像头已打开
        self.detecting = False  # 目标检测中

        self.i = 0
        self.p = np.array([[0,0],[640,0],[0,480],[640,480]])
        self.sum_interval = 0
        self.t0 = 0
        self.t1 = 0
        self.cap = False
        self.cap2 = False
        self.image = None  # 当前读取到的图片
        self.image2 = None  # 当前读取到的图片
        self.depthImage = None
        self.scale = 1  # 比例
        self.objects = []
        self.target = []
        self.CurrentPos = None
        self.CurrentPosDeleteList = []
        self.CurrentPosGrap = None
        self.CurrentPosGrapList = []
        self.pickList = []
        self.mouseClick = False
        self.FirstClick = False
        self.autoMode = False
        self.manualMode = False
        self.halfAutoMode = False
        self.createObjectAction = False
        self.createObjectActionManual = False
        self.Left_upper_arm = False
        self.Right_upper_arm = False
        self.Left_lower_arm = False
        self.Right_lower_arm = False
        self.createAllSignal = False
        self.xError = 0
        self.yError = 0
        self.fps = 0  # 帧率
        self.id = 5
        self.option = []
        self.colorizer = rs.colorizer()
        self.ptx = None
        self.pty = None
        self.rgb = None
        self.pickListAll = []
        self.dict = dict()

        
        # ------------------------------------------右键菜单---------------------------------------------#

    def contextMenuEvent(self, event):
        if self.halfAutoMode:
            self.eventPos = event.pos()
            self.eventPosx = self.eventPos.x()
            self.eventPosy = self.eventPos.y()
            menu = QMenu(self)
            self.createAction = QAction("选择目标", self)
            self.deleteAction = QAction("清除目标", self)
            self.createAllAction = QAction("选择全部", self)
            self.emptydeleteAction = QAction("清除全部", self)
            self.createAction.triggered.connect(self.createObject)
            self.deleteAction.triggered.connect(self.deleteObject)
            self.createAllAction.triggered.connect(self.createAllObject)
            self.emptydeleteAction.triggered.connect(self.emptydeleteObject)
            menu.addAction(self.createAction)
            menu.addAction(self.deleteAction)
            menu.addAction(self.createAllAction)
            menu.addAction(self.emptydeleteAction)
            menu.exec_(QCursor().pos())
        elif  self.manualMode:
            self.eventPos = event.pos()
            self.eventPosx = self.eventPos.x()
            self.eventPosy = self.eventPos.y()
            menu = QMenu(self)
            self.createActionManual = QAction("选择目标", self)
            self.createActionManual.triggered.connect(self.createObjectManual)
            menu.addAction(self.createActionManual)
            # menu.addAction(self.createAllAction)
            # menu.addAction(self.emptydeleteAction)
            menu.exec_(QCursor().pos())   

    def createObjectManual(self):
        self.createObjectActionManual = True
        self.CurrentPosGrapManual = [self.eventPosx - self.px,self.eventPosy - self.py] # 鼠标位置的坐标
        self.ptx = self.CurrentPosGrapManual[0]
        self.pty = self.CurrentPosGrapManual[1]
        image_x = int(self.ptx/self.ratiox)
        image_y = int(self.pty/self.ratioy)
        dis = self.depthImage[((int(self.pty/self.ratioy)), int(self.ptx/self.ratiox))] # 这是转换前的图像获取的深度，需要qpixmap中的点投影到深度图中获得实际深度图
        
        image_xyz = [image_x,image_y,dis]

        with open('config/pick.dat', 'r+') as f:
            with contextlib.closing(mmap.mmap(f.fileno(), 300, access=mmap.ACCESS_WRITE)) as m:
                pickArray = np.asarray(image_xyz).astype(np.uint16)
                m.seek(200)
                print(pickArray)
                m.write(pickArray.flatten().tobytes())

    def createObject(self):
        CurrentPosGrap = [self.eventPosx - self.px,self.eventPosy - self.py] # 鼠标位置的坐标
        ptx = CurrentPosGrap[0]
        pty = CurrentPosGrap[1]
        dis = self.depthImage[((int(pty/self.ratioy)), int(ptx/self.ratiox))] # 这是转换前的图像获取的深度，需要qpixmap中的点投影到深度图中获得实际深度图

        if dis > 1200 or dis < 400:
            msg = msg_box.MsgWarning()
            msg.setText("距离超过或小于阈值,请重新选择！")
            msg.exec()
        else:
            self.createObjectAction = True
            self.CurrentPosGrap = [self.eventPosx - self.px,self.eventPosy - self.py] # 鼠标位置的坐标
            self.CurrentPosGrapList.append(self.CurrentPosGrap)
            targetPos = [] 
            # print("image_xyz",image_xyz)
            if not self.manualMode:
                for obj in self.objects:
                    ox = round(self.pw * obj['x']) # 左上角的点
                    oy = round(self.ph * obj['y']) # 左上角的点
                    ow = round(self.pw * obj['w'])
                    oh = round(self.ph * obj['h'])
                    if self.CurrentPosGrap[0] - ox <= ow and self.CurrentPosGrap[0] - ox >= 0 and self.CurrentPosGrap[1] - oy <= oh and self.CurrentPosGrap[1] - oy >= 0:
                        targetPos = [round(ox), round(oy)] 
                        msg = msg_box.MsgWarning() 
                        msg.setText('已选择目标{}{}'.format(obj['class'],targetPos))
                        msg.exec()     

    def deleteObject(self):
        self.createObjectAction = False
        self.CurrentPos = [self.eventPosx - self.px,self.eventPosy - self.py] # 鼠标位置的坐标
        self.CurrentPosDeleteList.append(self.CurrentPos)
        targetPos = []
        # print(self.objects) 
        if not self.manualMode:
            for obj in self.objects:
                ox = round(self.pw * obj['x']) # 左上角的点
                oy = round(self.ph * obj['y']) # 左上角的点
                ow = round(self.pw * obj['w'])
                oh = round(self.ph * obj['h'])
                if self.CurrentPos[0] - ox <= ow and self.CurrentPos[0] - ox >= 0 and self.CurrentPos[1] - oy <= oh and self.CurrentPos[1] - oy >= 0:
                    targetPos = [round(ox), round(oy)]       
                    msg = msg_box.MsgWarning()
                    msg.setText('已删除目标{}{}'.format(obj['class'],targetPos))
                    msg.exec()

    def createAllObject(self):
        self.createAllSignal = True

    def emptydeleteObject(self):
        self.CurrentPosDeleteList = []
        self.CurrentPos = None    
        self.pickList = []
        self.pickListAll = []  

    def open_camera(self,selection = 1):
        """打开摄像头，成功打开返回True"""
        if selection == 1:
            self.cap = True
            YOLOGGER.info('开启相机') #YOLOGGER=logging.getLogger（）
            self.opened1 = True  # 已打开
            self.option = 0
            # self.socket.open()
            return True
        else:
            msg = msg_box.MsgWarning()
            msg.setText('摄像头开启失败')#msg.setText其实是msgBox.setText，是MsgWarning的父类QMessageBox的方法，用来在警告框中显示文字
            msg.exec()# 其实是msgBox.exec();和qt中的exec相同，执行完该行继续进行到主程序，直至点击退出
            return False
     
    def close_camera(self):#关闭摄像头的程序
        YOLOGGER.info('关闭摄像头')
        self.opened1 = False  # 先关闭目标检测线程再关闭摄像头，标志位
        self.opened2 = False  # 摄像头已打开
        # self.socket.close()
        time.sleep(0.1)  # 等待读取完最后一帧画面，读取一帧画面0.1s以内，一般0.02~0.03s；等0.1s再执行下面的程序
        self.cap = False
        self.image = None  # 当前无读取到的图片
        self.depthImage = None

    #设置FPS，显示摄像头图像而不是目标检测图像
    @thread_runner
    def show_camera(self, fps=0):
        """传入参数帧率，摄像头使用默认值0，视频一般取30|60"""
        YOLOGGER.info('显示画面线程1开始')
        # print("wait:",wait)
        self.t0 = time.time()

        while self.opened1:  # 摄像头已打开:
            time.sleep(0.075)
            with open('config/color.dat', 'r') as f:
                with contextlib.closing(mmap.mmap(f.fileno(), 480*640*12 , access=mmap.ACCESS_READ)) as m:
                    s = m.read(480*640*12)
                    image = np.frombuffer(s, dtype=np.uint8).reshape((960, 1280, 3))
                    if self.id == 1:
                        self.image = image[:480,:640,:3]
                    elif self.id == 2:
                        self.image = image[:480,640:1280,:3]
                    elif self.id == 3:
                        self.image = image[480:960,:640,:3]
                    elif self.id == 4:
                        self.image = image[480:960,640:1280,:3]                        
                    elif self.id == 5:
                        self.image = image       
                    self.image = np.ascontiguousarray(self.image)                       
                    thread = threading.Thread(target=self.updateSelf())
                    thread.start()
            with open('config/depth.dat', 'r') as f:
                with contextlib.closing(mmap.mmap(f.fileno(), 480*640*8 , access=mmap.ACCESS_READ)) as m:
                    s = m.read(480*640*8)
                    depthImage = np.frombuffer(s, dtype=np.uint16).reshape((960, 1280))
                    if self.id == 1:
                        self.depthImage = depthImage[:480,:640]
                    elif self.id == 2:
                        self.depthImage = depthImage[:480,640:1280]
                    elif self.id == 3:
                        self.depthImage = depthImage[480:960,:640]
                    elif self.id == 4:
                        self.depthImage = depthImage[480:960,640:1280]                        
                    elif self.id == 5:
                        self.depthImage = depthImage     
                    self.depthImage = np.ascontiguousarray(self.depthImage)                
                    thread = threading.Thread(target=self.updateSelf())
                    thread.start()
        self.update()
        YOLOGGER.info('显示画面线程1结束')

    def reset(self):
        """恢复初始状态"""
        self.scale = 1  # 比例无
        self.mouseClick = False

    def updateSelf(self):
        self.update()

    def resizeEvent(self, event):
        self.update()   

    def mouseDoubleClickEvent(self, event):
        pt = event.pos()
        self.mouseClick = True
        self.FirstClick == True
        if event.button() == Qt.LeftButton:
            print("图像坐标系：点击位置坐标为", [pt.x() - self.px, pt.y() - self.py])# widget长宽       
            if pt.y() - self.py < 0 or pt.y() - self.py >= self.ph or pt.x() - self.px < 0 or pt.x() - self.px >= self.pw:
                msg = msg_box.MsgSuccess()
                msg.setText('请点击图片内像素')
                msg.exec()
            self.dis = self.depthImage[((int((pt.y() - self.py)/self.ratioy)), int((pt.x() - self.px)/self.ratiox))] # 这是转换前的图像获取的深度，需要qpixmap中的点投影到深度图中获得实际深度图
            qimage = self.qpixmap.toImage()
            pix = qimage.pixel(pt.x() - self.px, pt.y() - self.py)
            pix = QColor(pix)
            r = pix.red()
            g = pix.green()
            b = pix.blue()
            self.ptx = pt.x() - self.px
            self.pty = pt.y() - self.py
            self.rgb = [r,g,b]
            image_x = int(self.ptx/self.ratiox)
            image_y = int(self.pty/self.ratioy)
            image_xyz = [image_x,image_y,self.dis]
            with open('config/pick.dat', 'r+') as f:
                with contextlib.closing(mmap.mmap(f.fileno(), 300, access=mmap.ACCESS_WRITE)) as m:
                    pickArray = np.asarray(image_xyz).astype(np.uint16)
                    m.seek(200)
                    print(pickArray)
                    m.write(pickArray.flatten().tobytes())
            self.update()
    

    def paintEvent(self, event):#通过self.update调用
        qp = QPainter() 
        qp.begin(self) # 一个painter被通过begin（）函数被激活并且使用一个QPainterDevice参数的构造函数进行构造，调用end（）函数和析构函数解除
        self.draw(qp)
        qp.end()

    def draw(self, qp):
        qp.setWindow(0, 0, self.width(), self.height())  # 设置窗口# widget长宽
        # print(self.width(),self.height())
        qp.setRenderHint(QPainter.SmoothPixmapTransform)
        # 画框架背景
        qp.setBrush(QColor('#cecece'))  # 框架背景色
        qp.setPen(Qt.NoPen)
        rect = QRect(0, 0, self.width(), self.height())
        qp.drawRect(rect)

        sw, sh = self.width(), self.height()  # 图像窗口宽高


        # 画图
        if self.opened1 and self.image is not None:
            ih, iw, _ = self.image.shape
            self.scale = sw / iw if sw / iw < sh / ih else sh / ih  # 缩放比例

            # 画第一个图像
            self.px = round((sw - iw * self.scale) / 2) # self.px显示图像左上角在窗口的相对位置，pw是qpixmap中x的位置最后还要转到self.px
            self.py = round((sh - ih * self.scale) / 2)
            qimage = QImage(self.image.data, iw, ih, 3 * iw, QImage.Format_BGR888)  # 转QImage
            self.qpixmap = QPixmap.fromImage(qimage.scaled(sw, sh, Qt.KeepAspectRatio))  # 保持指定长宽比转QPixmap
            self.pw, self.ph = self.qpixmap.width(), self.qpixmap.height()  # 缩放后的QPixmap大小
            self.ratiox = self.pw / iw 
            self.ratioy = self.ph / ih 
            qp.drawPixmap(self.px, self.py, self.qpixmap)

            # ----------------------------------方向提示----------------------------------------#
            if self.manualMode :
                with open('config/joy.dat', 'r') as f:
                    with contextlib.closing(mmap.mmap(f.fileno(), 36, access=mmap.ACCESS_READ)) as m:
                        s = m.read(36)
                        axes = np.frombuffer(s[0:24], dtype=np.float32)
                        buttons = np.frombuffer(s[24:36], dtype=np.uint8)
                        time.sleep(0.1)
                # print(buttons)
                if self.id == 5:
                    if buttons[5] == 1:
                        top11 = QPoint(self.px + 100,self.py) 
                        left11 = QPoint(self.px + 75,self.py + 80) 
                        center11 = QPoint(self.px + 100,self.py + 50) 
                        right11 = QPoint(self.px + 125,self.py + 80) 
                        polygon11  = QPolygon([top11,left11,center11,right11]) 
                        brush_direction11 = QBrush(QColor(0,0,255,255*np.maximum(axes[1], 0))) 
                        qp.setBrush(brush_direction11)
                        qp.drawPolygon(polygon11)

                        top12 = QPoint(self.px,self.py + 100) 
                        left12 = QPoint(self.px + 80,self.py + 75) 
                        center12 = QPoint(self.px + 50,self.py + 100) 
                        right12 = QPoint(self.px + 80,self.py + 125) 
                        polygon12  = QPolygon([top12,left12,center12,right12])
                        brush_direction12 = QBrush(QColor(0,0,255,255*np.maximum(axes[0], 0))) 
                        qp.setBrush(brush_direction12)
                        qp.drawPolygon(polygon12)
                        

                        top13 = QPoint(self.px + 200,self.py + 100) 
                        left13 = QPoint(self.px + 120,self.py + 75) 
                        center13 = QPoint(self.px + 150,self.py + 100) 
                        right13 = QPoint(self.px + 120,self.py + 125) 
                        polygon13  = QPolygon([top13,left13,center13,right13])
                        brush_direction13 = QBrush(QColor(0,0,255,255*np.maximum(-axes[0], 0))) 
                        qp.setBrush(brush_direction13)
                        qp.drawPolygon(polygon13)

                        top14  = QPoint(self.px + 100,self.py + 200) 
                        left14 = QPoint(self.px + 125,self.py + 120) 
                        center14 = QPoint(self.px + 100,self.py + 150) 
                        right14 = QPoint(self.px + 75,self.py + 120) 
                        polygon14  = QPolygon([top14,left14,center14,right14])
                        brush_direction14 = QBrush(QColor(0,0,255,255*np.maximum(-axes[1], 0))) 
                        qp.setBrush(brush_direction14)
                        qp.drawPolygon(polygon14)

                    elif buttons[4] == 1:
                        top21 = QPoint(self.px + self.qpixmap.width() / 2 + 100, self.py) 
                        left21 = QPoint(self.px + self.qpixmap.width() / 2 + 75, self.py + 80) 
                        center21 = QPoint(self.px + self.qpixmap.width() / 2 + 100, self.py + 50) 
                        right21 = QPoint(self.px + self.qpixmap.width() / 2 + 125, self.py + 80) 
                        polygon21  = QPolygon([top21,left21,center21,right21])
                        brush_direction21 = QBrush(QColor(0,0,255,255*np.maximum(axes[1], 0))) 
                        qp.setBrush(brush_direction21)
                        qp.drawPolygon(polygon21)


                        top22 = QPoint(self.px + self.qpixmap.width() / 2, self.py + 100) 
                        left22 = QPoint(self.px + self.qpixmap.width() / 2 + 80, self.py + 75) 
                        center22 = QPoint(self.px + self.qpixmap.width() / 2 + 50, self.py + 100) 
                        right22 = QPoint(self.px + self.qpixmap.width() / 2 + 80, self.py + 125) 
                        polygon22  = QPolygon([top22,left22,center22,right22])
                        brush_direction22 = QBrush(QColor(0,0,255,255*np.maximum(axes[0], 0))) 
                        qp.setBrush(brush_direction22)
                        qp.drawPolygon(polygon22)

                        top23 = QPoint(self.px + self.qpixmap.width() / 2 + 200, self.py + 100) 
                        left23 = QPoint(self.px + self.qpixmap.width() / 2 + 120, self.py + 75) 
                        center23 = QPoint(self.px + self.qpixmap.width() / 2 + 150, self.py + 100) 
                        right23 = QPoint(self.px + self.qpixmap.width() / 2 + 120, self.py + 125) 
                        polygon23  = QPolygon([top23,left23,center23,right23])
                        brush_direction23 = QBrush(QColor(0,0,255,255*np.maximum(-axes[0], 0))) 
                        qp.setBrush(brush_direction23)
                        qp.drawPolygon(polygon23)

                        top24 = QPoint(self.px + self.qpixmap.width() / 2 + 100, self.py + 200) 
                        left24 = QPoint(self.px + self.qpixmap.width() / 2 + 125, self.py + 120) 
                        center24= QPoint(self.px + self.qpixmap.width() / 2 + 100, self.py + 150) 
                        right24 = QPoint(self.px + self.qpixmap.width() / 2 + 75, self.py + 120) 
                        polygon24  = QPolygon([top24,left24,center24,right24])
                        brush_direction24 = QBrush(QColor(0,0,255,255*np.maximum(-axes[1], 0))) 
                        qp.setBrush(brush_direction24)
                        qp.drawPolygon(polygon24)
                    elif buttons[3] == 1:
                        top31 = QPoint(self.px + 100,self.py + self.qpixmap.height() / 2) 
                        left31 = QPoint(self.px + 75,self.py + self.qpixmap.height() / 2 + 80) 
                        center31 = QPoint(self.px + 100,self.py + self.qpixmap.height() / 2 + 50) 
                        right31 = QPoint(self.px + 125,self.py + self.qpixmap.height() / 2 + 80) 
                        polygon31  = QPolygon([top31,left31,center31,right31])
                        brush_direction3 = QBrush(QColor(0,0,255,255*np.maximum(axes[1], 0))) 
                        qp.setBrush(brush_direction3)
                        qp.drawPolygon(polygon31)


                        top32 = QPoint(self.px,self.py + self.qpixmap.height() / 2 + 100) 
                        left32 = QPoint(self.px + 80,self.py + self.qpixmap.height() / 2 + 75) 
                        center32 = QPoint(self.px + 50,self.py + self.qpixmap.height() / 2 + 100) 
                        right32 = QPoint(self.px + 80,self.py + self.qpixmap.height() / 2 + 125) 
                        polygon32  = QPolygon([top32,left32,center32,right32])
                        brush_direction32 = QBrush(QColor(0,0,255,255*np.maximum(axes[0], 0))) 
                        qp.setBrush(brush_direction32)
                        qp.drawPolygon(polygon32)

                        top33 = QPoint(self.px + 200,self.py + self.qpixmap.height() / 2 + 100) 
                        left33 = QPoint(self.px + 120,self.py + self.qpixmap.height() / 2 + 75) 
                        center33 = QPoint(self.px + 150,self.py + self.qpixmap.height() / 2 + 100) 
                        right33 = QPoint(self.px + 120,self.py + self.qpixmap.height() / 2 + 125) 
                        polygon33  = QPolygon([top33,left33,center33,right33])
                        brush_direction33 = QBrush(QColor(0,0,255,255*np.maximum(-axes[0], 0))) 
                        qp.setBrush(brush_direction33)
                        qp.drawPolygon(polygon33)

                        top34 = QPoint(self.px + 100,self.py + self.qpixmap.height() / 2 + 200) 
                        left34 = QPoint(self.px + 125,self.py + self.qpixmap.height() / 2 + 120) 
                        center34 = QPoint(self.px + 100,self.py + self.qpixmap.height() / 2 + 150) 
                        right34 = QPoint(self.px + 75,self.py + self.qpixmap.height() / 2 + 120) 
                        polygon34  = QPolygon([top34,left34,center34,right34])
                        brush_direction34 = QBrush(QColor(0,0,255,255*np.maximum(-axes[1], 0))) 
                        qp.setBrush(brush_direction34)
                        qp.drawPolygon(polygon34)
                    elif buttons[2] == 1:
                        top41 = QPoint(self.px + self.qpixmap.width() / 2 + 100,self.py + self.qpixmap.height() / 2) 
                        left41 = QPoint(self.px + self.qpixmap.width() / 2 + 75,self.py + self.qpixmap.height() / 2 + 80) 
                        center41 = QPoint(self.px + self.qpixmap.width() / 2 + 100,self.py + self.qpixmap.height() / 2 + 50) 
                        right41 = QPoint(self.px + self.qpixmap.width() / 2 + 125,self.py + self.qpixmap.height() / 2 + 80) 
                        polygon41  = QPolygon([top41,left41,center41,right41])
                        brush_direction41 = QBrush(QColor(0,0,255,255*np.maximum(axes[1], 0))) 
                        qp.setBrush(brush_direction41)
                        qp.drawPolygon(polygon41)
                        
                        top42 = QPoint(self.px + self.qpixmap.width() / 2,self.py + self.qpixmap.height() / 2 + 100) 
                        left42 = QPoint(self.px + self.qpixmap.width() / 2 + 80,self.py + self.qpixmap.height() / 2 + 75) 
                        center42 = QPoint(self.px + self.qpixmap.width() / 2 + 50,self.py + self.qpixmap.height() / 2 + 100) 
                        right42 = QPoint(self.px + self.qpixmap.width() / 2 + 80,self.py + self.qpixmap.height() / 2 + 125) 
                        polygon42  = QPolygon([top42,left42,center42,right42])
                        brush_direction42 = QBrush(QColor(0,0,255,255*np.maximum(axes[0], 0))) 
                        qp.setBrush(brush_direction42)
                        qp.drawPolygon(polygon42)

                        top43 = QPoint(self.px + self.qpixmap.width() / 2 + 200,self.py + self.qpixmap.height() / 2 + 100) 
                        left43 = QPoint(self.px + self.qpixmap.width() / 2 + 120,self.py + self.qpixmap.height() / 2 + 75) 
                        center43 = QPoint(self.px + self.qpixmap.width() / 2 + 150,self.py + self.qpixmap.height() / 2 + 100) 
                        right43 = QPoint(self.px + self.qpixmap.width() / 2 + 120,self.py + self.qpixmap.height() / 2 + 125) 
                        polygon43  = QPolygon([top43,left43,center43,right43])
                        brush_direction43 = QBrush(QColor(0,0,255,255*np.maximum(-axes[0], 0))) 
                        qp.setBrush(brush_direction43)
                        qp.drawPolygon(polygon43)

                        top44 = QPoint(self.px + self.qpixmap.width() / 2 + 100,self.py + self.qpixmap.height() / 2 + 200) 
                        left44 = QPoint(self.px + self.qpixmap.width() / 2 + 125,self.py + self.qpixmap.height() / 2 + 120) 
                        center44 = QPoint(self.px + self.qpixmap.width() / 2 + 100,self.py + self.qpixmap.height() / 2 + 150) 
                        right44 = QPoint(self.px + self.qpixmap.width() / 2 + 75,self.py + self.qpixmap.height() / 2 + 120) 
                        polygon44  = QPolygon([top44,left44,center44,right44])
                        brush_direction44 = QBrush(QColor(0,0,255,255*np.maximum(-axes[1], 0))) 
                        qp.setBrush(brush_direction44)
                        qp.drawPolygon(polygon44)
                # ---------------------------------伸缩指示---------------------------------------------#
                    pen = QPen()
                    pen.setWidth(5)
                    qp.setBrush(QColor(0,0,0,0))
                    if buttons[5]==1:
                        pen.setColor(QColor(0,0,255,255*np.maximum(axes[3], 0)))
                        qp.setPen(pen)
                        qp.drawPoint(self.px + 100,self.py + 100)
                        qp.drawEllipse(self.px + 75, self.py + 75, 50, 50)

                        pen.setColor(QColor(0,0,255,255*np.maximum(-axes[3], 0)))
                        qp.setPen(pen)
                        firstPoint11 =  QPoint(self.px + 85, self.py + 85)
                        lastPoint11 =  QPoint(self.px + 115, self.py + 115)
                        firstPoint12 =  QPoint(self.px + 115, self.py + 85)
                        lastPoint12 =  QPoint(self.px + 85, self.py + 115)
                        qp.drawLine(firstPoint11, lastPoint11)
                        qp.drawLine(firstPoint12, lastPoint12)
                        qp.drawEllipse(self.px + 75, self.py + 75, 50, 50)
                    elif buttons[4]==1:

                        pen.setColor(QColor(0,0,255,255*np.maximum(axes[3], 0)))
                        qp.setPen(pen)
                        qp.drawPoint(self.px + self.qpixmap.width() / 2 + 100,self.py + 100)
                        qp.drawEllipse(self.px + self.qpixmap.width() / 2 + 75, self.py + 75, 50, 50)

                        pen.setColor(QColor(0,0,255,255*np.maximum(-axes[3], 0)))
                        qp.setPen(pen)
                        firstPoint11 =  QPoint(self.px + self.qpixmap.width() / 2 + 85, self.py + 85)
                        lastPoint11 =  QPoint(self.px + self.qpixmap.width() / 2 + 115, self.py + 115)
                        firstPoint12 =  QPoint(self.px + self.qpixmap.width() / 2 + 115, self.py + 85)
                        lastPoint12 =  QPoint(self.px + self.qpixmap.width() / 2 + 85, self.py + 115)
                        qp.drawLine(firstPoint11, lastPoint11)
                        qp.drawLine(firstPoint12, lastPoint12)
                        qp.drawEllipse(self.px + self.qpixmap.width() / 2 + 75, self.py + 75, 50, 50)
                    elif buttons[3]==1:

                        pen.setColor(QColor(0,0,255,255*np.maximum(axes[3], 0)))
                        qp.setPen(pen)
                        qp.drawPoint(self.px + 100,self.py + self.qpixmap.height() / 2 + 100)
                        qp.drawEllipse(self.px + 75, self.py + self.qpixmap.height() / 2 + 75, 50, 50)

                        pen.setColor(QColor(0,0,255,255*np.maximum(-axes[3], 0)))
                        qp.setPen(pen)
                        firstPoint11 =  QPoint(self.px + 85, self.py + self.qpixmap.height() / 2 + 85)
                        lastPoint11 =  QPoint(self.px + 115, self.py + self.qpixmap.height() / 2 + 115)
                        firstPoint12 =  QPoint(self.px + 115, self.py + self.qpixmap.height() / 2 + 85)
                        lastPoint12 =  QPoint(self.px + 85, self.py + self.qpixmap.height() / 2 + 115)
                        qp.drawLine(firstPoint11, lastPoint11)
                        qp.drawLine(firstPoint12, lastPoint12)
                        qp.drawEllipse(self.px + 75, self.py + self.qpixmap.height() / 2 + 75, 50, 50)
                    elif buttons[2]==1: 
                        
                        pen.setColor(QColor(0,0,255,255*np.maximum(axes[3], 0)))
                        qp.setPen(pen)
                        qp.drawPoint(self.px + self.qpixmap.width() / 2 + 100,self.py+ self.qpixmap.height() / 2 + 100)
                        qp.drawEllipse(self.px + self.qpixmap.width() / 2 + 75, self.py + self.qpixmap.height() / 2 + 75, 50, 50)        

                        pen.setColor(QColor(0,0,255,255*np.maximum(-axes[3], 0)))
                        qp.setPen(pen)
                        firstPoint11 =  QPoint(self.px + self.qpixmap.width() / 2 + 85, self.py + self.qpixmap.height() / 2 + 85)
                        lastPoint11 =  QPoint(self.px + self.qpixmap.width() / 2 + 115, self.py + self.qpixmap.height() / 2 + 115)
                        firstPoint12 =  QPoint(self.px + self.qpixmap.width() / 2 + 115, self.py + self.qpixmap.height() / 2 + 85)
                        lastPoint12 =  QPoint(self.px + self.qpixmap.width() / 2 + 85, self.py + self.qpixmap.height() / 2 + 115)
                        qp.drawLine(firstPoint11, lastPoint11)
                        qp.drawLine(firstPoint12, lastPoint12)
                        qp.drawEllipse(self.px + self.qpixmap.width() / 2 + 75, self.py + self.qpixmap.height() / 2 + 75, 50, 50)        
            if self.detecting:
                self.pickList = []
                with open('config/res.dat', 'r') as f:
                    with contextlib.closing(mmap.mmap(f.fileno(), 1600 , access=mmap.ACCESS_READ)) as m:
                        r = m.read(1600)
                        res = [None for i in range(4)]
                        if self.id == 1:
                            i = 0
                            valuex = 0
                            valuey = 0
                        elif self.id == 2:
                            i = 1
                            valuex = 640
                            valuey = 0
                        elif self.id == 3:
                            i = 2
                            valuex = 0
                            valuey = 480
                        elif self.id == 4:
                            i = 3
                            valuex = 640
                            valuey = 480
                        if self.id != 5:
                            res[i] = r[400*i: 400*(i+1)]
                            bbox = np.frombuffer(res[i], dtype=np.uint16).reshape((-1, 2))
                            idx = np.where(np.sum(bbox, axis=1)==0)[0]
                            bbox = np.delete(bbox, idx, axis=0)+self.p[i]
                            for j in range(bbox.shape[0]):
                                if self.autoMode:
                                    cv2.rectangle(self.image, (bbox[j,0]-30 - valuex, bbox[j,1]-30 - valuey), (bbox[j,0]+30 - valuex, bbox[j,1]+30 - valuey), (255,0,255), 2)
                                if self.CurrentPosGrap:
                                    self.pickList.append([self.CurrentPosGrap[0]/self.ratiox+valuex, self.CurrentPosGrap[1]/self.ratioy+valuey, self.depthImage[int(self.CurrentPosGrap[1]/self.ratioy), int(self.CurrentPosGrap[0]/self.ratiox)]])
                                    self.pickListAll.append(self.pickList)
                                    self.CurrentPosGrap = []
                        else:
                            for i in range(4):
                                res[i] = r[400*i: 400*(i+1)]
                                bbox = np.frombuffer(res[i], dtype=np.uint16).reshape((-1, 2))
                                idx = np.where(np.sum(bbox, axis=1)==0)[0]
                                bbox = np.delete(bbox, idx, axis=0)+self.p[i]
                                for j in range(bbox.shape[0]):
                                    if self.autoMode:
                                        cv2.rectangle(self.image, (bbox[j,0]-30, bbox[j,1]-30), (bbox[j,0]+30, bbox[j,1]+30), (255,0,255), 2)
                                    if self.CurrentPosGrap:
                                        # print(self.depthImage.shape)
                                        # print(self.depthImage[int(self.CurrentPosGrap[1]/self.ratioy), int(self.CurrentPosGrap[0]/self.ratiox)])
                                        if self.depthImage[int(self.CurrentPosGrap[1]/self.ratioy), int(self.CurrentPosGrap[0]/self.ratiox)] != 0:
                                            self.pickList.append([self.CurrentPosGrap[0]/self.ratiox, self.CurrentPosGrap[1]/self.ratioy, self.depthImage[int(self.CurrentPosGrap[1]/self.ratioy), int(self.CurrentPosGrap[0]/self.ratiox)]])
                                        else:
                                            for j in range(20):
                                                if self.depthImage[int((self.CurrentPosGrap[1]+j)/self.ratioy), int(self.CurrentPosGrap[0]/self.ratiox)] ==0:
                                                
                                                    j = j + 1
                                                    break
                                                else:
                                                    self.pickList.append([self.CurrentPosGrap[0]/self.ratiox, self.CurrentPosGrap[1]/self.ratioy, self.depthImage[int((self.CurrentPosGrap[1]+j)/self.ratioy), int(self.CurrentPosGrap[0]/self.ratiox)]])
                                        self.pickListAll.append(self.pickList) # 将单个苹果序列添加到总采摘序列中
                                        self.CurrentPosGrap = []
                "手动删除目标"
                for object in self.pickListAll: 
                    if self.CurrentPos and abs(self.CurrentPos[0] - object[0][0]*self.ratiox)<=30 and abs(self.CurrentPos[1] - object[0][1]*self.ratioy)<=30:
                        self.pickListAll.remove(object)
                        self.CurrentPos = []
                        
                "标注目标信息"
                for i in range(len(self.pickListAll)):
                    cv2.rectangle(self.image, (int(self.pickListAll[i][0][0])-30, int(self.pickListAll[i][0][1])-30), (int(self.pickListAll[i][0][0])+30, int(self.pickListAll[i][0][1])+30), (255,0,255), 2)

                    pen = QPen()
                    pen.setColor(QColor(255, 255, 255)) # 255-是为了和背景颜色区分开
                    pen.setWidth(5)
                    qp.setPen(pen)
                    if self.id == 1:
                        valuex = 0
                        valuey = 0
                    elif self.id == 2:
                        valuex = 640
                        valuey = 0
                    elif self.id == 3:
                        valuex = 0
                        valuey = 480
                    elif self.id == 4:
                        valuex = 640
                        valuey = 480
                    if self.id == 5:
                        qp.drawText(self.px + self.pickListAll[i][0][0]*self.ratiox, self.py + self.pickListAll[i][0][1]*self.ratioy, str("采摘目标{}".format(i+1)))
                        cv2.rectangle(self.image, (int(self.pickListAll[i][0][0])-30, int(self.pickListAll[i][0][1])-30), (int(self.pickListAll[i][0][0])+30, int(self.pickListAll[i][0][1])+30), (255,0,255), 2)
                    else:
                        qp.drawText(self.px + (self.pickListAll[i][0][0] - valuex)*self.ratiox, self.py + (self.pickListAll[i][0][1] - valuey)*self.ratioy, str("采摘目标{}".format(i+1)))
                        cv2.rectangle(self.image, (int(self.pickListAll[i][0][0]- valuex)-30, int(self.pickListAll[i][0][1] - valuey)-30), (int(self.pickListAll[i][0][0]- valuex)+30, int(self.pickListAll[i][0][1] - valuey)+30), (255,0,255), 2)                            
                self.dict = dict()
                for k in range(len(self.pickListAll)):
                    self.dict['采摘目标{}'.format(k+1)] = self.pickListAll[k][0]
                self.createAllSignal = False
                    # print("self.dict",self.dict)


            # -----------------------------------------FPS-----------------------------------------#
            self.t1 = time.time()
            self.i = self.i + 1
            interval = self.t1 - self.t0
            self.sum_interval = self.sum_interval + interval
            if self.sum_interval > 1:
                self.fps = self.i 
                self.i = 0
                self.sum_interval = 0
            self.t0 = time.time()
            font = QFont()
            font.setFamily('Microsoft YaHei')
            # if self.fps > 0:
            font.setPointSize(12)
            qp.setFont(font)
            pen = QPen()
            pen.setColor(Qt.white)
            qp.setPen(pen)
            qp.drawStaticText(self.width()-60, self.py + 10, QStaticText('FPS: ' + str(round(self.fps, 2))))  

            if self.mouseClick == True and self.rgb is not None and self.ptx is not None and self.pty is not None:
                font = QFont()
                font.setFamily('Microsoft YaHei')
                font.setPointSize(12)
                qp.setFont(font)
                pen = QPen()
                pen.setColor(QColor(255-self.rgb[0], 255-self.rgb[1], 255-self.rgb[2])) # 255-是为了和背景颜色区分开
                qp.setPen(pen)
                qp.drawText(self.ptx , self.pty, 'RGB{}'.format(self.rgb))
                qp.drawText(self.ptx , self.pty + 15, '深度值{}'.format(self.dis))
                qp.drawText(self.ptx , self.pty + 30, '图像坐标系{}'.format([self.ptx,self.pty]))

            if self.manualMode == True: 

                pen = QPen()
                pen.setColor(QColor(255, 255, 255))
                pen.setWidth(3)
                qp.setPen(pen)
                # print(self.ratiox)
                if self.id == 5:
                    qp.drawEllipse(self.px+481.027/1280*self.pw-15, self.py+795.425/960*self.ph-15, 30, 30) # 左下
                    qp.drawEllipse(self.px+886.681/1280*self.pw-15, self.py+807.768/960*self.ph-15, 30, 30) # 右下
                    qp.drawEllipse(self.px+457.730/1280*self.pw-15, self.py+325.027/960*self.ph-15, 30, 30) # 左上
                    qp.drawEllipse(self.px+879.829/1280*self.pw-15, self.py+335.198/960*self.ph-15, 30, 30) # 右上

                    pointAimuUp1 =  QPoint(self.px+481.027/1280*self.pw, self.py+795.425/960*self.ph-15)
                    pointAimuUp2 =  QPoint(self.px+481.027/1280*self.pw, self.py+795.425/960*self.ph-15-10)
                    pointAimuLeft1 =  QPoint(self.px+481.027/1280*self.pw-15, self.py+795.425/960*self.ph)
                    pointAimuLeft2 =  QPoint(self.px+481.027/1280*self.pw-15-10, self.py+795.425/960*self.ph)
                    pointAimuRight1 =  QPoint(self.px+481.027/1280*self.pw+15, self.py+795.425/960*self.ph)
                    pointAimuRight2 =  QPoint(self.px+481.027/1280*self.pw+15+10, self.py+795.425/960*self.ph)
                    pointAimuDown1 =  QPoint(self.px+481.027/1280*self.pw, self.py+795.425/960*self.ph+15)
                    pointAimuDown2 =  QPoint(self.px+481.027/1280*self.pw, self.py+795.425/960*self.ph+15+10)

                    pointAimuUp12 =  QPoint(self.px+886.681/1280*self.pw, self.py+807.768/960*self.ph-15)
                    pointAimuUp22 =  QPoint(self.px+886.681/1280*self.pw, self.py+807.768/960*self.ph-15-10)
                    pointAimuLeft12 =  QPoint(self.px+886.681/1280*self.pw-15, self.py+807.768/960*self.ph)
                    pointAimuLeft22 =  QPoint(self.px+886.681/1280*self.pw-15-10, self.py+807.768/960*self.ph)
                    pointAimuRight12 =  QPoint(self.px+886.681/1280*self.pw+15, self.py+807.768/960*self.ph)
                    pointAimuRight22 =  QPoint(self.px+886.681/1280*self.pw+15+10, self.py+807.768/960*self.ph)
                    pointAimuDown12 =  QPoint(self.px+886.681/1280*self.pw, self.py+807.768/960*self.ph+15)
                    pointAimuDown22 =  QPoint(self.px+886.681/1280*self.pw, self.py+807.768/960*self.ph+15+10)

                    pointAimuUp13 =  QPoint(self.px+457.730/1280*self.pw, self.py+325.027/960*self.ph-15)
                    pointAimuUp23 =  QPoint(self.px+457.730/1280*self.pw, self.py+325.027/960*self.ph-15-10)
                    pointAimuLeft13 =  QPoint(self.px+457.730/1280*self.pw-15, self.py+325.027/960*self.ph)
                    pointAimuLeft23 =  QPoint(self.px+457.730/1280*self.pw-15-10, self.py+325.027/960*self.ph)
                    pointAimuRight13 =  QPoint(self.px+457.730/1280*self.pw+15, self.py+325.027/960*self.ph)
                    pointAimuRight23 =  QPoint(self.px+457.730/1280*self.pw+15+10, self.py+325.027/960*self.ph)
                    pointAimuDown13 =  QPoint(self.px+457.730/1280*self.pw, self.py+325.027/960*self.ph+15)
                    pointAimuDown23 =  QPoint(self.px+457.730/1280*self.pw, self.py+325.027/960*self.ph+15+10)
                    
                    pointAimuUp14 =  QPoint(self.px+879.829/1280*self.pw, self.py+335.198/960*self.ph-15)
                    pointAimuUp24 =  QPoint(self.px+879.829/1280*self.pw, self.py+335.198/960*self.ph-15-10)
                    pointAimuLeft14 =  QPoint(self.px+879.829/1280*self.pw-15, self.py+335.198/960*self.ph)
                    pointAimuLeft24 =  QPoint(self.px+879.829/1280*self.pw-15-10, self.py+335.198/960*self.ph)
                    pointAimuRight14 =  QPoint(self.px+879.829/1280*self.pw+15, self.py+335.198/960*self.ph)
                    pointAimuRight24 =  QPoint(self.px+879.829/1280*self.pw+15+10, self.py+335.198/960*self.ph)
                    pointAimuDown14 =  QPoint(self.px+879.829/1280*self.pw, self.py+335.198/960*self.ph+15)
                    pointAimuDown24 =  QPoint(self.px+879.829/1280*self.pw, self.py+335.198/960*self.ph+15+10)            
                    qp.drawLine(pointAimuUp1, pointAimuUp2)
                    qp.drawLine(pointAimuLeft1, pointAimuLeft2)
                    qp.drawLine(pointAimuRight1, pointAimuRight2)
                    qp.drawLine(pointAimuDown1, pointAimuDown2)

                    qp.drawLine(pointAimuUp12, pointAimuUp22)
                    qp.drawLine(pointAimuLeft12, pointAimuLeft22)
                    qp.drawLine(pointAimuRight12, pointAimuRight22)
                    qp.drawLine(pointAimuDown12, pointAimuDown22)

                    qp.drawLine(pointAimuUp13, pointAimuUp23)
                    qp.drawLine(pointAimuLeft13, pointAimuLeft23)
                    qp.drawLine(pointAimuRight13, pointAimuRight23)
                    qp.drawLine(pointAimuDown13, pointAimuDown23)
                    
                    qp.drawLine(pointAimuUp14, pointAimuUp24)
                    qp.drawLine(pointAimuLeft14, pointAimuLeft24)
                    qp.drawLine(pointAimuRight14, pointAimuRight24)
                    qp.drawLine(pointAimuDown14, pointAimuDown24)
                elif self.id == 3:
                    qp.drawEllipse(self.px+481.027/640*self.pw-15, self.py+(795.425-480)/480*self.ph-15, 30, 30) # 左下

                    pointAimuUp1 =  QPoint(self.px+481.027/640*self.pw, self.py+(795.425-480)/480*self.ph-15)
                    pointAimuUp2 =  QPoint(self.px+481.027/640*self.pw, self.py+(795.425-480)/480*self.ph-15-10)
                    pointAimuLeft1 =  QPoint(self.px+481.027/640*self.pw-15, self.py+(795.425-480)/480*self.ph)
                    pointAimuLeft2 =  QPoint(self.px+481.027/640*self.pw-15-10, self.py+(795.425-480)/480*self.ph)
                    pointAimuRight1 =  QPoint(self.px+481.027/640*self.pw+15, self.py+(795.425-480)/480*self.ph)
                    pointAimuRight2 =  QPoint(self.px+481.027/640*self.pw+15+10, self.py+(795.425-480)/480*self.ph)
                    pointAimuDown1 =  QPoint(self.px+481.027/640*self.pw, self.py+(795.425-480)/480*self.ph+15)
                    pointAimuDown2 =  QPoint(self.px+481.027/640*self.pw, self.py+(795.425-480)/480*self.ph+15+10)

                    qp.drawLine(pointAimuUp1, pointAimuUp2)
                    qp.drawLine(pointAimuLeft1, pointAimuLeft2)
                    qp.drawLine(pointAimuRight1, pointAimuRight2)
                    qp.drawLine(pointAimuDown1, pointAimuDown2)  

                elif self.id == 4:
                    qp.drawEllipse(self.px+(886.681-640)/640*self.pw-15, self.py+(807.768-480)/480*self.ph-15, 30, 30) # 左下

                    pointAimuUp12 =  QPoint(self.px+(886.681-640)/640*self.pw, self.py+(807.768-480)/480*self.ph-15)
                    pointAimuUp22 =  QPoint(self.px+(886.681-640)/640*self.pw, self.py+(807.768-480)/480*self.ph-15-10)
                    pointAimuLeft12 =  QPoint(self.px+(886.681-640)/640*self.pw-15, self.py+(807.768-480)/480*self.ph)
                    pointAimuLeft22 =  QPoint(self.px+(886.681-640)/640*self.pw-15-10, self.py+(807.768-480)/480*self.ph)
                    pointAimuRight12 =  QPoint(self.px+(886.681-640)/640*self.pw+15, self.py+(807.768-480)/480*self.ph)
                    pointAimuRight22 =  QPoint(self.px+(886.681-640)/640*self.pw+15+10, self.py+(807.768-480)/480*self.ph)
                    pointAimuDown12 =  QPoint(self.px+(886.681-640)/640*self.pw, self.py+(807.768-480)/480*self.ph+15)
                    pointAimuDown22 =  QPoint(self.px+(886.681-640)/640*self.pw, self.py+(807.768-480)/480*self.ph+15+10)

                    qp.drawLine(pointAimuUp12, pointAimuUp22)
                    qp.drawLine(pointAimuLeft12, pointAimuLeft22)
                    qp.drawLine(pointAimuRight12, pointAimuRight22)
                    qp.drawLine(pointAimuDown12, pointAimuDown22)  
                elif self.id == 1:
                    qp.drawEllipse(self.px+457.730/640*self.pw-15, self.py+325.027/480*self.ph-15, 30, 30) # 左上
                    pointAimuUp13 =  QPoint(self.px+457.730/640*self.pw, self.py+325.027/480*self.ph-15)
                    pointAimuUp23 =  QPoint(self.px+457.730/640*self.pw, self.py+325.027/480*self.ph-15-10)
                    pointAimuLeft13 =  QPoint(self.px+457.730/640*self.pw-15, self.py+325.027/480*self.ph)
                    pointAimuLeft23 =  QPoint(self.px+457.730/640*self.pw-15-10, self.py+325.027/480*self.ph)
                    pointAimuRight13 =  QPoint(self.px+457.730/640*self.pw+15, self.py+325.027/480*self.ph)
                    pointAimuRight23 =  QPoint(self.px+457.730/640*self.pw+15+10, self.py+325.027/480*self.ph)
                    pointAimuDown13 =  QPoint(self.px+457.730/640*self.pw, self.py+325.027/480*self.ph+15)
                    pointAimuDown23 =  QPoint(self.px+457.730/640*self.pw, self.py+325.027/480*self.ph+15+10)
                    qp.drawLine(pointAimuUp13, pointAimuUp23)
                    qp.drawLine(pointAimuLeft13, pointAimuLeft23)
                    qp.drawLine(pointAimuRight13, pointAimuRight23)
                    qp.drawLine(pointAimuDown13, pointAimuDown23)    
                elif self.id == 2:
                    qp.drawEllipse(self.px+(879.829-640)/640*self.pw-15, self.py+335.198/480*self.ph-15, 30, 30) # 右上
                    pointAimuUp14 =  QPoint(self.px+(879.829-640)/640*self.pw, self.py+335.198/480*self.ph-15)
                    pointAimuUp24 =  QPoint(self.px+(879.829-640)/640*self.pw, self.py+335.198/480*self.ph-15-10)
                    pointAimuLeft14 =  QPoint(self.px+(879.829-640)/640*self.pw-15, self.py+335.198/480*self.ph)
                    pointAimuLeft24 =  QPoint(self.px+(879.829-640)/640*self.pw-15-10, self.py+335.198/480*self.ph)
                    pointAimuRight14 =  QPoint(self.px+(879.829-640)/640*self.pw+15, self.py+335.198/480*self.ph)
                    pointAimuRight24 =  QPoint(self.px+(879.829-640)/640*self.pw+15+10, self.py+335.198/480*self.ph)
                    pointAimuDown14 =  QPoint(self.px+(879.829-640)/640*self.pw, self.py+335.198/480*self.ph+15)
                    pointAimuDown24 =  QPoint(self.px+(879.829-640)/640*self.pw, self.py+335.198/480*self.ph+15+10)                                                           
                    qp.drawLine(pointAimuUp14, pointAimuUp24)
                    qp.drawLine(pointAimuLeft14, pointAimuLeft24)
                    qp.drawLine(pointAimuRight14, pointAimuRight24)
                    qp.drawLine(pointAimuDown14, pointAimuDown24)        
