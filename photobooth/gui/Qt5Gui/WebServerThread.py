import subprocess
import time
from pathlib import Path



def start_web(p_number, hash_num, pic_web_width, pic_web_height):
    mypath = Path().absolute()
    path_webserver = str(mypath) + "/webserver/application.py"
    test = subprocess.Popen(["python",path_webserver, p_number , pic_web_width, pic_web_height, hash_num])
    time.sleep(300)
    test.kill()

