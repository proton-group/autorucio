# usage
# set hostname:
# --hostname myhostname
#
# if you need ssl (you need ssl) 
# select flag: --ssl
# give ca certificate: --ca-cert /path/cert
#
# userdata:
# --auth_type userpass (now work only userpass as default)
# --username name
# --password pass
# account type (root default):
# --account account_type

import sys

class Config:
    auth_type = "userpass"
    username = ""
    password = ""
    account_type = "root"
    hostname = ""
    ssl_flag = False
    cert = "/opt/rucio/etc/rootCAcrt.pem"

class GeneratorException(Exception):
    pass

def generator(cfg):
    file = open("rucio.cfg", "w")
    if(cfg.hostname == ""):
        raise GeneratorException("Hostname is needed.\nPlease, enter rucio server hostname with ==hostname flag")
    if cfg.ssl_flag:
        file.write("[client]\nrucio_host = https://" + cfg.hostname + ":443\n" + \
                    "auth_host = https://" + cfg.hostname + ":443\n" + \
                    "ca_cert = " + cfg.cert + "\n")
    else:
        file.write("[client]\nrucio_host = http://" + cfg.hostname + ":80\n" + \
                    "auth_host = http://" + cfg.hostname + ":80\n")
    if cfg.auth_type == "userpass":
        if(cfg.username == ""):
            raise GeneratorException("Username is needed.\nPlease enter your account name with --username flag")
        if(cfg.password == ""):
            raise GeneratorException("Password is needed.\nPlease enter your account name with --password flag")
        file.write("auth_type = userpass\n" + \
                    "username = " + cfg.username + "\n" + \
                    "password = " + cfg.password + "\n" + \
                    "account = " + cfg.account_type + "\n")
    file.write("request_retries = 3\n\n" + \
                "[policy]\n" + \
                "permission = generic\n" + \
                "schema = generic\n" + \
                "lfn2pfn_algorithm_default = hash\n" + \
                "support = https://github.com/rucio/rucio/issues/\n" + \
                "support_rucio = https://github.com/rucio/rucio/issues/")
    file.close()
    print("Please, copy rucio.cfg file from local directory to /opt/rucio/etc")

def configParser(cfg):
    for i in range(len(sys.argv)):
        if sys.argv[i] == "--auth_type":
            cfg.auth_type = sys.argv[i+1]
        if sys.argv[i] == "--account":
            cfg.account_type = sys.argv[i+1]
        if sys.argv[i] == "--username":
            cfg.username = sys.argv[i+1]
        if sys.argv[i] == "--password":
            cfg.password = sys.argv[i+1]
        if sys.argv[i] == "--hostname":
            cfg.hostname = sys.argv[i+1]
        if sys.argv[i] == "--ssl":
            cfg.ssl_flag = True
        if sys.argv[i] == "--ca-cert":
            cfg.cert = sys.argv[i+1]

if sys.argv[1] == "--help":
    print("usage:\n\
        set hostname:\n\
        --hostname myhostname\n\
        if you need ssl (you need ssl)\n\
        select flag: --ssl\n\
        give ca certificate: --ca-cert /path/cert\n\
        userdata:\n\
        --auth_type userpass (now work only userpass as default)\n\
        --username name\n\
        --password pass\n\
        account type (root default):\n\
        --account account_type\n")
    exit(0)

myconfig = Config()
configParser(myconfig)
generator(myconfig)