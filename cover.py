#! /usr/bin/python3
import subprocess, os
process = subprocess.Popen("./coverart.sh", shell=True, stdout=subprocess.PIPE).stdout.read()
#print "Content-type: image/png\n"
fileName, fileExtension = os.path.splitext(process)
print("Content-Type: image/" + fileExtension[1:].lower() + "\n")
with open(process, 'rb') as f:
	print(f.read())