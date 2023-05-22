
import rospy
import mmap, contextlib
import numpy as np
from result_msgs.msg import bboxes, bbox
import struct

class ROS_topic():
    def __init__(self):
        rospy.init_node('client')
        self.pub = rospy.Publisher('result', bboxes, queue_size=3)

    def data_send(self):
        bb = bboxes()
        with open('config/res.dat', 'r') as f:
            with contextlib.closing(mmap.mmap(f.fileno(), 1000, access=mmap.ACCESS_READ)) as m:
                s = m.read(1000)
                l = struct.unpack("L", s[0:8])[0]
                res = np.frombuffer(s[8: 8+l], dtype=np.uint16).reshape((-1, 8))
                for i in range(res.shape[0]):
                    b = bbox()
                    b.xx = res[i,4]
                    b.yy = res[i,5]
                    b.mask_d = res[i,6]
                    b.bbox_d = res[i,7]
                    bb.bboxes.append(b)
        self.pub.publish(bb)

if __name__ == '__main__':
    p = ROS_topic()
    while True:
        rospy.sleep(0.1)
        p.data_send()