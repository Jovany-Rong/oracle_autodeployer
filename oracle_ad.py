#!/usr/local/bin python
#coding: utf-8

import sshx
import os
import time
import platform
import shutil
import configparser as cp

linuxes = {1 : 'RedHat/CentOS 7.x 64-bit'}
oracles = {1 : 'Oracle 11.2.0.4 64-bit',
        2 : 'Oracle 12.2.0.1 64-bit'
}
host_dict = {}
#newname = ""

def getConf(sec, para):
    c = cp.ConfigParser()
    c.read("oracle_ad.conf", encoding="utf-8")
    v = None
    try:
        v = c.get(sec, para)
        v = v.replace("<num>", "#")
    except:
        pass

    return v

def getParams():
    params = {}
    params["status"] = "fail"

    if getConf("PARAMS", "hostname"):
        hostname = getConf("PARAMS", "hostname")
    else:
        hostname = input("""
【Input】请输入服务器IP地址：""")

    if getConf("PARAMS", "port"):
        port = getConf("PARAMS", "port")
    else:
        port = input("""
【Input】请输入服务器SSH端口号：""")

    if getConf("PARAMS", "username"):
        username = getConf("PARAMS", "username")
    else:
        username = input("""
【Input】请输入服务器登录用户名：""")

    if getConf("PARAMS", "password"):
        password = getConf("PARAMS", "password")
    else:
        password = input("""
【Input】请输入服务器登录密码：""")

    #if getConf("PARAMS", "newname"):
        #newname = getConf("PARAMS", "newname")
    #else:
        #newname = input("""
#【Input】请输入服务器待修改主机名：""")

    try:
        if len(hostname) > 0 and len(username) > 0:
            params["hostname"] = hostname
            params["port"] = int(port)
            params["username"] = username
            params["password"] = password
            #params["newname"] = newname

            params["status"] = "success"
    except:
        pass

    return params

def showFiles(filePath):
    ct = 0

    fileS = []
    paths = []

    for root, dirs, files in os.walk(filePath):
        del dirs
        root = root.replace("\\", "/")
        if not root.endswith("/"):
            root = root + "/"
       
        for file in files:
            ct += 1
            fileS.append(file)
            paths.append(root + file)
    
    return {"count": ct, "files": fileS, "paths": paths}

def ping(address):
    print("【Info】使用Ping检查服务器是否启动成功...")
    ping1 = u"ping %s -n 1" % address
    ping2 = u"ping %s -c 1" % address

    #print(platform.system())

    if "Windows" in platform.system():
        result = os.system(ping1)
    else:
        result = os.system(ping2)

    if result == 0:
        print("【Info】服务器已经启动成功\n")
        return True
    else:
        print("【Info】服务器尚未启动成功")
        return False

def reboot(host):
    s = sshx.SSHConnection(host)

    s.connect()

    s.execute("reboot")

    s.close()

    print("【Info】正在等待服务器重启完成...\n")
    
    time.sleep(15)

    while True:
        isOk = ping(host["host"])

        if isOk:
            break

        time.sleep(5)    

def uploadRpms(host):
    s = sshx.SSHConnection(host)

    s.connect()

    if getConf("RPM", "localPath"):
        localPath = getConf("RPM", "localPath")
    else:
        localPath = input("""
【Input】请输入本地RPM依赖包目录：【默认为当前目录.】""")
        print("\n")

    localPath = localPath.replace('\\', '/')
    
    if not localPath.endswith("/"):
        localPath = localPath + "/"
    
    if localPath == "/":
        localPath = "./"

    files = showFiles(localPath)

    print("【Info】正在上传该目录共%s个文件...\n" % files["count"])

    s.execute("rm -rf /media/lxyum")
    s.execute("mkdir /media/lxyum")
    s.execute("chown -R 777 /media/lxyum")

    for i in range(files["count"]):
        print("\t开始上传第%s个文件：%s" % (i + 1, files["files"][i]))
        s.upload(files["paths"][i], "/media/lxyum/" + files["files"][i])
    
    print("【Info】上传该目录共%s个文件完成\n" % files["count"])
    
    s.close()

def uploadOracle(host):
    s = sshx.SSHConnection(host)

    s.connect()

    if getConf("ORACLE", "localPath"):
        localPath = getConf("ORACLE", "localPath")
    else:
        localPath = input("""
【Input】请输入本地Oracle安装包目录：【默认为当前目录.】""")
        print("\n")

    localPath = localPath.replace('\\', '/')

    if not localPath.endswith("/"):
        localPath = localPath + "/"
    
    if localPath == "/":
        localPath = "./"

    files = showFiles(localPath)

    print("【Info】正在上传该目录共%s个文件...\n" % files["count"])

    s.execute("rm -rf /home/SoftwareOracle")
    s.execute("mkdir /home/SoftwareOracle")
    s.execute("chown -R 777 /home/SoftwareOracle")

    for i in range(files["count"]):
        print("\t开始上传第%s个文件：%s" % (i + 1, files["files"][i]))
        s.upload(files["paths"][i], "/home/SoftwareOracle/" + files["files"][i])
    
    print("【Info】上传该目录共%s个文件完成\n" % files["count"])
    
    s.close()

def installRpms(host, files):
    s = sshx.SSHConnection(host)

    s.connect()

    if not os.path.isdir("temp"):
        os.makedirs("temp")

    print("【Info】正在备份服务器repo文件...\n")

    s.execute("cd /etc/yum.repos.d;cp -f CentOS-Base.repo CentOS-Base.repo-bak")
    s.execute("cd /etc/yum.repos.d;cp -f CentOS-Debuginfo.repo CentOS-Debuginfo.repo-bak")
    s.execute("cd /etc/yum.repos.d;cp -f CentOS-Media.repo CentOS-Media.repo-bak")
    s.execute("cd /etc/yum.repos.d;cp -f CentOS-Vault.repo CentOS-Vault.repo-bak")
    s.execute("cd /etc/yum.repos.d;cp -f CentOS-CR.repo CentOS-CR.repo-bak")
    s.execute("cd /etc/yum.repos.d;cp -f CentOS-fasttrack.repo CentOS-fasttrack.repo-bak")
    s.execute("cd /etc/yum.repos.d;cp -f CentOS-Sources.repo CentOS-Sources.repo-bak")

    print("【Info】服务器repo文件备份完成\n")
    print("【Info】正在删除服务器多余repo文件...\n")
    
    s.execute("cd /etc/yum.repos.d;rm -f CentOS-Base.repo")
    s.execute("cd /etc/yum.repos.d;rm -f CentOS-Debuginfo.repo")
    s.execute("cd /etc/yum.repos.d;rm -f CentOS-Vault.repo")
    s.execute("cd /etc/yum.repos.d;rm -f CentOS-CR.repo")
    s.execute("cd /etc/yum.repos.d;rm -f CentOS-fasttrack.repo")
    s.execute("cd /etc/yum.repos.d;rm -f CentOS-Sources.repo")

    print("【Info】服务器多余repo文件删除完成\n")
    print("【Info】正在修改/etc/yum.repos.d/CentOS-Media.repo配置文件...\n")
    
    s.download(r"/etc/yum.repos.d/CentOS-Media.repo", r"temp/CentOS-Media.repo")

    with open("temp/CentOS-Media.repo", "r+", newline="\n", encoding="utf-8") as f:
        fText = f.read()

    rows = fText.split("\n")
        
    newRows = []

    isAdd1 = True
    isAdd2 = True

    for row in rows:
        if ("enabled=" in row) and ("#" not in row.split("enabled=")[0]) and (len(row.split("enabled=")[0].strip()) == 0):
            row = "enabled=1"
            isAdd1 = False

        if ("baseurl=" in row) and ("#" not in row.split("baseurl=")[0]) and (len(row.split("baseurl=")[0].strip()) == 0):
            row = "baseurl=file:///media/lxyum"
            isAdd2 = False

        newRows.append(row)

    aText = ""

    for row in newRows:
        aText = aText + row + "\n"

    if isAdd1:
        aText = aText + "enabled=1" + "\n"
    if isAdd2:
        aText = aText + "baseurl=file:///media/lxyum" + "\n"

    aText = aText.strip()

    aText = aText.replace("\r\n", "\n")

    with open("temp/CentOS-Media.repo", "w+", newline="\n", encoding="utf-8") as f:
        f.write(aText)

    print("【Info】/etc/yum.repos.d/CentOS-Media.repo配置文件修改完成\n")
    print("【Info】正在更新服务器/etc/yum.repos.d/CentOS-Media.repo配置文件...\n")
        
    ex = s.execute("rm -rf /etc/yum.repos.d/CentOS-Media.repo")

    s.upload("temp/CentOS-Media.repo", "/etc/yum.repos.d/CentOS-Media.repo")

    print("【Info】/etc/yum.repos.d/CentOS-Media.repo服务器配置文件更新完成\n")

    os.remove("temp/CentOS-Media.repo")

    print("【Info】正在清理yum缓存...\n")
    s.execute("yum makecache")

    print("【Info】yum缓存清理完成\n")

    print("【Info】正在修改/etc/yum.conf配置文件...\n")
    
    s.download("/etc/yum.conf", "temp/yum.conf")

    with open("temp/yum.conf", "r+", newline="\n", encoding="utf-8") as f:
        fText = f.read()

    rows = fText.split("\n")
        
    newRows = []

    isAdd1 = True
    isAdd2 = True
    isAdd3 = True
    isAdd4 = True
    isAdd5 = True

    for row in rows:
        if ("cachedir=" in row) and ("#" not in row.split("cachedir=")[0]) and (len(row.split("cachedir=")[0].strip()) == 0):
            row = "cachedir=/media/lxyum"
            isAdd1 = False

        if ("keepcache=" in row) and ("#" not in row.split("keepcache=")[0]) and (len(row.split("keepcache=")[0].strip()) == 0):
            row = "keepcache=1"
            isAdd2 = False

        if ("logfile=" in row) and ("#" not in row.split("logfile=")[0]) and (len(row.split("logfile=")[0].strip()) == 0):
            row = "logfile=/media/log/yum.log"
            isAdd3 = False
        
        if ("installonly_limit=" in row) and ("#" not in row.split("installonly_limit=")[0]) and (len(row.split("installonly_limit=")[0].strip()) == 0):
            row = "installonly_limit=500"
            isAdd4 = False

        if ("reposdir=" in row) and ("#" not in row.split("reposdir=")[0]) and (len(row.split("reposdir=")[0].strip()) == 0):
            row = "reposdir=/etc/yum.repos.d"
            isAdd5 = False

        newRows.append(row)

    aText = ""

    for row in newRows:
        aText = aText + row + "\n"

    if isAdd1:
        aText = aText + "cachedir=/media/lxyum" + "\n"
    if isAdd2:
        aText = aText + "keepcache=1" + "\n"
    if isAdd3:
        aText = aText + "logfile=/media/log/yum.log" + "\n"
    if isAdd4:
        aText = aText + "installonly_limit=500" + "\n"
    if isAdd5:
        aText = aText + "reposdir=/etc/yum.repos.d" + "\n"

    aText = aText.strip()

    aText = aText.replace("\r\n", "\n")

    with open("temp/yum.conf", "w+", newline="\n", encoding="utf-8") as f:
        f.write(aText)

    print("【Info】/etc/yum.conf配置文件修改完成\n")
    print("【Info】正在备份服务器/etc/yum.conf配置文件...\n")
        
    ex = s.execute("cp -f /etc/yum.conf /etc/yum.conf.bak")

    print("【Info】/etc/yum.conf服务器配置文件备份完成\n")
    print("【Info】正在更新服务器/etc/yum.conf配置文件...\n")
        
    ex = s.execute("rm -rf /etc/yum.conf")

    s.upload("temp/yum.conf", "/etc/yum.conf")

    print("【Info】/etc/yum.conf服务器配置文件更新完成\n")

    #s.close()

    os.remove("temp/yum.conf")

    print("【Info】正在清理yum缓存...\n")
    s.execute("yum clean all")
    s.execute("yum makecache")

    print("【Info】yum缓存清理完成\n")

    print("【Info】正在安装RPM依赖包...\n")
    
    for file in files:
        if file.endswith(".rpm"):
            print("\t正在安装：%s..." % file)
            ex = s.execute("cd /media/lxyum;rpm -ivh %s --nodeps --force" % file)
            if ex["status"] == "success":
                print("\t%s安装成功" % file)
            elif ("警告" in ex["result"]) or ("warning" in ex["result"].lower()):
                print("\t%s安装成功，但出现警告：%s" % (file, ex["result"]))
            else:
                print("【Error】%s" % ex["result"])
                print("\t%s安装失败" % file)
    
    print("【Info】RPM依赖包安装完成\n")

    s.close()
    

def disableSELinux(host):
    s = sshx.SSHConnection(host)

    s.connect()

    if not os.path.isdir("temp"):
        os.makedirs("temp")

    print("【Info】正在修改SELinux配置文件...\n")
    
    s.download(r"/etc/selinux/config", r"temp/selinuxconfig")

    with open("temp/selinuxconfig", "r+", newline="\n", encoding="utf-8") as f:
        fText = f.read()

    rows = fText.split("\n")
        
    newRows = []

    isAdd1 = True
    isAdd2 = True

    for row in rows:
        if ("SELINUX=" in row) and ("#" not in row.split("SELINUX=")[0]) and (len(row.split("SELINUX=")[0].strip()) == 0):
            row = "SELINUX=disabled"
            isAdd1 = False

        if ("SELINUXTYPE=" in row) and ("#" not in row.split("SELINUXTYPE=")[0]) and (len(row.split("SELINUXTYPE=")[0].strip()) == 0):
            row = "SELINUXTYPE=targeted"
            isAdd2 = False

        newRows.append(row)

    aText = ""

    for row in newRows:
        aText = aText + row + "\n"

    if isAdd1:
        aText = aText + "SELINUX=disabled" + "\n"
    if isAdd2:
        aText = aText + "SELINUXTYPE=targeted" + "\n"

    aText = aText.strip()

    aText = aText.replace("\r\n", "\n")

    with open("temp/selinuxconfig", "w+", newline="\n", encoding="utf-8") as f:
        f.write(aText)

    print("【Info】SELinux配置文件修改完成\n")
    print("【Info】正在备份服务器SELinux配置文件...\n")
        
    ex = s.execute("cp -f /etc/selinux/config /etc/selinux/config.bak")

    print("【Info】SELinux服务器配置文件备份完成\n")
    print("【Info】正在更新服务器SELinux配置文件...\n")
        
    ex = s.execute("rm -rf /etc/selinux/config")

    s.upload("temp/selinuxconfig", "/etc/selinux/config")

    print("【Info】SELinux服务器配置文件更新完成\n")

    s.close()

    os.remove("temp/selinuxconfig")

    if getConf("SELINUX", "isReboot"):
        isReboot = getConf("SELINUX", "isReboot")
    else:
        isReboot = input("""
【Input】是否需要立即重新启动以使配置生效：【y/n，默认y】""")
        print("\n")

    if isReboot != "n" and isReboot != "N":
        reboot(host)

def optimizeKernel(host):
    paraDic = dict()

    paraDic["file-max"] = '6815744'
    paraDic["aio-max-nr"] = '1048576'
    paraDic["shmall"] = '2097152'
    paraDic["shmmax"] = '2147483648'
    paraDic["shmmni"] = '4096'
    paraDic["sem"] = '250 32000 100 128'
    paraDic["rmem_default"] = '262144'
    paraDic["rmem_max"] = '4194304'
    paraDic["wmem_default"] = '262144'
    paraDic["wmem_max"] = '1048576'

    paraDic["file-max"] = getConf("KERNEL", "file-max")
    paraDic["aio-max-nr"] = getConf("KERNEL", "aio-max-nr")
    paraDic["shmall"] = getConf("KERNEL", "shmall")
    paraDic["shmmax"] = getConf("KERNEL", "shmmax")
    paraDic["shmmni"] = getConf("KERNEL", "shmmni")
    paraDic["sem"] = getConf("KERNEL", "sem")
    paraDic["rmem_default"] = getConf("KERNEL", "rmem_default")
    paraDic["rmem_max"] = getConf("KERNEL", "rmem_max")
    paraDic["wmem_default"] = getConf("KERNEL", "wmem_default")
    paraDic["wmem_max"] = getConf("KERNEL", "wmem_max")

    s = sshx.SSHConnection(host)

    s.connect()

    if not os.path.isdir("temp"):
        os.makedirs("temp")
    
    print("【Info】正在修改sysctl.conf配置文件...\n")

    s.download(r"/etc/sysctl.conf", r"temp/sysctl.conf")

    with open("temp/sysctl.conf", "r+", newline="\n", encoding="utf-8") as f:
        fText = f.read()

    rows = fText.split("\n")
        
    newRows = []

    isAdd1 = True
    isAdd2 = True
    isAdd3 = True
    isAdd4 = True
    isAdd5 = True
    isAdd6 = True
    isAdd7 = True
    isAdd8 = True
    isAdd9 = True
    isAdd10 = True
    isAdd11 = True
    isAdd12 = True
    isAdd13 = True

    for row in rows:
        if ("net.ipv4.icmp_echo_ignore_broadcasts" in row) and ("#" not in row.split("net.ipv4.icmp_echo_ignore_broadcasts")[0]) and (len(row.split("net.ipv4.icmp_echo_ignore_broadcasts")[0].strip()) == 0):
            row = "net.ipv4.icmp_echo_ignore_broadcasts = 1"
            isAdd1 = False

        if ("net.ipv4.conf.all.rp_filter" in row) and ("#" not in row.split("net.ipv4.conf.all.rp_filter")[0]) and (len(row.split("net.ipv4.conf.all.rp_filter")[0].strip()) == 0):
            row = "net.ipv4.conf.all.rp_filter = 1"
            isAdd2 = False

        if ("fs.file-max" in row) and ("#" not in row.split("fs.file-max")[0]) and (len(row.split("fs.file-max")[0].strip()) == 0):
            row = "fs.file-max = %s" % paraDic["file-max"]
            isAdd3 = False

        if ("fs.aio-max-nr" in row) and ("#" not in row.split("fs.aio-max-nr")[0]) and (len(row.split("fs.aio-max-nr")[0].strip()) == 0):
            row = "fs.aio-max-nr = %s" % paraDic["aio-max-nr"]
            isAdd4 = False

        if ("kernel.shmall" in row) and ("#" not in row.split("kernel.shmall")[0]) and (len(row.split("kernel.shmall")[0].strip()) == 0):
            row = "kernel.shmall = %s" % paraDic["shmall"]
            isAdd5 = False

        if ("kernel.shmmax" in row) and ("#" not in row.split("kernel.shmmax")[0]) and (len(row.split("kernel.shmmax")[0].strip()) == 0):
            row = "kernel.shmmax = %s" % paraDic["shmmax"]
            isAdd6 = False

        if ("kernel.shmmni" in row) and ("#" not in row.split("kernel.shmmni")[0]) and (len(row.split("kernel.shmmni")[0].strip()) == 0):
            row = "kernel.shmmni = %s" % paraDic["shmmni"]
            isAdd7 = False

        if ("kernel.sem" in row) and ("#" not in row.split("kernel.sem")[0]) and (len(row.split("kernel.sem")[0].strip()) == 0):
            row = "kernel.sem = %s" % paraDic["sem"]
            isAdd8 = False

        if ("net.ipv4.ip_local_port_range" in row) and ("#" not in row.split("net.ipv4.ip_local_port_range")[0]) and (len(row.split("net.ipv4.ip_local_port_range")[0].strip()) == 0):
            row = "net.ipv4.ip_local_port_range = 9000 65500"
            isAdd9 = False

        if ("net.core.rmem_default" in row) and ("#" not in row.split("net.core.rmem_default")[0]) and (len(row.split("net.core.rmem_default")[0].strip()) == 0):
            row = "net.core.rmem_default = %s" % paraDic["rmem_default"]
            isAdd10 = False

        if ("net.core.rmem_max" in row) and ("#" not in row.split("net.core.rmem_max")[0]) and (len(row.split("net.core.rmem_max")[0].strip()) == 0):
            row = "net.core.rmem_max = %s" % paraDic["rmem_max"]
            isAdd11 = False

        if ("net.core.wmem_default" in row) and ("#" not in row.split("net.core.wmem_default")[0]) and (len(row.split("net.core.wmem_default")[0].strip()) == 0):
            row = "net.core.wmem_default = %s" % paraDic["wmem_default"]
            isAdd12 = False

        if ("net.core.wmem_max" in row) and ("#" not in row.split("net.core.wmem_max")[0]) and (len(row.split("net.core.wmem_max")[0].strip()) == 0):
            row = "net.core.wmem_max = %s" % paraDic["wmem_max"]
            isAdd13 = False

        newRows.append(row)

    aText = ""

    for row in newRows:
        aText = aText + row + "\n"

    
    if isAdd1:
        t = "net.ipv4.icmp_echo_ignore_broadcasts = 1"
        aText = aText + t + "\n"

    if isAdd2:
        t = "net.ipv4.conf.all.rp_filter = 1"
        aText = aText + t + "\n"

    if isAdd3:
        t = "fs.file-max = %s" % paraDic["file-max"]
        aText = aText + t + "\n"

    if isAdd4:
        t = "fs.aio-max-nr = %s" % paraDic["aio-max-nr"]
        aText = aText + t + "\n"

    if isAdd5:
        t = "kernel.shmall = %s" % paraDic["shmall"]
        aText = aText + t + "\n"

    if isAdd6:
        t = "kernel.shmmax = %s" % paraDic["shmmax"]
        aText = aText + t + "\n"

    if isAdd7:
        t = "kernel.shmmni = %s" % paraDic["shmmni"]
        aText = aText + t + "\n"

    if isAdd8:
        t = "kernel.sem = %s" % paraDic["sem"]
        aText = aText + t + "\n"

    if isAdd9:
        t = "net.ipv4.ip_local_port_range = 9000 65500"
        aText = aText + t + "\n"

    if isAdd10:
        t = "net.core.rmem_default = %s" % paraDic["rmem_default"]
        aText = aText + t + "\n"

    if isAdd11:
        t = "net.core.rmem_max = %s" % paraDic["rmem_max"]
        aText = aText + t + "\n"

    if isAdd12:
        t = "net.core.wmem_default = %s" % paraDic["wmem_default"]
        aText = aText + t + "\n"

    if isAdd13:
        t = "net.core.wmem_max = %s" % paraDic["wmem_max"]
        aText = aText + t + "\n"

    aText = aText.strip()

    aText = aText.replace("\r\n", "\n")

    with open("temp/sysctl.conf", "w+", newline="\n", encoding="utf-8") as f:
        f.write(aText)
    
    print("【Info】sysctl.conf配置文件修改完成\n")
    print("【Info】正在备份服务器sysctl.conf配置文件...\n")
        
    ex = s.execute("cp -f /etc/sysctl.conf /etc/sysctl.conf.bak")

    print("【Info】sysctl.conf服务器配置文件备份完成\n")
    print("【Info】正在更新服务器sysctl.conf配置文件...\n")
        
    ex = s.execute("rm -rf /etc/sysctl.conf")

    s.upload("temp/sysctl.conf", "/etc/sysctl.conf")

    print("【Info】sysctl.conf服务器配置文件更新完成\n")

    s.close()

    os.remove("temp/sysctl.conf")

    if getConf("KERNEL", "isReboot"):
        isReboot = getConf("KERNEL", "isReboot")
    else:
        isReboot = input("""
【Input】是否需要立即重新启动以使配置生效：【y/n，默认y】""")
        print("\n")

    if isReboot != "n" and isReboot != "N":
        reboot(host)

def disableFirewall(host):
    s = sshx.SSHConnection(host)

    s.connect()

    print("【Info】正在关闭防火墙...\n")

    ex = s.execute("systemctl stop firewalld")

    if ex["status"] == "success":
        print("【Info】防火墙关闭完成\n")
    else:
        print("【Error】防火墙关闭失败：%s\n" % ex["result"])

    print("【Info】正在禁用防火墙...\n")

    ex = s.execute("systemctl disable firewalld")

    if ex["status"] == "success":
        print("【Info】防火墙禁用完成\n")
    else:
        print("【Error】防火墙禁用失败：%s\n" % ex["result"])

def changeOSMark(host):
    s = sshx.SSHConnection(host)

    s.connect()

    if not os.path.isdir("temp"):
        os.makedirs("temp")

    print("【Info】正在修改RedHat标识文件...\n")
    
    s.download(r"/etc/redhat-release", r"temp/redhat-release")

    aText = "redhat-7"

    aText = aText.replace("\r\n", "\n")

    with open("temp/redhat-release", "w+", newline="\n", encoding="utf-8") as f:
        f.write(aText)

    print("【Info】RedHat标识文件修改完成\n")
    print("【Info】正在备份服务器RedHat标识文件...\n")
        
    ex = s.execute("cp -f /etc/redhat-release /etc/redhat-release.bak")

    print("【Info】RedHat标识文件服务器备份完成\n")
    print("【Info】正在更新服务器RedHat标识文件...\n")
        
    ex = s.execute("rm -rf /etc/redhat-release")

    s.upload("temp/redhat-release", "/etc/redhat-release")

    print("【Info】RedHat标识文件服务器更新完成\n")

    s.close()

    os.remove("temp/redhat-release")

    if getConf("OSMARK", "isReboot"):
        isReboot = getConf("OSMARK", "isReboot")
    else:
        isReboot = input("""
【Input】是否需要立即重新启动以使配置生效：【y/n，默认y】""")
        print("\n")

    if isReboot != "n" and isReboot != "N":
        reboot(host)

def addGroup(host):
    s = sshx.SSHConnection(host)

    s.connect()

    print("【Info】正在创建用户组oinstall...\n")

    ex = s.execute("groupadd oinstall")

    if ex["status"] == "success":
        print("【Info】创建用户组oinstall完成\n")
    else:
        print("【Error】创建用户组oinstall失败：%s\n" % ex["result"])

    print("【Info】正在创建用户组dba...\n")

    ex = s.execute("groupadd dba")

    if ex["status"] == "success":
        print("【Info】创建用户组dba完成\n")
    else:
        print("【Error】创建用户组dba失败：%s\n" % ex["result"])

def addUser(host, oracleVer):
    s = sshx.SSHConnection(host)

    s.connect()

    print("【Info】正在创建用户oracle...\n")
    
    ex = s.execute("useradd -g oinstall -G dba -p '$6$y/3qf./b$sJLSR5eAIDho9SGbibAfVsXZ7rMs6A0cColL1yX9asUSLpDKXRopLfFXs6s.AsLPNRFuEIqRSjhjc6KuJd5xs1' -m oracle")

    if ex["status"] == "success":
        print("【Info】创建用户oracle完成（oracle/oracle）\n")
    else:
        print("【Error】创建用户oracle失败：%s\n" % ex["result"])

    print("【Info】正在修改/etc/security/limits.conf配置文件...\n")

    s.download(r"/etc/security/limits.conf", r"temp/limits.conf")

    with open("temp/limits.conf", "r+", newline="\n", encoding="utf-8") as f:
        fText = f.read()

    rows = fText.split("\n")
    
    newRows = []

    isAdd1 = True
    isAdd2 = True
    isAdd3 = True
    isAdd4 = True

    for row in rows:
        if ("oracle soft nproc" in row) and ("#" not in row.split("oracle soft nproc")[0]) and (len(row.split("oracle soft nproc")[0].strip()) == 0):
            row = "oracle soft nproc 2047"
            isAdd1 = False

        if ("oracle hard nproc" in row) and ("#" not in row.split("oracle hard nproc")[0]) and (len(row.split("oracle hard nproc")[0].strip()) == 0):
            row = "oracle hard nproc 16384"
            isAdd2 = False

        if ("oracle soft nofile" in row) and ("#" not in row.split("oracle soft nofile")[0]) and (len(row.split("oracle soft nofile")[0].strip()) == 0):
            row = "oracle soft nofile 1024"
            isAdd3 = False

        if ("oracle hard nofile" in row) and ("#" not in row.split("oracle hard nofile")[0]) and (len(row.split("oracle hard nofile")[0].strip()) == 0):
            row = "oracle hard nofile 65536"
            isAdd4 = False

        newRows.append(row)

    aText = ""

    for row in newRows:
        aText = aText + row + "\n"

    if isAdd1:
        t = "oracle soft nproc 2047"
        aText = aText + t + "\n"

    if isAdd2:
        t = "oracle hard nproc 16384"
        aText = aText + t + "\n"

    if isAdd3:
        t = "oracle soft nofile 1024"
        aText = aText + t + "\n"

    if isAdd4:
        t = "oracle hard nofile 65536"
        aText = aText + t + "\n"

    aText = aText.strip()

    aText = aText.replace("\r\n", "\n")

    with open("temp/limits.conf", "w+", newline="\n", encoding="utf-8") as f:
        f.write(aText)
    
    print("【Info】/etc/security/limits.conf配置文件修改完成\n")
    print("【Info】正在备份服务器/etc/security/limits.conf配置文件...\n")
        
    ex = s.execute("cp -f /etc/security/limits.conf /etc/security/limits.conf.bak")

    print("【Info】/etc/security/limits.conf服务器配置文件备份完成\n")
    print("【Info】正在更新服务器/etc/security/limits.conf配置文件...\n")
        
    ex = s.execute("rm -rf /etc/security/limits.conf")

    s.upload("temp/limits.conf", "/etc/security/limits.conf")

    print("【Info】/etc/security/limits.conf服务器配置文件更新完成\n")

    os.remove("temp/limits.conf")

    print("【Info】正在修改.bash_profile配置文件...\n")

    s.download(r"/home/oracle/.bash_profile", r"temp/bash_profile")

    with open("temp/bash_profile", "r+", newline="\n", encoding="utf-8") as f:
        fText = f.read()

    if oracleVer == 1:
        t = """
# Get the aliases and functions
if [ -f ~/.bashrc ]; then
. ~/.bashrc
fi

# User specific environment and startup programs

PATH=$PATH:$HOME/.local/bin:$HOME/bin

export PATH
export ORACLE_BASE=/home/data/oracle/app
export ORACLE_HOME=/home/data/oracle/app/oracle/product/11.2.0/dbhome_1
export ORACLE_SID=orcl
export ORACLE_UNQNAME=orcl
export ORACLE_TERM=xterm
export PATH=$ORACLE_HOME/bin:/usr/sbin:$PATH:PATH.PATH:/usr/bin:/usr/sbin:/bin:/sbin
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:/lib:/usr/lib
export LANG=C 
export NLS_LANG=AMERICAN_AMERICA.ZHS16GBK
    """
    elif oracleVer == 2:
        t = """
# Get the aliases and functions
if [ -f ~/.bashrc ]; then
. ~/.bashrc
fi

# User specific environment and startup programs

PATH=$PATH:$HOME/.local/bin:$HOME/bin

export PATH
export ORACLE_BASE=/home/data/oracle/app
export ORACLE_HOME=/home/data/oracle/app/oracle/product/12.2.0/dbhome_1
export ORACLE_SID=orcl
export ORACLE_UNQNAME=orcl
export ORACLE_TERM=xterm
export PATH=$ORACLE_HOME/bin:/usr/sbin:$PATH:PATH.PATH:/usr/bin:/usr/sbin:/bin:/sbin
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:/lib:/usr/lib
export LANG=C 
export NLS_LANG=AMERICAN_AMERICA.ZHS16GBK
    """

    aText = fText + "\n" + t
    
    aText = aText.strip()

    aText = aText.replace("\r\n", "\n")

    with open("temp/bash_profile", "w+", newline="\n", encoding="utf-8") as f:
        f.write(aText)
    
    print("【Info】/home/oracle/.bash_profile配置文件修改完成\n")
    print("【Info】正在备份服务器/home/oracle/.bash_profile配置文件...\n")
        
    ex = s.execute("cp -f /home/oracle/.bash_profile /home/oracle/.bash_profile.bak")

    print("【Info】/home/oracle/.bash_profile服务器配置文件备份完成\n")
    print("【Info】正在更新服务器/home/oracle/.bash_profile配置文件...\n")
        
    ex = s.execute("rm -rf /home/oracle/.bash_profile")

    s.upload("temp/bash_profile", "/home/oracle/.bash_profile")

    print("【Info】/home/oracle/.bash_profile服务器配置文件更新完成\n")

    s.close()

    os.remove("temp/bash_profile")

def createOraDirs(host):
    s = sshx.SSHConnection(host)

    s.connect()

    print("【Info】正在创建目录/home/data/oracle...\n")

    ex = s.execute("mkdir -p /home/data/oracle/rsp")

    if ex["status"] == "success":
        print("【Info】创建目录/home/data/oracle完成\n")
    else:
        print("【Error】创建目录/home/data/oracle失败：%s\n" % ex["result"])

    print("【Info】正在创建目录/home/data/oraInventory...\n")

    ex = s.execute("mkdir -p /home/data/oraInventory")

    if ex["status"] == "success":
        print("【Info】创建目录/home/data/oraInventory完成\n")
    else:
        print("【Error】创建目录/home/data/oraInventory失败：%s\n" % ex["result"])

    print("【Info】正在创建目录/home/data/database...\n")

    ex = s.execute("mkdir -p /home/data/database")

    if ex["status"] == "success":
        print("【Info】创建目录/home/data/database完成\n")
    else:
        print("【Error】创建目录/home/data/database失败：%s\n" % ex["result"])

    print("【Info】正在授权目录/home/data/oracle...\n")

    ex = s.execute("chown -R oracle:oinstall /home/data/oracle")

    if ex["status"] == "success":
        print("【Info】授权目录/home/data/oracle完成\n")
    else:
        print("【Error】授权目录/home/data/oracle失败：%s\n" % ex["result"])

    print("【Info】正在授权目录/home/data/oraInventory...\n")

    ex = s.execute("chown -R oracle:oinstall /home/data/oraInventory")

    if ex["status"] == "success":
        print("【Info】授权目录/home/data/oraInventory完成\n")
    else:
        print("【Error】授权目录/home/data/oraInventory失败：%s\n" % ex["result"])

    print("【Info】正在授权目录/home/data/database...\n")

    ex = s.execute("chown -R oracle:oinstall /home/data/database")

    if ex["status"] == "success":
        print("【Info】授权目录/home/data/database完成\n")
    else:
        print("【Error】授权目录/home/data/database失败：%s\n" % ex["result"])

    s.close()

def unzipOracle(host, oracleVer):
    if oracleVer == 1:
        unzipOracle_11204(host)
    elif oracleVer == 2:
        unzipOracle_12201(host)

def unzipOracle_11204(host):
    s = sshx.SSHConnection(host)

    s.connect()

    print("【Info】正在解压文件p13390677_112040_Linux-x86-64_1of7.zip...\n")
    
    ex = s.execute("cd /home/SoftwareOracle;unzip p13390677_112040_Linux-x86-64_1of7.zip -d /home/data/database/")

    if ex["status"] == "success":
        print("【Info】解压文件p13390677_112040_Linux-x86-64_1of7.zip完成\n")
    else:
        print("【Error】解压文件p13390677_112040_Linux-x86-64_1of7.zip失败：%s\n" % ex["result"])

    print("【Info】正在解压文件p13390677_112040_Linux-x86-64_2of7.zip...\n")
    
    ex = s.execute("cd /home/SoftwareOracle;unzip p13390677_112040_Linux-x86-64_2of7.zip -d /home/data/database/")

    if ex["status"] == "success":
        print("【Info】解压文件p13390677_112040_Linux-x86-64_2of7.zip完成\n")
    else:
        print("【Error】解压文件p13390677_112040_Linux-x86-64_2of7.zip失败：%s\n" % ex["result"])

    print("【Info】正在解压文件p13390677_112040_Linux-x86-64_3of7.zip...\n")
    
    ex = s.execute("cd /home/SoftwareOracle;unzip p13390677_112040_Linux-x86-64_3of7.zip -d /home/data/database/")

    if ex["status"] == "success":
        print("【Info】解压文件p13390677_112040_Linux-x86-64_3of7.zip完成\n")
    else:
        print("【Error】解压文件p13390677_112040_Linux-x86-64_3of7.zip失败：%s\n" % ex["result"])

    print("【Info】正在解压文件p10404530_112030_Linux-x86-64_4of7.zip...\n")
    
    ex = s.execute("cd /home/SoftwareOracle;unzip p10404530_112030_Linux-x86-64_4of7.zip -d /home/data/database/")

    if ex["status"] == "success":
        print("【Info】解压文件p10404530_112030_Linux-x86-64_4of7.zip完成\n")
    else:
        print("【Error】解压文件p10404530_112030_Linux-x86-64_4of7.zip失败：%s\n" % ex["result"])

    print("【Info】正在解压文件p10404530_112030_Linux-x86-64_5of7.zip...\n")
    
    ex = s.execute("cd /home/SoftwareOracle;unzip p10404530_112030_Linux-x86-64_5of7.zip -d /home/data/database/")

    if ex["status"] == "success":
        print("【Info】解压文件p10404530_112030_Linux-x86-64_5of7.zip完成\n")
    else:
        print("【Error】解压文件p10404530_112030_Linux-x86-64_5of7.zip失败：%s\n" % ex["result"])

    print("【Info】正在解压文件p10404530_112030_Linux-x86-64_6of7.zip...\n")
    
    ex = s.execute("cd /home/SoftwareOracle;unzip p10404530_112030_Linux-x86-64_6of7.zip -d /home/data/database/")

    if ex["status"] == "success":
        print("【Info】解压文件p10404530_112030_Linux-x86-64_6of7.zip完成\n")
    else:
        print("【Error】解压文件p10404530_112030_Linux-x86-64_6of7.zip失败：%s\n" % ex["result"])

    print("【Info】正在解压文件p10404530_112030_Linux-x86-64_7of7.zip...\n")
    
    ex = s.execute("cd /home/SoftwareOracle;unzip p10404530_112030_Linux-x86-64_7of7.zip -d /home/data/database/")

    if ex["status"] == "success":
        print("【Info】解压文件p10404530_112030_Linux-x86-64_7of7.zip完成\n")
    else:
        print("【Error】解压文件p10404530_112030_Linux-x86-64_7of7.zip失败：%s\n" % ex["result"])

    ex = s.execute("chown -R oracle:oinstall /home/data/database/database/")

    s.close()

def unzipOracle_12201(host):
    s = sshx.SSHConnection(host)

    s.connect()

    print("【Info】正在解压文件linuxx64_12201_database.zip...\n")
    
    ex = s.execute("cd /home/SoftwareOracle;unzip linuxx64_12201_database.zip -d /home/data/database/")

    if ex["status"] == "success":
        print("【Info】解压文件linuxx64_12201_database.zip完成\n")
    else:
        print("【Error】解压文件linuxx64_12201_database.zip失败：%s\n" % ex["result"])

    ex = s.execute("chown -R oracle:oinstall /home/data/database/database/")

    s.close()

def setLogin(host):
    s = sshx.SSHConnection(host)

    s.connect()

    if not os.path.isdir("temp"):
        os.makedirs("temp")

    print("【Info】正在修改/etc/pam.d/login配置文件...\n")

    s.download(r"/etc/pam.d/login", r"temp/login")

    with open("temp/login", "r+", newline="\n", encoding="utf-8") as f:
        fText = f.read()

    rows = fText.split("\n")
        
    newRows = []

    isAdd1 = True
    isAdd2 = True

    for row in rows:
        if ("session" in row and "required" in row and "/lib64/security/pam_limits.so" in row) and ("#" not in row.split("session")[0]) and (len(row.split("session")[0].strip()) == 0):
            isAdd1 = False

        if ("session" in row and "required" in row and "pam_limits.so" in row) and ("#" not in row.split("session")[0]) and (len(row.split("session")[0].strip()) == 0):
            isAdd2 = False

        newRows.append(row)

    aText = ""

    for row in newRows:
        aText = aText + row + "\n"

    
    if isAdd1:
        t = "session required /lib64/security/pam_limits.so"
        aText = aText + t + "\n"

    if isAdd2:
        t = "session required pam_limits.so"
        aText = aText + t + "\n"

    aText = aText.strip()

    aText = aText.replace("\r\n", "\n")

    with open("temp/login", "w+", newline="\n", encoding="utf-8") as f:
        f.write(aText)
    
    print("【Info】/etc/pam.d/login配置文件修改完成\n")
    print("【Info】正在备份服务器/etc/pam.d/login配置文件...\n")
        
    ex = s.execute("cp -f /etc/pam.d/login /etc/pam.d/login.bak")

    print("【Info】/etc/pam.d/login服务器配置文件备份完成\n")
    print("【Info】正在更新服务器/etc/pam.d/login配置文件...\n")
        
    ex = s.execute("rm -rf /etc/pam.d/login")

    s.upload("temp/login", "/etc/pam.d/login")

    print("【Info】/etc/pam.d/login服务器配置文件更新完成\n")

    s.close()

    os.remove("temp/login")

def setProfile(host, oracleVer):
    s = sshx.SSHConnection(host)

    s.connect()

    if not os.path.isdir("temp"):
        os.makedirs("temp")

    print("【Info】正在修改/etc/profile配置文件...\n")

    s.download(r"/etc/profile", r"temp/profile")

    with open("temp/profile", "r+", newline="\n", encoding="utf-8") as f:
        fText = f.read()
        
    isAdd = True

    if oracleVer == 1:

        tText = """export ORACLE_BASE=/home/data/oracle/app
export ORACLE_HOME=/home/data/oracle/app/oracle/product/11.2.0/dbhome_1
export ORACLE_SID=orcl
export PATH=$ORACLE_HOME/bin:/usr/sbin:$PATH:PATH.PATH:/usr/bin:/usr/sbin:/bin:/sbin
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:/lib:/usr/lib

if [ $USER = "oracle" ]; then
   if [ $SHELL = "/bin/ksh" ]; then
       ulimit -p 16384
       ulimit -n 65536
    else
       ulimit -u 16384 -n 65536
   fi
fi"""
    elif oracleVer == 2:
        tText = """export ORACLE_BASE=/home/data/oracle/app
export ORACLE_HOME=/home/data/oracle/app/oracle/product/12.2.0/dbhome_1
export ORACLE_SID=orcl
export PATH=$ORACLE_HOME/bin:/usr/sbin:$PATH:PATH.PATH:/usr/bin:/usr/sbin:/bin:/sbin
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:/lib:/usr/lib

if [ $USER = "oracle" ]; then
   if [ $SHELL = "/bin/ksh" ]; then
       ulimit -p 16384
       ulimit -n 65536
    else
       ulimit -u 16384 -n 65536
   fi
fi"""

    if tText in fText:
        isAdd = False

    aText = fText

    if isAdd == True:
        aText = aText + '\n' + tText

    aText = aText.replace("\r\n", "\n")
    
    with open("temp/profile", "w+", newline="\n", encoding="utf-8") as f:
        f.write(aText)
    
    print("【Info】/etc/profile配置文件修改完成\n")
    print("【Info】正在备份服务器/etc/profile配置文件...\n")
        
    ex = s.execute("cp -f /etc/profile /etc/profile.bak")

    print("【Info】/etc/profile服务器配置文件备份完成\n")
    print("【Info】正在更新服务器/etc/profile配置文件...\n")
        
    ex = s.execute("rm -rf /etc/profile")

    s.upload("temp/profile", "/etc/profile")

    print("【Info】/etc/profile服务器配置文件更新完成\n")

    s.close()

    os.remove("temp/profile")

def copyRsps(host, oracleVer):
    if oracleVer == 1:
        copyRsps_11204(host)
    elif oracleVer == 2:
        copyRsps_12201(host)

def copyRsps_11204(host):
    s = sshx.SSHConnection(host)

    s.connect()

    print("【Info】正在创建/etc/oraInst.loc配置文件...\n")

    s.execute("rm -rf /etc/oraInst.loc")
    s.upload("resource/11.2.0.4/oraInst.loc", "/etc/oraInst.loc")

    print("【Info】创建/etc/oraInst.loc配置文件完成\n")
    print("【Info】正在授权/etc/oraInst.loc配置文件...\n")
    
    s.execute("chmod 777 /etc")
    s.execute("chmod 777 /etc/oraInst.loc")
    s.execute("chown -R oracle:oinstall /etc/oraInst.loc")

    print("【Info】授权/etc/oraInst.loc配置文件完成\n")
    print("【Info】正在创建/home/data/oracle/rsp/db_install.rsp响应文件...\n")

    with open("resource/11.2.0.4/db_install.rsp", "r+", newline="\n", encoding="utf-8") as f:
        fText = f.read()

    aText = fText.replace("<hostname>", host["host"])

    aText = aText.replace("\r\n", "\n")

    if not os.path.isdir("temp"):
        os.makedirs("temp")

    with open("temp/db_install.rsp", "w+", newline="\n", encoding="utf-8") as f:
        f.write(aText)

    s.execute("rm -rf /home/data/oracle/rsp/db_install.rsp")
    s.upload("temp/db_install.rsp", "/home/data/oracle/rsp/db_install.rsp")

    print("【Info】创建/home/data/oracle/rsp/db_install.rsp响应文件完成\n")
    print("【Info】正在创建/home/data/oracle/rsp/dbca.rsp响应文件...\n")

    s.execute("rm -rf /home/data/oracle/rsp/dbca.rsp")
    s.upload("resource/11.2.0.4/dbca.rsp", "/home/data/oracle/rsp/dbca.rsp")

    print("【Info】创建/home/data/oracle/rsp/dbca.rsp响应文件完成\n")
    print("【Info】正在创建/home/data/oracle/rsp/netca.rsp响应文件...\n")

    s.execute("rm -rf /home/data/oracle/rsp/netca.rsp")
    s.upload("resource/11.2.0.4/netca.rsp", "/home/data/oracle/rsp/netca.rsp")

    print("【Info】创建/home/data/oracle/rsp/netca.rsp响应文件完成\n")
    print("【Info】正在授权/home/data/oracle/rsp目录...\n")
    
    s.execute("chmod 777 /home/data/oracle/rsp/*.rsp")
    s.execute("chown -R oracle:oinstall /home/data/oracle/rsp")

    print("【Info】授权/home/data/oracle/rsp目录完成\n")

def copyRsps_12201(host):
    s = sshx.SSHConnection(host)

    s.connect()

    print("【Info】正在创建/etc/oraInst.loc配置文件...\n")

    s.execute("rm -rf /etc/oraInst.loc")
    s.upload("resource/12.2.0.1/oraInst.loc", "/etc/oraInst.loc")

    print("【Info】创建/etc/oraInst.loc配置文件完成\n")
    print("【Info】正在授权/etc/oraInst.loc配置文件...\n")
    
    s.execute("chmod 777 /etc")
    s.execute("chmod 777 /etc/oraInst.loc")
    s.execute("chown -R oracle:oinstall /etc/oraInst.loc")

    print("【Info】授权/etc/oraInst.loc配置文件完成\n")
    print("【Info】正在创建/home/data/oracle/rsp/db_install.rsp响应文件...\n")

    with open("resource/12.2.0.1/db_install.rsp", "r+", newline="\n", encoding="utf-8") as f:
        fText = f.read()

    aText = fText.replace("<hostname>", host["host"])

    aText = aText.replace("\r\n", "\n")

    if not os.path.isdir("temp"):
        os.makedirs("temp")

    with open("temp/db_install.rsp", "w+", newline="\n", encoding="utf-8") as f:
        f.write(aText)

    s.execute("rm -rf /home/data/oracle/rsp/db_install.rsp")
    s.upload("temp/db_install.rsp", "/home/data/oracle/rsp/db_install.rsp")

    print("【Info】创建/home/data/oracle/rsp/db_install.rsp响应文件完成\n")
    print("【Info】正在创建/home/data/oracle/rsp/dbca.rsp响应文件...\n")

    s.execute("rm -rf /home/data/oracle/rsp/dbca.rsp")
    s.upload("resource/12.2.0.1/dbca.rsp", "/home/data/oracle/rsp/dbca.rsp")

    print("【Info】创建/home/data/oracle/rsp/dbca.rsp响应文件完成\n")
    print("【Info】正在创建/home/data/oracle/rsp/netca.rsp响应文件...\n")

    s.execute("rm -rf /home/data/oracle/rsp/netca.rsp")
    s.upload("resource/12.2.0.1/netca.rsp", "/home/data/oracle/rsp/netca.rsp")

    print("【Info】创建/home/data/oracle/rsp/netca.rsp响应文件完成\n")
    print("【Info】正在授权/home/data/oracle/rsp目录...\n")
    
    s.execute("chmod 777 /home/data/oracle/rsp/*.rsp")
    s.execute("chown -R oracle:oinstall /home/data/oracle/rsp")

    print("【Info】授权/home/data/oracle/rsp目录完成\n")

def installOracle(host, oracleVer):
    if oracleVer == 1:
        installOracle_11204(host)
    elif oracleVer == 2:
        installOracle_12201(host)

def installOracle_11204(host):
    s = sshx.SSHConnection(host)

    s.connect()

    print("【Info】正在安装Oracle程序，请稍候...\n")
    
    ex = s.execute(". ~/.bash_profile;/home/data/database/database/runInstaller -silent -force -noconfig -ignorePrereq -responseFile /home/data/oracle/rsp/db_install.rsp")

    if ex["status"] == "success":
        print(ex["result"])
        print("【Info】Oracle程序安装完成\n")
    else:
        print(ex["result"])
        print("【Error】Oracle程序安装失败\n")
    
    s.close()

def installOracle_12201(host):
    s = sshx.SSHConnection(host)

    s.connect()

    print("【Info】正在安装Oracle程序，请稍候...\n")
    
    ex = s.execute(". ~/.bash_profile;/home/data/database/database/runInstaller -silent -force -noconfig -ignorePrereq -showProgress -responseFile /home/data/oracle/rsp/db_install.rsp")

    if ex["status"] == "success":
        print(ex["result"])
        ex = s.execute("/home/data/oracle/app/oracle/product/12.2.0/dbhome_1/root.sh")
        print("【Info】Oracle程序安装完成\n")
    else:
        print(ex["result"])
        print("【Error】Oracle程序安装失败\n")
    
    s.close()

def initListener(host, oracleVer):
    if oracleVer == 1:
        initListener_11204(host)
    elif oracleVer == 2:
        initListener_12201(host)

def initListener_11204(host):
    s = sshx.SSHConnection(host)

    s.connect()

    print("【Info】正在配置监听程序，请稍候...\n")

    ex = s.execute("/home/data/oracle/app/oracle/product/11.2.0/dbhome_1/bin/netca /silent /responsefile /home/data/oracle/rsp/netca.rsp")

    if ex["status"] == "success":
        print(ex["result"])
        print("【Info】监听程序配置完成\n")
    else:
        print(ex["result"])
        print("【Error】监听程序配置失败\n")
    
    print("【Info】正在创建/home/data/oracle/app/oracle/product/11.2.0/dbhome_1/network/admin/listener.ora配置文件...\n")

    with open("resource/11.2.0.4/listener.ora", "r+", newline="\n", encoding="utf-8") as f:
        fText = f.read()

    aText = fText.replace("<hostname>", host["host"])

    aText = aText.replace("\r\n", "\n")

    if not os.path.isdir("temp"):
        os.makedirs("temp")

    with open("temp/listener.ora", "w+", newline="\n", encoding="utf-8") as f:
        f.write(aText)
    
    s.execute("rm -rf /home/data/oracle/app/oracle/product/11.2.0/dbhome_1/network/admin/listener.ora")
    s.upload("temp/listener.ora", "/home/data/oracle/app/oracle/product/11.2.0/dbhome_1/network/admin/listener.ora")

    print("【Info】创建/home/data/oracle/app/oracle/product/11.2.0/dbhome_1/network/admin/listener.ora配置文件完成\n")
    print("【Info】正在启动监听程序...\n")

    ex = s.execute(". ~/.bash_profile;lsnrctl stop")
    ex = s.execute(". ~/.bash_profile;lsnrctl start")

    if ex["status"] == "success":
        print(ex["result"])
        print("【Info】监听程序启动完成\n")
    else:
        print(ex["result"])
        print("【Error】监听程序启动失败\n")
    
    s.close()

def initListener_12201(host):
    s = sshx.SSHConnection(host)

    s.connect()

    print("【Info】正在配置监听程序，请稍候...\n")

    ex = s.execute("/home/data/oracle/app/oracle/product/12.2.0/dbhome_1/bin/netca /silent /responsefile /home/data/oracle/rsp/netca.rsp")

    if ex["status"] == "success":
        print(ex["result"])
        print("【Info】监听程序配置完成\n")
    else:
        print(ex["result"])
        print("【Error】监听程序配置失败\n")
    
    print("【Info】正在启动监听程序...\n")

    ex = s.execute(". ~/.bash_profile;lsnrctl stop")
    ex = s.execute(". ~/.bash_profile;lsnrctl start")

    if ex["status"] == "success":
        print(ex["result"])
        print("【Info】监听程序启动完成\n")
    else:
        print(ex["result"])
        print("【Error】监听程序启动失败\n")
    
    s.close()

def initInstance(host, oracleVer):
    if oracleVer == 1:
        initInstance_11204(host)
    elif oracleVer == 2:
        initInstance_12201(host)

def initInstance_11204(host):
    s = sshx.SSHConnection(host)

    s.connect()

    print("【Info】正在初始化Oracle实例，请稍候...\n")
    
    ex = s.execute(". ~/.bash_profile;dbca -silent -createDatabase -responseFile /home/data/oracle/rsp/dbca.rsp -templateName /home/data/oracle/app/oracle/product/11.2.0/dbhome_1/assistants/dbca/templates/General_Purpose.dbc -gdbName orcl -sid orcl -sysPassword gtis -systemPassword gtis -emConfiguration LOCAL -dbsnmpPassword gtis -sysmanPassword gtis")

    if ex["status"] == "success":
        print(ex["result"])
        print("【Info】Oracle实例初始化完成\n")
    else:
        print(ex["result"])
        print("【Error】Oracle实例初始化失败\n")
    
    s.close()

def initInstance_12201(host):
    s = sshx.SSHConnection(host)

    s.connect()

    print("【Info】正在初始化Oracle实例，请稍候...\n")
    
    ex = s.execute(". ~/.bash_profile;dbca -silent -createDatabase  -responseFile /home/data/oracle/rsp/dbca.rsp")

    if ex["status"] == "success":
        print(ex["result"])
        print("【Info】Oracle实例初始化完成\n")
    else:
        print(ex["result"])
        print("【Error】Oracle实例初始化失败\n")
    
    s.close()

def main():

    print("**************************************************")
    print("******Oracle For Linux AutoDeployer***************")
    print("**************************************************\n")
    print("*********Author: Chenfei Jovany Rong Version：1.0\n\n")

    try:
        os.system("pause")
    except:
        pass

    if getConf("DEFAULT", "linuxVerSelect"):
        linuxVerSelect = getConf("DEFAULT", "linuxVerSelect")
    else:
        linuxVerSelect = input("""
【Select】请输入服务器系统版本：【默认为1】
    【1】RedHat/CentOS 7.x 64-bit

""")

        print("\n")

    try:
        if linuxVerSelect != "":
            linuxVer = int(linuxVerSelect)
        else:
            linuxVer = 1

        print("【Info】选择了服务器系统版本为%s\n" % linuxes[linuxVer])

        isGoOn = True

    except:
        print("【Error】无效的输入！\n")
        
        isGoOn = False

    if isGoOn:
        if getConf("DEFAULT", "oracleVerSelect"):
            oracleVerSelect = getConf("DEFAULT", "oracleVerSelect")
        else:
            oracleVerSelect = input("""
【Select】请输入Oracle版本：【默认为1】
    【1】Oracle 11.2.0.4 64-bit
    【2】Oracle 12.2.0.1 64-bit

""")
            print("\n")

        try:
            if oracleVerSelect != "":
                oracleVer = int(oracleVerSelect)
            else:
                oracleVer = 1

            print("【Info】选择了Oracle版本为%s\n" % oracles[oracleVer])

            isGoOn = True

        except:
            print("【Error】无效的输入！\n")
        
            isGoOn = False

    if isGoOn:
        p = getParams()

        if p["status"] == "success":
            isGoOn = True

            host_dict["host"] = p["hostname"]
            host_dict["port"] = p["port"]
            host_dict["username"] = p["username"]
            host_dict["password"] = p["password"]

        else:
            print("【Error】无效的输入！\n")
        
            isGoOn = False

    if isGoOn:
        try:
            shutil.rmtree("temp")
        except:
            pass

        if getConf("DEFAULT", "isUploadRpms"):
            isUploadRpms = getConf("DEFAULT", "isUploadRpms")
        else:
            isUploadRpms = input("""
【Input】是否需要上传RPM依赖包：【y/n，默认n】""")
            print("\n")
        
        if isUploadRpms == "y" or isUploadRpms == "Y":
            #print(host_dict)
            uploadRpms(host_dict)

        if getConf("DEFAULT", "isUploadOracle"):
            isUploadOracle = getConf("DEFAULT", "isUploadOracle")
        else:
            isUploadOracle = input("""
【Input】是否需要上传Oracle安装包：【y/n，默认n】""")
            print("\n")
        
        if isUploadOracle == "y" or isUploadOracle == "Y":
            #print(host_dict)
            uploadOracle(host_dict)

        if getConf("DEFAULT", "isDisableSELinux"):
            isDisableSELinux = getConf("DEFAULT", "isDisableSELinux")
        else:
            isDisableSELinux = input("""
【Input】是否需要关闭SELinux：【y/n，默认y】""")
            print("\n")

        if isDisableSELinux != "n" and isDisableSELinux != "N":
            #print(host_dict)
            disableSELinux(host_dict)

        if getConf("DEFAULT", "isOptimizeKernel"):
            isOptimizeKernel = getConf("DEFAULT", "isOptimizeKernel")
        else:
            isOptimizeKernel = input("""
【Input】是否需要优化内核参数：【y/n，默认y】""")
            print("\n")
        
        if isOptimizeKernel != "n" and isOptimizeKernel != "N":
            #print(host_dict)
            optimizeKernel(host_dict)

        if getConf("DEFAULT", "isDisableFirewall"):
            isDisableFirewall = getConf("DEFAULT", "isDisableFirewall")
        else:
            isDisableFirewall = input("""
【Input】是否需要禁用防火墙：【y/n，默认y】""")
            print("\n")
        
        if isDisableFirewall != "n" and isDisableFirewall != "N":
            #print(host_dict)
            disableFirewall(host_dict)

        if getConf("DEFAULT", "isChangeOSMark"):
            isChangeOSMark = getConf("DEFAULT", "isChangeOSMark")
        else:
            isChangeOSMark = input("""
【Input】是否需要改变系统标识为RedHat：【y/n，默认y】""")
            print("\n")
        
        if isChangeOSMark != "n" and isChangeOSMark != "N":
            #print(host_dict)
            changeOSMark(host_dict)
        
        if getConf("DEFAULT", "isAddGroup"):
            isAddGroup = getConf("DEFAULT", "isAddGroup")
        else:
            isAddGroup = input("""
【Input】是否需要新建用户组oinstall和dba：【y/n，默认y】""")
            print("\n")
        
        if isAddGroup != "n" and isAddGroup != "N":
            #print(host_dict)
            addGroup(host_dict)

        if getConf("DEFAULT", "isAddUser"):
            isAddUser = getConf("DEFAULT", "isAddUser")
        else:
            isAddUser = input("""
【Input】是否需要新建Oracle安装用户（oracle/oracle）：【y/n，默认y】""")
            print("\n")
        
        if isAddUser != "n" and isAddUser != "N":
            #print(host_dict)
            addUser(host_dict, oracleVer)

        if getConf("DEFAULT", "isInstallRpms"):
            isInstallRpms = getConf("DEFAULT", "isInstallRpms")
        else:
            isInstallRpms = input("""
【Input】是否需要安装RPM依赖包：【y/n，默认y】""")
            print("\n")
        
        if isInstallRpms != "n" and isInstallRpms != "N":
            fs = ["binutils-2.27-27.base.el7.x86_64.rpm",
            "binutils-2.27-34.base.el7.x86_64.rpm",
            "binutils-devel-2.27-34.base.el7.i686.rpm",
            "binutils-devel-2.27-34.base.el7.x86_64.rpm",
            "centos-release-7-6.1810.2.el7.centos.x86_64.rpm",
            "centos-release-7-7.1908.0.el7.centos.x86_64.rpm",
            "compat-libcap1-1.10-7.el7.i686.rpm",
            "compat-libcap1-1.10-7.el7.x86_64.rpm",
            "compat-libstdc++-33-3.2.3-72.el7.i686.rpm",
            "compat-libstdc++-33-3.2.3-72.el7.x86_64.rpm",
            "cpp-4.8.5-39.el7.x86_64.rpm",
            "createrepo-0.9.9-28.el7.noarch.rpm",
            "deltarpm-3.6-3.el7.x86_64.rpm",
            "elfutils-libelf-0.170-4.el7.x86_64.rpm",
            "elfutils-libelf-0.172-2.el7.i686.rpm",
            "elfutils-libelf-0.172-2.el7.x86_64.rpm",
            "elfutils-libelf-devel-0.170-4.el7.x86_64.rpm",
            "elfutils-libelf-devel-0.172-2.el7.i686.rpm",
            "elfutils-libelf-devel-0.172-2.el7.x86_64.rpm",
            "elfutils-libelf-devel-static-0.172-2.el7.i686.rpm",
            "elfutils-libelf-devel-static-0.172-2.el7.x86_64.rpm",
            "elfutils-libs-0.172-2.el7.i686.rpm",
            "elfutils-libs-0.172-2.el7.x86_64.rpm",
            "expat-2.1.0-10.el7_3.x86_64.rpm",
            "gc-7.2d-7.el7.i686.rpm",
            "gc-7.2d-7.el7.x86_64.rpm",
            "gc-devel-7.2d-7.el7.i686.rpm",
            "gc-devel-7.2d-7.el7.x86_64.rpm",
            "gcc-4.8.5-28.el7.x86_64.rpm",
            "gcc-4.8.5-36.el7.x86_64.rpm",
            "gcc-c++-4.8.5-28.el7.x86_64.rpm",
            "gcc-c++-4.8.5-36.el7.x86_64.rpm",
            "gcc-gfortran-4.8.5-36.el7.x86_64.rpm",
            "gcc-gnat-4.8.5-36.el7.x86_64.rpm",
            "gcc-go-4.8.5-36.el7.x86_64.rpm",
            "gcc-objc++-4.8.5-36.el7.x86_64.rpm",
            "gcc-objc-4.8.5-36.el7.x86_64.rpm",
            "gcc-plugin-devel-4.8.5-36.el7.x86_64.rpm",
            "glibc-2.17-222.el7.x86_64.rpm",
            "glibc-2.17-260.el7.i686.rpm",
            "glibc-2.17-260.el7.x86_64.rpm",
            "glibc-common-2.17-222.el7.x86_64.rpm",
            "glibc-common-2.17-260.el7.x86_64.rpm",
            "glibc-devel-2.17-222.el7.x86_64.rpm",
            "glibc-devel-2.17-260.el7.i686.rpm",
            "glibc-devel-2.17-260.el7.x86_64.rpm",
            "glibc-headers-2.17-222.el7.x86_64.rpm",
            "glibc-headers-2.17-260.el7.x86_64.rpm",
            "glibc-static-2.17-260.el7.i686.rpm",
            "glibc-static-2.17-260.el7.x86_64.rpm",
            "glibc-utils-2.17-260.el7.x86_64.rpm",
            "kernel-headers-3.10.0-1062.el7.x86_64.rpm",
            "kernel-headers-3.10.0-957.el7.x86_64.rpm",
            "ksh-20120801-137.el7.x86_64.rpm",
            "ksh-20120801-139.el7.x86_64.rpm",
            "libICE-1.0.9-9.el7.x86_64.rpm",
            "libSM-1.2.2-2.el7.x86_64.rpm",
            "libSM-devel-1.2.2-2.el7.x86_64.rpm",
            "libXft-2.3.2-2.el7.x86_64.rpm",
            "libXft-devel-2.3.2-2.el7.x86_64.rpm",
            "libXi-1.7.9-1.el7.i686.rpm",
            "libXi-1.7.9-1.el7.src.rpm",
            "libXi-1.7.9-1.el7.x86_64.rpm",
            "libXp-1.0.2-2.1.el7.i686.rpm",
            "libXp-1.0.2-2.1.el7.x86_64.rpm",
            "libXp-devel-1.0.2-2.1.el7.i686.rpm",
            "libXp-devel-1.0.2-2.1.el7.x86_64.rpm",
            "libXrender-0.9.10-1.el7.x86_64.rpm",
            "libXrender-devel-0.9.10-1.el7.x86_64.rpm",
            "libXt-1.1.5-3.el7.x86_64.rpm",
            "libXt-devel-1.1.5-3.el7.x86_64.rpm",
            "libXtst-1.2.3-1.el7.i686.rpm",
            "libXtst-1.2.3-1.el7.src.rpm",
            "libXtst-1.2.3-1.el7.x86_64.rpm",
            "libaio-0.3.109-13.el7.i686.rpm",
            "libaio-0.3.109-13.el7.x86_64.rpm",
            "libaio-devel-0.3.109-13.el7.i686.rpm",
            "libaio-devel-0.3.109-13.el7.x86_64.rpm",
            "libgcc-4.8.5-28.el7.x86_64.rpm",
            "libgcc-4.8.5-36.el7.i686.rpm",
            "libgcc-4.8.5-36.el7.x86_64.rpm",
            "libmpc-1.0.1-3.el7.x86_64.rpm",
            "libstdc++-4.8.5-28.el7.x86_64.rpm",
            "libstdc++-4.8.5-36.el7.i686.rpm",
            "libstdc++-4.8.5-36.el7.x86_64.rpm",
            "libstdc++-devel-4.8.5-28.el7.x86_64.rpm",
            "libstdc++-devel-4.8.5-36.el7.i686.rpm",
            "libstdc++-devel-4.8.5-36.el7.x86_64.rpm",
            "libstdc++-docs-4.8.5-36.el7.x86_64.rpm",
            "libstdc++-static-4.8.5-36.el7.i686.rpm",
            "libstdc++-static-4.8.5-36.el7.x86_64.rpm",
            "libxml2-python-2.9.1-6.el7_2.3.x86_64.rpm",
            "make-3.82-23.el7.x86_64.rpm",
            "mpfr-3.1.1-4.el7.x86_64.rpm",
            "net-tools-2.0-0.6.20130109git.fc19.x86_64.rpm",
            "numactl-2.0.9-7.el7.x86_64.rpm",
            "pdksh-5.2.14-37.el5_8.1.x86_64.rpm",
            "python-deltarpm-3.6-3.el7.x86_64.rpm",
            "rabbitmq-server-3.6.6-1.el7.noarch.rpm",
            "socat-1.7.3.2-2.el7.x86_64.rpm",
            "sysstat-10.1.5-13.el7.x86_64.rpm",
            "sysstat-10.1.5-17.el7.x86_64.rpm",
            "timedhosts.txt",
            "unixODBC-2.3.1-11.el7.i686.rpm",
            "unixODBC-2.3.1-11.el7.x86_64.rpm",
            "unixODBC-devel-2.3.1-11.el7.i686.rpm",
            "unixODBC-devel-2.3.1-11.el7.x86_64.rpm",
            "unzip-6.0-19.el7.x86_64.rpm",
            "zip-3.0-11.el7.x86_64.rpm"
            ]
            #print(host_dict)
            installRpms(host_dict, fs)

        if getConf("DEFAULT", "isCreateOraDirs"):
            isCreateOraDirs = getConf("DEFAULT", "isCreateOraDirs")
        else:
            isCreateOraDirs = input("""
【Input】是否需要创建Oracle相关目录：【y/n，默认y】""")
            print("\n")

        if isCreateOraDirs != "n" and isCreateOraDirs != "N":
            createOraDirs(host_dict)

        if getConf("DEFAULT", "isUnzipOracle"):
            isUnzipOracle = getConf("DEFAULT", "isUnzipOracle")
        else:
            isUnzipOracle = input("""
【Input】是否需要解压Oracle安装文件：【y/n，默认y】""")
            print("\n")

        if isUnzipOracle != "n" and isUnzipOracle != "N":
            unzipOracle(host_dict, oracleVer)

        setLogin(host_dict)

        setProfile(host_dict, oracleVer)

        copyRsps(host_dict, oracleVer)

        if getConf("DEFAULT", "isReboot"):
            isReboot = getConf("DEFAULT", "isReboot")
        else:
            isReboot = input("""
【Input】是否需要立即重新启动以确保所有配置生效：【y/n，默认y】""")
            print("\n")

        if isReboot != "n" and isReboot != "N":
            reboot(host_dict)

        oracle_dict = host_dict
        oracle_dict["username"] = "oracle"
        oracle_dict["password"] = "oracle"

        if getConf("DEFAULT", "isInstallOracle"):
            isInstallOracle = getConf("DEFAULT", "isInstallOracle")
        else:
            isInstallOracle = input("""
【Input】是否需要安装Oracle数据库软件：【y/n，默认y】""")
            print("\n")

        if isInstallOracle != "n" and isInstallOracle != "N":
            installOracle(oracle_dict, oracleVer)

        if getConf("DEFAULT", "isInitListener"):
            isInitListener = getConf("DEFAULT", "isInitListener")
        else:
            isInitListener = input("""
【Input】是否需要安装初始化监听：【y/n，默认y】""")
            print("\n")

        if isInitListener != "n" and isInitListener != "N":
            initListener(oracle_dict, oracleVer)
        
        initInstance(oracle_dict, oracleVer)

        print("【Info】安装过程已结束\n")
        
        try:
            os.system("pause")
        except:
            pass

if __name__ == '__main__':
    main()

    