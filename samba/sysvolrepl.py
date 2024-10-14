#!/usr/bin/python3

import dns.resolver
import subprocess

#Global vars
DOMAIN="example.com"
MOUNTPATH="/mnt/sysvol"
CREDFILE="/root/.smbcreds"
SAMBADIR="/var/lib/samba"

#start of main program
print("----------")

print("resolving dns for fsmo role")
pdcempath=dns.resolver.resolve("_ldap._tcp.pdc._msdcs."+DOMAIN, 'SRV')[0].target.to_text()

#format dns address
pdcempath="//"+pdcempath[0:len(pdcempath)-1]

print("PDC master is at "+pdcempath)
print("Checking mount")

#run findmnt -o SOURCE -n /mnt/sysvol
findmnt = subprocess.run(["findmnt","-o","SOURCE","-n",MOUNTPATH],capture_output=True)

#check if there was an error message. If there was print it and exit
if not (str(findmnt.stderr,"utf-8") == ""):
    print("error: "+findmnt.stderr)
    exit(findmnt.returncode)

#get current mount
currentmount = str(findmnt.stdout,"utf-8").rstrip()

#fix if needed
if (currentmount == ""):
    print("nothing mounted so mounting directly")
    #mount -t cifs -o crredentials= //domain /mnt/sysvol
    subprocess.run(["mount", "-t", "cifs", "-o", "credentials="+CREDFILE,pdcempath+"/sysvol",MOUNTPATH])
elif not (currentmount == (pdcempath+"/sysvol")):
    print("current mount is "+currentmount+" which is not correct")
    print("umounting")
    subprocess.run(["umount",MOUNTPATH])
    print("mounting "+result+"/sysvol")
    subprocess.run(["mount", "-t", "cifs", "-o", "credentials="+CREDFILE,pdcempath+"/sysvol",MOUNTPATH])
else:
    print("mount correct")

#run rsync
print("running rsync with "+MOUNTPATH+" and "+SAMBADIR)
subprocess.run(["rsync", "-XAavz", "--delete-after", MOUNTPATH, SAMBADIR])
print("-----")
