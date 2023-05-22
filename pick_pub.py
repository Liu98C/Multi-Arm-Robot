from xml.etree.ElementTree import PI
import rospy
import numpy as np
import cv2
import threading
from sensor_msgs.msg import Image
import mmap, contextlib
import message_filters
from result_msgs.msg import bboxes, bbox


class Pick():
    def __init__(self):
        rospy.init_node('object_pick')
        self.pub = rospy.Publisher('resPick', bboxes, queue_size=5)
        with open('config/pick.dat', 'w') as f:
            f.write('\x00'*300)
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
                        bb = bboxes()
                        print(v.shape)
                        for i in range(v.shape[0]):
                            b = bbox()
                            b.xx = v[i, 0]
                            b.yy = v[i, 1]
                            b.mask_d= v[i, 2]
                            b.bbox_d = 0
                            bb.bboxes.append(b)
                        self.pub.publish(bb)
                        with open('config/pick.dat', 'r+') as f:
                            with contextlib.closing(mmap.mmap(f.fileno(), 300, access=mmap.ACCESS_WRITE)) as m:
                                s = np.zeros(300, dtype=np.uint8)
                                m.seek(0)
                                m.write(s)

if __name__ == "__main__":
    Pick()