import threading
import time
import test
import thread




img, port_number = thread.qr_generator()
img.show()
thread4hz = threading.Thread(target=test.start_web,kwargs=dict(p_number=port_number))
thread4hz.start()
#thread.worker.start(number)
for i in range(0,100):
    print(i)
    time.sleep(2)

