"""
Python Script to create a respin CentOS ISO with Custom Packages

"""

import sys
import argparse
import yum
import urllib2
import re
import subprocess
import os
from distutils.dir_util import copy_tree
import shutil
import fileinput

OUTPUT_FILENAME = "CentOS-7-x86_64-Minimal-1503-01-RDO.iso"
PACKAGES = ['yum-utils', 'genisoimage', 'createrepo']
PACKAGE_LIST = "https://github.com/asadpiz/org_centos_cloud/blob/master/PackageList.md"
WORK_DIRECTORY= "/tmp/centos-respin"
PATH= "/var/cache/yum"

def main(argv):
    parser = argparse.ArgumentParser(
        description="Creates a Respin of CentOS. By Default fetches CentOS 7 minimal ISO from the network and adds openstack packages from CentOS Cloud Repo to ISO")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-f", "--isofile", help="CentOS ISO File")
    group.add_argument("-d", "--isodirectory", help="CentOS DVD Directory")
    group.add_argument("-l", "--isolink",
                       help="CentOS ISO Link [DEFAULT] = http://mirror.eu.oneandone.net/linux/distributions/centos/7/isos/x86_64/CentOS-7-x86_64-Minimal-1503-01.iso",
                       default="http://mirror.eu.oneandone.net/linux/distributions/centos/7/isos/x86_64/CentOS-7-x86_64-Minimal-1503-01.iso", )
    parser.add_argument("-o", "--output", help="Output filename [DEFAULT] = CentOS-7-x86_64-Minimal-1503-01-RDO.iso",
                        default="CentOS-7-x86_64-Minimal-1503-01-RDO.iso")
    parser.add_argument("-p", "--packagelist",
                        help="Package List to be Added to ISO [DEFAULT] = https://github.com/asadpiz/org_centos_cloud/blob/master/PackageList.md",
                        default=PACKAGE_LIST)
    args = parser.parse_args()

    # ENABLE CACHE
    for line in fileinput.input('/etc/yum.conf', inplace=True):
        if str(line).startswith("keepcache=0"):
            print(line.replace("keepcache=0", "keepcache=1").rstrip("\n"))
        else:
            print (line)
    fileinput.close()


    # Download Required Packages
    yb = yum.YumBase()
    yb.add_enable_repo('myrepo', ['http://buildlogs.centos.org/centos/7/cloud/openstack-kilo/'])
    installed = [x.name for x in (yb.rpmdb.returnPackages())]
    for package in PACKAGES:
        if package in installed:
            print('{0} is already installed'.format(package))
        else:
            print('Installing {0}'.format(package))
            kwarg = {
                'name': package
            }
            yb.install(**kwarg)
            yb.resolveDeps()
            yb.buildTransaction()
            yb.processTransaction()

    # Fetch PackageList
    plist = ["",]
    for line in urllib2.urlopen(args.packagelist):
        if args.packagelist == PACKAGE_LIST:
            if str (line).startswith("<p>"):
                line = re.sub('<[^>]*>', '', line)
                plist.append(line.strip("\n"))
        else:
            plist.append(str(line.strip("\n")))

    # Create backup of current cache
    if os.path.exists(WORK_DIRECTORY):
        os.rmdir(WORK_DIRECTORY)
        os.makedirs(WORK_DIRECTORY)
    else:
        os.makedirs(WORK_DIRECTORY)
    copy_tree("/var/cache/yum", WORK_DIRECTORY + "/")
    shutil.rmtree("/var/cache/yum/")

    # Create Cloud Repo

    # Download Packages in /var/cache
    process = subprocess.Popen(["yumdownloader"] + plist, stdout=subprocess.PIPE)
    for line in iter(process.stdout.readline, ''):
            sys.stdout.write(line)

    # yb.add_enable_repo('myrepo', ['http://buildlogs.centos.org/centos/7/cloud/openstack-kilo/'])
    # installed = [x.name for x in (yb.rpmdb.returnPackages())]
    # plist = ["", ]
    #
    # for line in urllib2.urlopen(PACKAGE_LIST):
    #     if str (line).startswith("<p>"):
    #         line = re.sub('<[^>]*>', '', line)
    #         plist.append(line.strip("\n"))
    # print (plist)
    # pkgs = yb.pkgSack.searchNames(plist)
    # for pkg in pkgs:
    #     print "%s: %s" % (pkg, pkg.summary)
    #     print (pkgs)
    #     yb.downloadPkgs(pkg)
    # CLEANUP Copy Contents of Cache back
    if os.path.exists("/var/cache/yum"):
        print ("pathh exists")
        copy_tree(WORK_DIRECTORY + "/", "/var/cache/yum/")
    else:
        print ("path doesn'te xist")
        os.mkdir(PATH)
        copy_tree(WORK_DIRECTORY + "/", "/var/cache/yum/")
    # Download List of Packages
if __name__ == "__main__":
    main(sys.argv)  # We don't want Script's own name to be parsed
