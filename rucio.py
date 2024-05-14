import os
import sys, subprocess, shlex

def shell(command):
    p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    while p.poll() is None:
        print(out)
    p.wait()
    return out.decode('utf-8'), err

def init(crt, cfg, path):
    shell("sudo docker stop rucio-client")
    shell("sudo docker rm rucio-client")
    if path == "":
        shell("sudo docker run -v " + cfg + ":/opt/rucio/etc/rucio.cfg -v " + crt + \
            ":/opt/rucio/etc/rootCAcrt.pem " + "-v .:/home/user --name=rucio-client -it -d rucio/rucio-clients")
    else:
        shell("sudo docker run -v " + cfg + ":/opt/rucio/etc/rucio.cfg -v " + crt + \
            ":/opt/rucio/etc/rootCAcrt.pem " + "-v " + path + ".:/home/user --name=rucio-client -it -d rucio/rucio-clients")

def client():
    datapath = ""
    for i, args in enumerate(sys.argv):
        if(args=="--path"):
            datapath = sys.argv[i+1]
        if(args=="--init"):
            init(sys.argv[i+1], sys.argv[i+2], datapath)
            exit(0)
        if(args=="--help"):
            print("usage:\nUse --init with ca certificate and rucio.cfg files path as parameters \
                for initialization.\nAfter use \"python3 rucio.py\" as classic rucio client.\nFor rucio client help run script without args.")
            exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == "admin":
        print("".join(str(x) + " " for x in sys.argv[2:]))
        out, err = shell("sudo docker exec -it rucio-client rucio-admin " + "".join(str(x) + " " for x in sys.argv[2:]))
    else:        
        out, err = shell("sudo docker exec -it rucio-client rucio " + "".join(str(x) + " " for x in sys.argv[1:]))
    print(out)
    if(err != b''):
        print(err.decode())
client()