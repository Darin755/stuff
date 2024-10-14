#!/usr/bin/python3

#os imported to run commands
import os
import subprocess
#socket imported to to dns lookups
import socket
#args
import argparse

#This is a script to join a Linux Machine to a Active Directory domain. 
#This will only work on Linux
    
def checkDns(domain):
    print("checking DNS")
    try:
        #main domain
        print("trying to resolve "+domain)
        socket.gethostbyname_ex(domain)
        
        #Maybe add more verification

    except:
        print("E: Could not reolve domain name")
        print("This is most likely due to bad DNS settings. Try configuring systemd resolved or simular")
        exit(1)

def checkRoot():
    if os.geteuid() != 0:
        print("E: please run this as root")
        exit(1)


checkRoot()

#set args
parser = argparse.ArgumentParser(description="A script to join a Linux computer to AD")
parser.add_argument('--domain', help='The Active directory domain name (Needs to be resolvable)')
parser.add_argument('--use-current-hostname', action='store', nargs='*',help="Use the current hostname in /etc/hostname")
parser.add_argument('--username', help='Set the admin username')

#read actual args 
args = parser.parse_args()

#Start
print("Welcome!\nThis script will install realmd and join this machine to a domain.")
print("starting setup")
#get and check domain
if args.domain:
    domain = args.domain
else:
    anw = "n"
    while not (anw[0] == 'y'):
        domain = input("Please enter a domain name (ex. example.lan): ").strip()
        anw = input("Is "+domain+" the correct domain? (type y for yes): ")
    #check resolvablity

checkDns(domain)
print("domain resolved successfully")

oldhostname = ""
try:
    with open("/etc/hostname","r") as fp:
        oldhostname = fp.read().strip()
except:
    print("failed to read /etc/hostname")
    
if oldhostname == "":
    #import uuid and grab the end part
    import uuid
    oldhostname = "computer-"+str(uuid.uuid4())[0:8]
#check if domain already present
elif oldhostname[len(oldhostname)-len(domain):len(oldhostname)] == domain:
    #remove domain
    oldhostname = oldhostname[0:len(oldhostname)-len(domain)-1]

if (args.use_current_hostname == None):
    if not (input("Is "+oldhostname+" a good hostname name (enter y for yes): ")[0] == "y"):
        print("please enter a hostname. Do not include the "+domain+" ending")
        oldhostname = input("hostname: ")
else:
    print("using "+oldhostname+" as hostname")

print("setting hostname to "+oldhostname+"."+domain)
#set hostname
if (oldhostname[len(oldhostname)-len(domain):len(oldhostname)] == domain):
    subprocess.call(["hostnamectl","set-hostname",oldhostname])
else:
    subprocess.call(["hostnamectl","set-hostname",oldhostname+"."+domain])

print("installing realmd")
    #install realmd
try:
    #check if it is installed already
    subprocess.call(["realm"],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    print("realmd already installed")
except:
    try:
        #dnf handles everything automaticlly
        subprocess.call(["dnf","install","realmd","-y"])
        print("installed realmd with dnf")
    except:
        try:
            #apt needs a lists update
            subprocess.call(["apt","update"])
            subprocess.call(["apt", "install", "realmd", "-y"])
        except:
            print("E:Failed to install realmd. Please install it manually")
            exit(1)
    try:
        subprocess.call(["realm"],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
        print("realmd install successfully")
    except:
        print("E: realmd is not installed for some reason")
        exit(1)
# realm should be installed by now

# get user
if args.username == None:
    user = input("enter admin username for "+domain+": ")
else:
    user = args.username

#run realmd
subprocess.call(["realm","join","-v",domain,"-U", user])

#we add the option to disable use_fully_qualified_names
print("reading sssd.conf")
print("backing up sssd.conf to /etc/ssd/sssd.conf.bak")
#backup sssd.conf
subprocess.call(["cp","/etc/sssd/sssd.conf", "/etc/sssd/sssd.conf.bak"],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
try:
    with open('/etc/sssd/sssd.conf','r') as fp:
        filedata = fp.read()
        if ("use_fully_qualified_names" in filedata):
            lines = filedata.splitlines()
            for i in range(0,len(lines)):
                if "use_fully_qualified_names" in lines[i]:
                    print("setting use_fully_qualified_names to False")
                    lines[i] = "use_fully_qualified_names = False"
                    break
            with open('/etc/sssd/sssd.conf','w') as f2:
                for line in lines:
                    f2.write(line+"\n")
        else:
            print("adding use_fully_qualified_names = False")
            with open('/etc/sssd/sssd.conf','a') as fp2:
                fp2.write("use_fully_qualified_names = False")
except:
    print("could not process sssd.conf")

            


#configure pam
print("enabling mkhomedir in pam")
try:
    subprocess.call(["pam-auth-update","--enable","mkhomedir"])
#   with open('/etc/pam.d/common-session','r') as f:
#        filedata = f.read()
#        if not ("pam_mkhomedir.so" in filedata):
#            print("modifying pam to allow for creation of user homes")
#            print("backup at /etc/pam.d/common-session.bak")
#            subprocess.call(["cp","/etc/pam.d/common-session", "/etc/pam.d/common-session.bak"],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
#            lines = filedata.splitlines()
#            for i in range(0,len(lines)):
#                if "pam_unix.so" in lines[i]:
#                    print("adding mkhomedir.so")
#                    lines.insert(i+1,"session required pam_mkhomedir.so skel=/etc/skel umask=0077")
#                    break
#            with open('/etc/pam.d/common-session','w') as f2:
#                for line in lines:
#                    f2.write(line+"\n")

except:
    print("Failed but this is likely not going to be a problem")
    print("skipping adding pam_mkhomedir.so to pam")


#restart sssd
print("restarting sssd")
subprocess.call(["systemctl","restart", "sssd"],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)

#we a done
print("This computer is now theoretically joined to "+domain+". Try su - [username] or su - [username]@"+domain)
print("bye")

