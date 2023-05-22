
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
        rospy.init_node('DEPTH')
        self.count = 0
        self.bridge = CvBridge()
        with open('config/depth.dat', 'w') as f:
            f.write('\x00'*480*640*8)


    def depth_cb(self, data1, data2, data3, data4):
        depth1 = self.bridge.imgmsg_to_cv2(data1, desired_encoding='16UC1')
        depth2 = self.bridge.imgmsg_to_cv2(data2, desired_encoding='16UC1')
        depth3 = self.bridge.imgmsg_to_cv2(data3, desired_encoding='16UC1')
        depth4 = self.bridge.imgmsg_to_cv2(data4, desired_encoding='16UC1')
        # depth1 =  cv2.resize(depth1, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
        tmp1 = np.concatenate((depth1, depth2), axis=1)
        tmp2 = np.concatenate((depth3, depth4), axis=1)
        tmp = np.concatenate((tmp1, tmp2), axis=0)
        # tmp = cv2.resize(tmp, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
        with open('config/depth.dat', 'r+') as f:
            with contextlib.closing(mmap.mmap(f.fileno(), 480*640*8, access=mmap.ACCESS_WRITE)) as m:
                m.seek(0)
                m.write(tmp.tobytes())
        rospy.loginfo('frame{} complete'.format(str(self.count)))
        self.count += 1


    def depth_sub(self):
        cam1 = message_filters.Subscriber('/depth1', Image)
        cam2 = message_filters.Subscriber('/depth2', Image)        
        cam3 = message_filters.Subscriber('/depth3', Image)
        cam4 = message_filters.Subscriber('/depth4', Image)
        depth_data = message_filters.ApproximateTimeSynchronizer([cam1, cam2, cam3, cam4], queue_size=2, slop=1, allow_headerless = True)
        depth_data.registerCallback(self.depth_cb)
        rospy.spin()


if __name__ == "__main__":
    data_sub = Recv()
    data_sub.depth_sub()

