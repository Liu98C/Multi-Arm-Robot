#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import numpy as np
import rospy
from robot_msgs.msg import hardware, robotcore
import json
import mmap, contextlib

class State():
    def __init__(self):
        self.motorStatus = np.zeros((10, 20))
        self.gripperStatus = [0 for i in range(10)]
        self.camera = [0 for i in range(10)]
        self.motorPosition = [0 for i in range(10)]

    
    
    def hardwareMessage(self):
        rospy.Subscriber('robot_feedback', hardware, queue_size=10)
        rospy.spin()
    

    
    
    
    # processing messages from other nodes and print the states and errors
   


    def trigger_processing(self):
        rospy.Subscriber('robot_feedback', hardware, queue_size=10)
        rospy.spin()

    


    def period_callback(self, msgs):
        # 检查电机状态
        if msgs.motor_status:
            curStatus = msgs.motor_status
            for i in range(10):
                # 是否上电
                isEnabled = int(curStatus[i][13]) - int(self.motorStatus[i][13])
                if isEnabled == 1: rospy.loginfo('motor{} is enabled'.format(str(i)))
                elif isEnabled == -1: rospy.loginfo('motor{} is disabled'.format(str(i)))
                # 出现警告
                warning = int(curStatus[i][8]) - int(self.motorStatus[i][8])
                if warning == 1: rospy.loginfo('motor{} warning'.format(str(i)))
                # 是否回零
                origin_back = int(curStatus[i][0]) - int(self.motorStatus[i][0])
                if origin_back == -1: rospy.loginfo('motor{} is in origin, can move'.format(str(i)))
            self.motorStatus = curStatus
        # 检查电机故障
        # if msgs.actual_position:



    # def cameraCheck():
    


    # def 

class Command():

    def __init__(self):
        self.message = np.zeros(15) 
        self.control_publisher = rospy.Publisher('robot_control', hardware, queue_size=5)
        self.core_publisher = rospy.Publisher('robot_command', robotcore, queue_size=5)
        self.hardware = hardware()


        while not rospy.is_shutdown():
            rospy.sleep(0.1)
            newMessage = self.getMessage()
            print(newMessage)
            # judge = newMessage - self.message
            # print(judge)
            if np.all(newMessage[0:10]):
                self.hardware.motor_control = newMessage[0:10].tolist()
            
            self.control_publisher.publish(self.hardware)
            self.message = newMessage
            

        

        
    def getMessage(self):
        with open('config/order.dat', 'r') as f:
            with contextlib.closing(mmap.mmap(f.fileno(), 15, access=mmap.ACCESS_READ)) as m:
                s = m.read(15)
                msg = np.frombuffer(s, dtype=np.uint8)
                return msg


    
    











