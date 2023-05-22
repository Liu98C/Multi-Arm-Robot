
import rospy
import numpy as np
import cv2
import _thread
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import mmap, contextlib
import message_filters
from robot_msgs.msg import bboxes, bbox, robotcore
from sensor_msgs.msg import Joy

class Recv():

    def __init__(self) :
        rospy.init_node('NUC')
        self.count = 0
        self.bridge = CvBridge()
        self.pub = rospy.Publisher('resPick', robotcore, queue_size=5)
        self.buttons = np.zeros(12, dtype=np.uint8)
        with open('config/joy.dat', 'w') as f:
            f.write('\x00'*36)
        with open('config/pick.dat', 'w') as f:
            f.write('\x00'*300)
        with open('config/color.dat', 'w') as f:
            f.write('\x00'*480*640*12)
        with open('config/depth.dat', 'w') as f:
            f.write('\x00'*480*640*8)
        with open('config/res.dat', 'w') as f:
            f.write('\x00'*16*100)
        _thread.start_new_thread(self.color_sub, ())
        _thread.start_new_thread(self.depth_sub, ())
        _thread.start_new_thread(self.res_sub, ())
        _thread.start_new_thread(self.joy_sub, ())
        _thread.start_new_thread(self.pick_pub, ())
        while not rospy.is_shutdown():
            rospy.sleep(0.25)
        # _thread.start_new_thread()


    def color_cb(self, data1, data2, data3, data4):
        # print('heres')
        color1 = self.bridge.compressed_imgmsg_to_cv2
        color1 = self.bridge.imgmsg_to_cv2(data1, desired_encoding='bgr8')
        color2 = self.bridge.imgmsg_to_cv2(data2, desired_encoding='bgr8')
        color3 = self.bridge.imgmsg_to_cv2(data3, desired_encoding='bgr8')
        color4 = self.bridge.imgmsg_to_cv2(data4, desired_encoding='bgr8')
        tmp1 = np.concatenate((color3, color2), axis=1)
        tmp2 = np.concatenate((color1, color4), axis=1)
        tmp = np.concatenate((tmp1, tmp2), axis=0)
        with open('config/color.dat', 'r+') as f:
            with contextlib.closing(mmap.mmap(f.fileno(), 480*640*12, access=mmap.ACCESS_WRITE)) as m:
                m.seek(0)
                m.write(tmp.tobytes())

    def color_sub(self):
        cam1 = message_filters.Subscriber('/color1', Image)
        cam2 = message_filters.Subscriber('/color2', Image)        
        cam3 = message_filters.Subscriber('/color3', Image)
        cam4 = message_filters.Subscriber('/color4', Image)
        color_data = message_filters.ApproximateTimeSynchronizer([cam1, cam2, cam3, cam4], queue_size=1, slop=1, allow_headerless = True)
        color_data.registerCallback(self.color_cb)
        rospy.spin()

    def depth_cb(self, data1, data2, data3, data4):
        depth1 = self.bridge.imgmsg_to_cv2(data1, desired_encoding='16UC1')
        depth2 = self.bridge.imgmsg_to_cv2(data2, desired_encoding='16UC1')
        depth3 = self.bridge.imgmsg_to_cv2(data3, desired_encoding='16UC1')
        depth4 = self.bridge.imgmsg_to_cv2(data4, desired_encoding='16UC1')
        tmp1 = np.concatenate((depth3, depth2), axis=1)
        tmp2 = np.concatenate((depth1, depth4), axis=1)
        tmp = np.concatenate((tmp1, tmp2), axis=0)
        with open('config/depth.dat', 'r+') as f:
            with contextlib.closing(mmap.mmap(f.fileno(), 480*640*8, access=mmap.ACCESS_WRITE)) as m:
                m.seek(0)
                m.write(tmp.tobytes())

    def depth_sub(self):
        cam1 = message_filters.Subscriber('/depth1', Image)
        cam2 = message_filters.Subscriber('/depth2', Image)        
        cam3 = message_filters.Subscriber('/depth3', Image)
        cam4 = message_filters.Subscriber('/depth4', Image)
        depth_data = message_filters.ApproximateTimeSynchronizer([cam1, cam2, cam3, cam4], queue_size=1, slop=1, allow_headerless = True)
        depth_data.registerCallback(self.depth_cb)
        rospy.spin()

    def res_sub(self):
        res1 = message_filters.Subscriber('/result1', bboxes)
        res2 = message_filters.Subscriber('/result2', bboxes)        
        res3 = message_filters.Subscriber('/result3', bboxes)
        res4 = message_filters.Subscriber('/result4', bboxes)
        color_data = message_filters.ApproximateTimeSynchronizer([res1, res2, res3, res4], queue_size=5, slop=0.5, allow_headerless = True)
        color_data.registerCallback(self.res_cb)
        rospy.spin()

    def res_cb(self, data1, data2, data3, data4):
        res1 = data1.bboxes
        res2 = data2.bboxes
        res3 = data3.bboxes
        res4 = data4.bboxes
        with open('config/res.dat', 'r+') as f:
            with contextlib.closing(mmap.mmap(f.fileno(), 16*100, access=mmap.ACCESS_WRITE)) as m:
                m.seek(0)
                m.write(np.zeros(1600).astype(np.uint8).tobytes())
                tmp1, tmp2, tmp3, tmp4 = [],[],[],[]
                for bbox in res1:
                    tmp1.append(bbox.xx)
                    tmp1.append(bbox.yy)
                for bbox in res2:
                    tmp2.append(bbox.xx)
                    tmp2.append(bbox.yy)
                for bbox in res3:
                    tmp3.append(bbox.xx)
                    tmp3.append(bbox.yy)   
                for bbox in res4:
                    tmp4.append(bbox.xx)
                    tmp4.append(bbox.yy) 
                m.seek(0)
                m.write(np.asarray(tmp3).astype(np.uint16).tobytes())
                m.seek(400)
                m.write(np.asarray(tmp2).astype(np.uint16).tobytes())  
                m.seek(800)
                m.write(np.asarray(tmp1).astype(np.uint16).tobytes())
                m.seek(1200)
                m.write(np.asarray(tmp4).astype(np.uint16).tobytes())


    def pick_pub(self):
        while not rospy.is_shutdown():
            rospy.sleep(0.1)
            with open('config/pick.dat', 'r') as f:
                with contextlib.closing(mmap.mmap(f.fileno(), 300, access=mmap.ACCESS_READ)) as m:
                    s = m.read(300)
                    v = np.frombuffer(s, dtype=np.uint16).reshape((-1, 3))
                    if np.sum(v) != 0:
                        rospy.loginfo('find pickList !')
                        idx = np.where(np.sum(v, axis=1)==0)[0]
                        v = np.delete(v, idx, axis=0)
                        target = robotcore()
                        target.UL_targets = v.flatten().tolist()
                        
                        # bb = bboxes()
                        # for i in range(v.shape[0]):
                        #     b = bbox()
                        #     b.xx = v[i, 0]
                        #     b.yy = v[i, 1]
                        #     b.mask_d= v[i, 2]
                        #     b.bbox_d = v[i, 2]
                        #     bb.bboxes.append(b)
                        target.mode = 'SUP'
                        self.pub.publish(target)
                        print(target)
                        print('send')
                        with open('config/pick.dat', 'r+') as f:
                            f.write('\x00'*300)

    def joy_sub(self):
        rospy.Subscriber('joy', Joy, callback=self.joy_cb, queue_size=3)
        rospy.spin()

    def joy_cb(self, msgs):
        axes = np.asarray(msgs.axes).astype(np.float32)
        # buttons = np.asarray(msgs.buttons).astype(np.uint8)
        if msgs.buttons[2] == 1:
            self.buttons = np.zeros(12, dtype=np.uint8)
            self.buttons[2] = 1
        if msgs.buttons[3] == 1:
            self.buttons = np.zeros(12, dtype=np.uint8)
            self.buttons[3] = 1
        if msgs.buttons[4] == 1:
            self.buttons = np.zeros(12, dtype=np.uint8)
            self.buttons[4] = 1
        if msgs.buttons[5] == 1:
            self.buttons = np.zeros(12, dtype=np.uint8)
            self.buttons[5] = 1
        with open('config/joy.dat', 'r+') as f:
            with contextlib.closing(mmap.mmap(f.fileno(), 36, access=mmap.ACCESS_WRITE)) as m:
                m.seek(0)
                m.write(axes.tobytes() + self.buttons.tobytes())


if __name__ == "__main__":
    Recv()


