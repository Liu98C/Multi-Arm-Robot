import rospy
import numpy as np
import cv2
import threading
from sensor_msgs.msg import Image
import mmap, contextlib
import message_filters
from result_msgs.msg import bboxes


class Recv():

    def __init__(self) :
        rospy.init_node('RES')
        self.count = 0
        with open('config/res.dat', 'w') as f:
            f.write('\x00'*16*100)
        # with open('depth.dat', 'w') as f:
        #     f.write('\x00'*480*640*8)

    
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
                m.write(np.asarray(tmp1).astype(np.uint16).tobytes())
                m.seek(400)
                m.write(np.asarray(tmp2).astype(np.uint16).tobytes())  
                m.seek(800)
                m.write(np.asarray(tmp3).astype(np.uint16).tobytes())
                m.seek(1200)
                m.write(np.asarray(tmp4).astype(np.uint16).tobytes())  
        rospy.loginfo('frame{} complete'.format(str(self.count)))
        self.count += 1

    def res_sub(self):
        res1 = message_filters.Subscriber('/result1', bboxes)
        res2 = message_filters.Subscriber('/result2', bboxes)        
        res3 = message_filters.Subscriber('/result3', bboxes)
        res4 = message_filters.Subscriber('/result4', bboxes)
        color_data = message_filters.ApproximateTimeSynchronizer([res1, res2, res3, res4], queue_size=5, slop=0.5, allow_headerless = True)
        color_data.registerCallback(self.res_cb)
        rospy.spin()


if __name__ == "__main__":
    data_sub = Recv()
    data_sub.res_sub()