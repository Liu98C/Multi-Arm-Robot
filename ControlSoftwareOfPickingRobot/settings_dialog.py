# -*- coding: utf-8 -*-

"""
Author: Cheng Liu
Email: liucheng3666@163.com
Date: 2022/11/10
"""
from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (QDialog, QGridLayout, QCheckBox, QLabel, QLineEdit, QPushButton, QGroupBox, QComboBox,
                               QListView, QDoubleSpinBox, QVBoxLayout, QHBoxLayout, QFileDialog)

import gb

#设置setting按钮的内容
class SettingsDialog(QDialog):
    def __init__(self):
        super(SettingsDialog, self).__init__()
        self.setWindowTitle('Settings')#setting框的标题
        self.setWindowIcon(QIcon('img/yologo.png'))#setting框左上角图片
        self.setWindowFlags(Qt.WindowCloseButtonHint)#显示关闭按钮

        HEIGHT = 30

        grid = QGridLayout()#以网格的方式管理界面组件

        # 选择权重文件
        label_IP = QLabel('IP地址')#设置标签Weights
        self.line_IP = QLineEdit()
        self.line_IP.setFixedHeight(HEIGHT)
        self.line_IP.setPlaceholderText('172.16.0.10')#当鼠标停留在标签不点击时显示的内容

        grid.addWidget(label_IP, 2, 0)#往网格的不同坐标添加Weights组件
        grid.addWidget(self.line_IP, 2, 1, 1, 2)#往网格的不同坐标添加line组件

        # 是否使用GPU
        label_region = QLabel('采摘区域分配')#设置标签CUDA device
        self.line_region1 = QLineEdit()
        self.line_region2 = QLineEdit()
        self.line_region3 = QLineEdit()
        self.line_region4 = QLineEdit()
        
        self.line_region1.setToolTip('(x1,y1)')#当鼠标停留在标签不点击时显示的内容
        self.line_region1.setPlaceholderText('(x1,y1)')#设置line_device中的提示文字
        self.line_region1.setFixedHeight(HEIGHT)#高
        self.line_region2.setToolTip('(x2,y2)')#当鼠标停留在标签不点击时显示的内容
        self.line_region2.setPlaceholderText('(x2,y2)')#设置line_device中的提示文字
        self.line_region2.setFixedHeight(HEIGHT)#高
        self.line_region3.setToolTip('(x3,y3)')#当鼠标停留在标签不点击时显示的内容
        self.line_region3.setPlaceholderText('(x3,y3)')#设置line_device中的提示文字
        self.line_region3.setFixedHeight(HEIGHT)#高
        self.line_region4.setToolTip('(x4,y4)')#当鼠标停留在标签不点击时显示的内容
        self.line_region4.setPlaceholderText('(x4,y4)')#设置line_device中的提示文字
        self.line_region4.setFixedHeight(HEIGHT)#高
        grid.addWidget(label_region, 3, 0)
        grid.addWidget(self.line_region1, 3, 1, 1, 1)
        grid.addWidget(self.line_region2, 3, 2, 1, 1)
        grid.addWidget(self.line_region3, 4, 1, 1, 1)
        grid.addWidget(self.line_region4, 4, 2, 1, 1)

        label_speed = QLabel('机械臂初始速度')
        self.line_speed = QLineEdit()
        self.line_speed.setFixedHeight(HEIGHT)
        self.line_speed.setPlaceholderText('5')#当鼠标停留在标签不点击时显示的内容
        grid.addWidget(label_speed, 5, 0)#往网格的不同坐标添加Weights组件
        grid.addWidget(self.line_speed, 5, 1, 1, 2)#往网格的不同坐标添加line组件


        box = QGroupBox()#设置一个容器
        box.setLayout(grid)#把网格放入容器中

        hbox = QHBoxLayout()#初始化水平布局
        self.btn_cancel = QPushButton('取消')#设置一个取消按钮
        self.btn_cancel.clicked.connect(self.restore)#当点击取消键，恢复原配置
        self.btn_ok = QPushButton('完成')#设置一个ok按钮
        self.btn_ok.clicked.connect(self.save_settings)#当点击ok键，更新配置
        hbox.addStretch()#添加一个可伸缩空间
        hbox.addWidget(self.btn_cancel)#把取消按钮增加到水平布局中
        hbox.addWidget(self.btn_ok)#把ok按钮增加到水平布局中

        vbox = QVBoxLayout()#初始化垂直布局
        vbox.addWidget(box)#把容器放入垂直布局中
        vbox.addLayout(hbox)#用于在垂直布局中插入水平布局

        self.setLayout(vbox)

        self.load_settings()


    def load_settings(self):#初始化所有配置
        self.line_IP.setText(gb.get_config('weights', ''))
        self.line_region1.setText(gb.get_config('zoneCoordinate1', ''))
        self.line_region2.setText(gb.get_config('zoneCoordinate2', ''))
        self.line_region3.setText(gb.get_config('zoneCoordinate3', ''))
        self.line_region4.setText(gb.get_config('zoneCoordinate4', ''))
        self.line_speed.setText(gb.get_config('speed', ''))


    def save_settings(self):#不同的组件有不同的更新方式，有需要查即可
        """更新配置"""
        config = {
            'weights': self.line_IP.text(),
            'zoneCoordinate1': self.line_region1.text(),
            'zoneCoordinate2': self.line_region2.text(),
            'zoneCoordinate3': self.line_region3.text(),
            'zoneCoordinate4': self.line_region4.text(),
            'speed': self.line_speed.text()
        }
        gb.record_config(config)#将设置参数写入到本地文件保存，传入字典
        self.accept()#暂时不明白

    def restore(self):
        """恢复原配置"""
        self.load_settings()#加载默认配置？
        self.reject()

    def closeEvent(self, event):#关闭事件就恢复原配置
        self.restore()
