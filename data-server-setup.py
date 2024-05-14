import shlex, subprocess, sys, distro, os

def shell(command):
    p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    while p.poll() is None:
        print(out)
    p.wait()
    return out.decode('utf-8'), err

def install():
    if distro.name() == "Ubuntu":
        print(shell("sudo apt install xrootd"))
def init():
    file = open("xrootd.cfg", "w")
    file.write("xrootd.export /data\nxrootd.chksum md5")
def run():
    print(shell("xrootd -c xrootd.cfg"))

def main():
    for i, args in enumerate(sys.argv):
        if(args=="--init"):
            print("Install xrootd server")
            install()
            init()
            exit(0)
    run()
main()