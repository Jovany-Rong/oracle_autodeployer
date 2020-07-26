#!/usr/local/bin python
#coding: utf-8

import sshx
import paramiko
import os
import platform
import oracle_ad as ad

def ping(address):
    ping1 = u"ping %s -n 1" % address
    ping2 = u"ping %s -c 1" % address

    print(platform.system())

    if "Windows" in platform.system():
        result = os.system(ping1)
    else:
        result = os.system(ping2)

    if result == 0:
        return True
    else:
        return False

def showFiles(filePath):
    ct = 0

    fileS = []
    paths = []

    for root, dirs, files in os.walk(filePath):
        root = root.replace("\\", "/")
        if not root.endswith("/"):
            root = root + "/"
       
        for file in files:
            ct += 1
            fileS.append(file)
            paths.append(root + file)
    
    return {"files": fileS, "paths": paths}

oracle_dict = {"host": "192.168.2.171", "port": 22, "username": "oracle", "password": "oracle"}

s = sshx.SSHConnection(oracle_dict)

s.connect()

s.exec_echo("ping 192.168.2.178")

