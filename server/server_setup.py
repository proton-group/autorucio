import shlex, subprocess, sys, distro, os
from getpass import getpass

#rucio.cfg

def shell(command):
    p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    while p.poll() is None:
        print(out)
    p.wait()
    return out.decode('utf-8'), err

def shell_pipe(command1, command2):
    p = subprocess.Popen(shlex.split(command1), stdout=subprocess.PIPE)
    out = subprocess.check_output(shlex.split(command2), stdin=p.stdout)
    p.wait()
    return out.decode('utf-8')

def install_manager():
    out = "docker"
    if distro.name() == "centos":
        out = shell_pipe("dpkg --list","grep docker")
    if distro.name() == "Fedora Linux":
        out = shell_pipe("dpkg --list","grep docker")
    if distro.name() == "Ubuntu":
        out = shell_pipe("dpkg --list","grep docker")
    if not "docker" in out:
        docker_setup()
    if distro.name() == "centos":
        out = shell_pipe("dpkg --list","grep postgresql")
        if not 'postgresql' in out:
            print("Postgresql init...")
            postgres_setup()
    if distro.name() == "Fedora Linux":
        out = shell_pipe("dpkg --list","grep postgresql")
        if not 'postgresql' in out:
            print("Postgresql init...")
            postgres_setup()
    if distro.name() == "Ubuntu":
        out = shell_pipe("dpkg --list","grep postgresql")
        if not 'postgresql' in out:
            print("System doesn't have postgresql package or script can't detect it. Install postgresql with postgres-install.sh and AFTER USE THIS SCRIPT WITH --init postgresql argument. TERMINATE.")
            exit(-1)
        print("Postgresql init...")
        postgres_setup()

def docker_setup():
    if distro.name() == "centos":
        shell("yum -y install docker")
    if distro.name() == "Fedora Linux":
        shell("dnf -y install docker")
    if distro.name() == "Ubuntu":
        print("You need to install Docker with another script. TERMINATE")
        exit(0)

def postgres_setup():
    for i, args in enumerate(sys.argv):
        if(args=="--init" and sys.argv[i+1]=="postgresql"):
            if distro.name() == "centos":
                shell("yum -y install postgresql-server")
                shell("postgresql-setup --initdb")
                shell("mv /var/lib/pgsql/data/pg_hba.conf /var/lib/pgsql/data/pg_hba.conf.old")
                file = open("/var/lib/pgsql/data/pg_hba.conf", "w")
            if distro.name() == "Fedora Linux":
                shell("dnf -y install postgresql-server")
                shell("postgresql-setup --initdb")
                shell("mv /var/lib/pgsql/data/pg_hba.conf /var/lib/pgsql/data/pg_hba.conf.old")
                file = open("/var/lib/pgsql/data/pg_hba.conf", "w")
            if distro.name() == "Ubuntu":
                shell("mv /etc/postgresql/14/main/pg_hba.conf /etc/postgresql/14/main/pg_hba.conf.old")
                file = open("/etc/postgresql/14/main/pg_hba.conf", "w")
            file.write("local   all             postgres                                peer\n"+ \
                            "# TYPE  DATABASE        USER            ADDRESS                 METHOD\n" + \
                            "# \"local\" is for Unix domain socket connections only\n" + \
                            "local   all             all                                     peer\n" +\
                            "# IPv4 local connections:\n" +\
                            "host    all             all             127.0.0.1/32            trust\n" +\
                            "# IPv6 local connections:\n" +\
                            "host    all             all             ::1/128                 trust\n" +\
                            "# Allow replication connections from localhost, by a user with the\n" +\
                            "# replication privilege.\n" +\
                            "local   replication     all                                     peer\n" +\
                            "host    replication     all             127.0.0.1/32            scram-sha-256\n" +\
                            "host    replication     all             ::1/128                 scram-sha-256\n")
            file.close()
            shell("systemctl restart postgresql")
        
def password_check():
    if not "--password" in sys.argv:
        print("Database password is needed. Run script with --password argument")
        exit(-1)

def ssl_config(domain):
    #certbot
    shell("mkdir ./rucio_certs")
    shell("openssl req -nodes -newkey rsa:2048 -keyout ./rucio_certs/ruciokey.pem -out ./rucio_certs/ruciocsr.pem -outform PEM -subj \"/C=RU/ST=LenObl/L=SPB/O=JINR/OU=IT Department/CN=" + domain + "\"")
    shell("openssl req -nodes -x509 -sha256 -days 1825 -newkey rsa:2048 -keyout ./rucio_certs/rootCAkey.pem -out ./rucio_certs/rootCAcrt.pem -outform PEM -subj \"/C=RU/ST=LenObl/L=SPB/O=JINR/OU=IT Department/CN=JINRCA\"")
    shell("touch ./rucio_certs/domain.ext")
    file = open("./rucio_certs/domain.ext", "w")
    file.write("authorityKeyIdentifier=keyid,issuer\n" +\
                    "basicConstraints=CA:FALSE\n" +\
                    "subjectAltName = @alt_names\n" +\
                    "[alt_names]\n" +\
                    "DNS.1 = " + domain + "\n" +\
                    "IP.1 = " + domain + "\n")
    file.close()
    '''
    shell("echo \"authorityKeyIdentifier=keyid,issuer\n" +\
                    "basicConstraints=CA:FALSE\n" +\
                    "subjectAltName = @alt_names\n" +\
                    "[alt_names]\n" +\
                    "DNS.1 = " + domain + "\n\" > ./rucio_certs/domain.ext")
    '''
    shell("openssl x509 -req -CA ./rucio_certs/rootCAcrt.pem -CAkey ./rucio_certs/rootCAkey.pem -in ./rucio_certs/ruciocsr.pem -out ./rucio_certs/domain.pem -outform PEM -days 365 -CAcreateserial -extfile ./rucio_certs/domain.ext")

def rucio_server(ssl):
    for i, args in enumerate(sys.argv):
        if(args=="--init" and sys.argv[i+1]=="rucio"):
            print("Configuration... Making root account.\n")
            print("New username:")
            username = input()
            password = getpass()
            password_check()
            print("Rucio database initialization...")
            command = "sudo -u postgres createdb rucio"
            out,err = shell(command)
            command = "docker run --network host --rm -e RUCIO_CFG_DATABASE_DEFAULT=\"postgresql://localhost:5432/rucio?user=postgres&password=" + \
                sys.argv[sys.argv.index("--password") + 1] + \
                    "\" -e RUCIO_CFG_BOOTSTRAP_USERPASS_IDENTITY=\"" + username + "\" -e RUCIO_CFG_BOOTSTRAP_USERPASS_PWD=\"" + password + "\" rucio/rucio-init"
            out,err = shell(command)
    password_check()
    print("Please, use this ca certificate for clients:")
    file = open("rucio_certs/rootCAcrt.pem")
    print(file.read())
    file.close()
    print("rucio server running...")
    shell("sudo docker stop rucio-server")
    shell("sudo docker rm rucio-server")
    if not ssl:
        command = "docker run --network host --name=rucio-server -e RUCIO_CFG_DATABASE_DEFAULT=\"postgresql://localhost:5432/rucio?user=postgres&password=" + \
        sys.argv[sys.argv.index("--password") + 1] + \
            "\" -p 80:80 rucio/rucio-server"
    if ssl:
        command = "docker run --network host --name=rucio-server -e RUCIO_CFG_DATABASE_DEFAULT=\"postgresql://localhost:5432/rucio?user=postgres&password=" + \
        sys.argv[sys.argv.index("--password") + 1] + \
            "\" -v ./rucio_certs/rootCAcrt.pem:/etc/grid-security/ca.pem -v ./rucio_certs/domain.pem:/etc/grid-security/hostcert.pem" + \
                " -v ./rucio_certs/ruciokey.pem:/etc/grid-security/hostkey.pem -p 443:443 -e RUCIO_ENABLE_SSL=True rucio/rucio-server"
    out, err = shell(command)
    print(out)
    print(err)
    print("Rucio server start")

def sudoers_check():
    if os.geteuid() != 0:
        exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")
#Rucio Configuration
sudoers_check()
install_manager()
for i, args in enumerate(sys.argv):
    if(args=="--help"):
        print("Usage:\n")
        print("python3 server_setup.py --init postgresql --init rucio --ssl --password mypassword --domain mydomai.org\n")
        print("args:")
        print("\"--init postgresql\" for install and initialize database (use with --password arg for set db password)")
        print("\"--init rucio\" initialize rucio server (u need init database)")
        print("\"--ssl\" for secure (use with --domain arg for set domain name)")
        print("\"--domain mydomain.org\" set domain for ssl certificate")
        print("\"--password mypassword\" set PostgreSQL password for init database")
        exit(0)
for i, args in enumerate(sys.argv):
    if(args=="--ssl"):
        for i, args in enumerate(sys.argv):
            if(args=="--domain"):
                print("setup ssl...")
                ssl_config(sys.argv[i+1])
        print("Rucio server script started")
        rucio_server(True)
        exit(0)
print("Rucio server script started")
rucio_server(False)