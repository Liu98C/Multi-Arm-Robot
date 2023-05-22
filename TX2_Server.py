from http.client import OK
import time
import socket, cv2, pickle, struct
import threading
import numpy as np
# import pyshine as ps # pip install pyshine
import cv2
import rospy
import mmap, contextlib
from result_msgs.msg import bboxes, bbox

class Socket():
	def __init__(self):
		rospy.init_node('client')
		self.pub = rospy.Publisher('result', bboxes, queue_size=3)

	def open(self):
		self.server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1) 	
		host_ip = '172.16.0.10' 
		print('HOST IP:',host_ip)
		port = 7777
		self.socket_address = (host_ip,port)
		self.server_socket.bind(self.socket_address)
		self.server_socket.listen()
		self.client_socket,self.addr = self.server_socket.accept()
		print("Listening at",self.socket_address)
	
	def close(self):
		self.client_socket.close()

	def show_client(self):
		print('CLIENT {} CONNECTED!'.format(self.addr))
		if self.client_socket: # if a client socket exists
			payload_size = struct.calcsize("L")
			
			while True:
				# time.sleep(0.1)
				data = b""
				# print('OK')
				bb = bboxes()
				while len(data) < 4096:
					packet = self.client_socket.recv(1024*4-len(data)) # 4K
					if not packet: break
					data+=packet
				# print(len(data))
				packed_msg_size = data[:payload_size]
				data = data[payload_size:]
				res_size = struct.unpack("L",packed_msg_size)[0]
				# msg_size = 4096 + 640*480*3
				# # msg_size = res_size
				# print(res_size)
				# while len(data) < msg_size:
				# 	# print('here')
				# 	# print("len(data)",len(data))
				# 	# print("msg_size",msg_size)
				# 	data += self.client_socket.recv(1024*4)
				res_data = data[:res_size]
				
				# with open('res.dat', 'r+') as f:
				# 	with contextlib.closing(mmap.mmap(f.fileno(), 1000, access=mmap.ACCESS_WRITE)) as m:
				# 		buf = packed_msg_size + res_data
				# 		m.seek(0)
				# 		m.write(buf)

				# frame_data = data[res_size:msg_size]
				res = np.frombuffer(res_data, dtype=np.uint16).reshape((-1, 8))
				# frame = pickle.loads(frame_data)
				# frame = np.frombuffer(frame_data, dtype=np.uint8).reshape(480, 640, 3)
				for i in range(res.shape[0]):
					b = bbox()
					b.xx = res[i,4]
					b.yy = res[i,5]
					b.mask_d = res[i,6]
					b.bbox_d = res[i,7]
					bb.bboxes.append(b)

				self.pub.publish(bb)
				# 	cv2.rectangle(frame, (x0, y0), (x1, y1), [0, 255, 255], 2)
				# 	cv2.putText(frame, str(res[i,6]), (x0, y0+5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, [0, 255, 255], thickness=1)
				# return frame
				# self.pub.publish(bb)
				# self.client_socket.close()
		
if __name__ == '__main__':
	sock = Socket()
	# with open('res.dat', 'w') as f:
	# 	f.write('\x00'*1000)
	sock.open()
	sock.show_client()
	print("TOTAL CLIENTS ",threading.activeCount() - 1)