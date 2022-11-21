import os, glob
dataset_path='/Users/fabianeckert/git/photobooth/webserver'
files = glob.glob(dataset_path+'/static/people_photo/*.jpg')


files.sort(key=os.path.getmtime)
names = [os.path.basename(x) for x in files]

print(names)

