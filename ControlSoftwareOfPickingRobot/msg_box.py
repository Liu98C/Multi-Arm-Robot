# coding=utf-8
"""
Author: Cheng Liu
Email: liucheng3666@163.com
Date: 2022/11/10
"""
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtWidgets import QMessageBox,QPushButton

class MsgSuccess(QMessageBox):#制作成功框子
    """提示（操作成功）对话框，使用的时候设置提示信息即可"""

    def __init__(self):
        super(MsgSuccess, self).__init__()
        self.setWindowTitle('注意')#标题栏
        self.setWindowIcon(QIcon('img/yologo.png'))#显示图标
        pix = QPixmap('img/success.svg').scaled(48, 48)#加载到一个控件中，通常是标签或者按钮，用于在标签或按钮上显示图像
        self.setIconPixmap(pix)
        self.setStyleSheet('font: 16px Microsoft YaHei')#设置字体格式
        btn_assert = self.addButton(self.tr("确定"), QMessageBox.YesRole)
        # self.btn_noTips = self.addButton(self.tr("不再提醒"), QMessageBox.NoRole)
        # btn_noTips.setText("不再提醒")




class MsgWarning(QMessageBox):#制作警告框子
    """注意对话框，使用的时候设置提示信息即可"""

    def __init__(self):
        super(MsgWarning, self).__init__()
        self.setWindowTitle('注意')
        self.setWindowIcon(QIcon('img/yologo.png'))
        pix = QPixmap('img/warn.svg').scaled(48, 48)
        self.setIconPixmap(pix)
        self.setStyleSheet('font: 16px Microsoft YaHei')
        btn_assert = self.addButton(self.tr("确定"), QMessageBox.YesRole)
        # self.btn_noTips = self.addButton(self.tr("拒绝"), QMessageBox.NoRole)
        
