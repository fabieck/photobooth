from flask import Flask, render_template, request, url_for
import os
import sys
from pathlib import Path
import os.path, time
import os, glob
import socket

print('Number of arguments:', len(sys.argv), 'arguments.')
print('Argument List:', str(sys.argv))
port = str(sys.argv[1])
print("port: ", port)
#'192.168.178.41'
global width, height
width = str(sys.argv[2])
height = str(sys.argv[3])
#hash_num = str(sys.argv[4])

PEOPLE_FOLDER = os.path.join('static', 'people_photo')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = PEOPLE_FOLDER
path = os.path.dirname(sys.argv[0])
time.sleep(2)
files = glob.glob(path + '/static/people_photo/*.jpeg')
#print("files", files)
files.sort(key=os.path.getmtime)
if (len(files)>4):
    print("remove files")
    os.remove(files[0])
picture_list = [os.path.basename(x) for x in files]
##if hash numbers are wanted just uncomment follwing line and comment @app.route('/')
#@app.route(hash_num)
@app.route('/')
@app.route('/index')
def show_index():
    print("hsow index")
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], picture_list[-1])
    return render_template("index.html", user_image = full_filename, width=width, height=height)

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    print("ip ist : ", get_ip())
    if(get_ip()[1]=="9"):
        app.run(debug=False, host='0.0.0.0', port=port)
    else:
        #app.run(debug=False, host=str(get_ip()), port=port)
        app.run(debug=False, host='10.42.0.1', port=port)


