
import rospy
import numpy as np
import cv2
import threading
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import mmap, contextlib
import message_filters

class Recv():

    def __init__(self) :
        rospy.init_node('COLOR')
        self.count = 0
        self.bridge = CvBridge()
        with open('config/color.dat', 'w') as f:
            f.write('\x00'*480*640*12)
        # with open('depth.dat', 'w') as f:
        #     f.write('\x00'*480*640*8)
    
    def color_cb(self, data1, data2, data3, data4):
        self.bridge.cv2_to_compressed_imgmsg
        color1 = self.bridge.compressed_imgmsg_to_cv2
        color1 = self.bridge.imgmsg_to_cv2(data1, desired_encoding='bgr8')
        color2 = self.bridge.imgmsg_to_cv2(data2, desired_encoding='bgr8')
        color3 = self.bridge.imgmsg_to_cv2(data3, desired_encoding='bgr8')
        color4 = self.bridge.imgmsg_to_cv2(data4, desired_encoding='bgr8')
        # color1 =  cv2.resize(color1, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
        tmp1 = np.concatenate((color1, color2), axis=1)
        tmp2 = np.concatenate((color3, color4), axis=1)
        tmp = np.concatenate((tmp1, tmp2), axis=0)
        # tmp = cv2.resize(tmp, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
        # cv2.imshow('test', tmp)
        # cv2.waitKey(50)
        with open('config/color.dat', 'r+') as f:
            with contextlib.closing(mmap.mmap(f.fileno(), 480*640*12, access=mmap.ACCESS_WRITE)) as m:
                m.seek(0)
                m.write(tmp.tobytes())
        rospy.loginfo('frame{} complete'.format(str(self.count)))
        self.count += 1


    def color_sub(self):
        cam1 = message_filters.Subscriber('/color1', Image)
        cam2 = message_filters.Subscriber('/color2', Image)        
        cam3 = message_filters.Subscriber('/color3', Image)
        cam4 = message_filters.Subscriber('/color4', Image)
        color_data = message_filters.ApproximateTimeSynchronizer([cam1, cam2, cam3, cam4], queue_size=5, slop=0.5, allow_headerless = True)
        color_data.registerCallback(self.color_cb)
        rospy.spin()


if __name__ == "__main__":
    data_sub = Recv()
    data_sub.color_sub()

