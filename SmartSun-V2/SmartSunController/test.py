from VisualStandardInterface import VSI
import threading
import time

v = VSI(25, 0, '192.168.255.255')

v.startThreadedJob('error')


time.sleep(5)
v.stopThreadedJob()
time.sleep(5)

v.startThreadedJob('standard')
print("starting new one...")
