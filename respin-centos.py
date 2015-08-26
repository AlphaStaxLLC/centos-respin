#!/usr/bin/env python
"""
Python Script to create a respin CentOS ISO with Custom Packages

"""

import sys
import argparse
import yum
import urllib, urllib2, urlparse
import re
import subprocess
import os
from distutils.dir_util import copy_tree
import shutil
import fileinput
import glob
import xml.etree.ElementTree as ET
import zipfile
import stat


OUTPUT_FILENAME = "CentOS-7-x86_64-Minimal-1503-01-RDO.iso"
PACKAGES = ['yum-utils', 'genisoimage', 'createrepo', 'isomd5sum']
PACKAGE_LIST = "https://github.com/asadpiz/org_centos_cloud/blob/master/PackageList.md"
WORK_DIRECTORY = "/tmp/centos-respin"

def mount_iso(args, iso_mount):
    """
    This function handles the ISO Mounting, if an ISO file is given it just simply
    mounts the ISO. Otherwise it tries to download the ISO over http and then mounts
    it.

    :param args:
    :param iso_mount:
    :return:
    """
    if not args.isofile:
        print ("Downloading ISO Please Wait....\n")
        split = urlparse.urlsplit(str(args.isolink))
        filename = split.path.split("/")[-1]
        urllib.urlretrieve(str(args.isolink), filename)
        args.isofile = filename
        print ("Finished Download\n")
    if os.path.exists(iso_mount):
        if os.path.ismount(iso_mount):
            subprocess.call(["umount", "-f", iso_mount])
        shutil.rmtree(iso_mount)
    os.makedirs(iso_mount)
    subprocess.call(["mount", "-t", "iso9660", "-o", "loop", args.isofile, iso_mount])

def indent(elem, level=0):
    """
    This is just to make the comps file pretty, should be replaced by something
    else in future.

    :param elem:
    :param level:
    :return:
    """

    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
          elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
          elem.tail = i
        for elem in elem:
          indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
          elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
          elem.tail = i

def edit_comps(file,plist):
    """
    Adds a new Software Group to Comps File

    :param file:
    :param plist:
    :return:
    """
    tree = ET.parse(str(file))

    root = tree.getroot()
    group = ET.SubElement(root, 'group')
    id = ET.SubElement(group, 'id')
    name = ET.SubElement(group, 'name')
    description = ET.SubElement(group, 'description')
    default=ET.SubElement(group, 'default')
    uservisible=ET.SubElement(group, 'uservisible')
    packagelist=ET.SubElement(group, 'packagelist')

    id.text = "Cloud"
    name.text = "CentOS Cloud"
    description.text = "Packages from CentOS cloud Repo"
    default.text = "true"
    uservisible.text = "true"

    for elem in plist:
        packagereq = ET.SubElement(packagelist, 'packagereq')
        packagereq.text = elem
        packagereq.set("type","mandatory")

    indent(group)
    tree.write(WORK_DIRECTORY + "/DVD/comps.xml")

def main(argv):
    """
    Main Function:
    Download Required Packages.
    Creates Directories: /mnt/respin-iso, <WORK_DIRECTORY>/DVD, <WORK_DIRECTORY>/Packages


    :param argv:
    :return:
    """
    parser = argparse.ArgumentParser(
        description="Creates a Respin of CentOS. By Default fetches CentOS 7 minimal ISO from the network and adds openstack packages from CentOS Cloud Repo to ISO")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-f", "--isofile", help="ISO File", default=None)
    group.add_argument("-d", "--isodirectory", help="DVD Directory", default=None)
    group.add_argument("-l", "--isolink",
                       help="ISO http Link [DEFAULT] = http://mirror.eu.oneandone.net/linux/distributions/centos/7/isos/x86_64/CentOS-7-x86_64-Minimal-1503-01.iso",
                       default="http://mirror.eu.oneandone.net/linux/distributions/centos/7/isos/x86_64/CentOS-7-x86_64-Minimal-1503-01.iso", )
    parser.add_argument("-p", "--packagelist",
                        help="Package List (only arch x86_64) to be Added to ISO, Make sure the packages you want to download have a corresponding repo in /etc/yum.repos.d/ [DEFAULT] = https://github.com/asadpiz/org_centos_cloud/blob/master/PackageList.md",
                        default=PACKAGE_LIST)
    parser.add_argument("-o", "--output",
                        help="Output Filename [DEFAULT] = CentOS-7-x86_64-RDO-1503.iso",
                        default="CentOS-7-x86_64-RDO-1503.iso")
    args = parser.parse_args()
    FNULL = open(os.devnull, 'w') # Disable output

    # Download Required Packages
    print ("Downloading Dependencies\n")
    p = subprocess.Popen(["yum", "-y", "install"] + PACKAGES[0:],stdout=FNULL)
    p.wait()
    # Create Directories
    iso_mount = "/mnt/respin-iso"
    dvd_dir = WORK_DIRECTORY + "/DVD"
    package_dir = WORK_DIRECTORY + "/Packages"
    if os.path.exists(dvd_dir):
        # Existing DVD Directory Found! Remove & Create New
        shutil.rmtree(dvd_dir)
        os.makedirs(dvd_dir)
    else:
        os.makedirs(dvd_dir)

    if (args.isofile):
        mount_iso(args, iso_mount)
    elif args.isodirectory:
        iso_mount = str(args.isodirectory)
    else:  # DEFAULT or LINK PROVIDED
        mount_iso(args, iso_mount)
    if os.path.exists(iso_mount):
        copy_tree(iso_mount, dvd_dir)
    else:
        raise Exception("No DVD Directory Found!")

    # Download Cloud Addon
    if os.path.exists(dvd_dir + "/images/updates.img"):
        os.remove(dvd_dir + "/images/updates.img")
    urllib.urlretrieve ("https://github.com/asadpiz/org_centos_cloud/releases/download/v0.1-alpha/updates.img", dvd_dir + "/images/updates.img")
    # Fetch Contents of RDO file
    if os.path.exists("RDO.zip"):
        pass
    else:
        # urlretrieve was not blocking
        # urllib.urlretrieve ("https://github.com/asadpiz/centos-respin/blob/master/RDO.zip?raw=true", "RDO.zip")
        f = urllib.urlopen("https://github.com/asadpiz/centos-respin/blob/master/RDO.zip?raw=true")
        with open("RDO.zip", "wb") as zipFile:
            zipFile.write(f.read())
    if os.path.exists(dvd_dir + "/Packages/RDO"):
        shutil.rmtree(dvd_dir + "/Packages/RDO")
    os.makedirs(dvd_dir + "/Packages/RDO")
    z = zipfile.ZipFile("RDO.zip")
    z.extract(r"mkiso.sh", WORK_DIRECTORY + "/")
    for name in z.namelist():
        if str (name) == "mkiso.sh":
            pass
        else:
            z.extract(name, dvd_dir + "/Packages/RDO")
    # Create Cloud Repo with baseurl=http://buildlogs.centos.org/centos/7/cloud/openstack-kilo/
    if os.path.exists("/etc/yum.repos.d/cloud.repo"):
        os.remove("/etc/yum.repos.d/cloud.repo")
    repo_file = open("/etc/yum.repos.d/cloud.repo", "w")
    repo_file.write(
        "[cloud]\nname=CentOS Cloud Packages - $basearch\nbaseurl=http://buildlogs.centos.org/centos/7/cloud/openstack-kilo/\nfailovermethod=priority\nenabled=1\ngpgcheck=0")
    repo_file.close()
    # Fetch PackageList
    plist = []
    if str(args.packagelist).startswith("http"):
        for line in urllib2.urlopen(args.packagelist):
            if args.packagelist == PACKAGE_LIST:
                if str(line).startswith("<p>"):
                    line = re.sub('<[^>]*>', '', line)
                    plist.append(line.strip("\n"))
            else:
                plist.append(str(line.strip("\n")))
    else:
        for line in fileinput.input(args.packagelist):
            plist.append(line.strip("\n"))

    if os.path.exists(WORK_DIRECTORY + "/comps.xml"):
        os.remove(WORK_DIRECTORY + "/comps.xml")
    for file in glob.glob(dvd_dir + "/repodata/*-comps.xml"):
        edit_comps(file,plist)
    shutil.rmtree(dvd_dir + "/repodata")

    # TODO: check if packages already present in directory prompt
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
        os.makedirs(package_dir)
    else:
        os.makedirs(package_dir)

    # TODO: Download Packages via yum API | DNF
    print ("Downloading %d Packages For ISO, Please Wait...\n" % (len(plist)))
    # Updates means two versions of same package will be on ISO which causes Anaconda to Act Up
    p = subprocess.Popen(["yum","-y", "install", "--installroot="+ WORK_DIRECTORY, "--disablerepo=updates","--downloadonly",
                              "--downloaddir=" + package_dir] + plist[0:],stdout=FNULL)


    # p = subprocess.Popen(["yumdownloader", "--installroot=" + WORK_DIRECTORY, "-x *.i686", "--resolve",
    #                              "--destdir=" + str(package_dir)] + plist[0:])
    p.wait()

    copy_tree(package_dir, dvd_dir + "/Packages")
    print ("Done Downloading Packages\n")

    #  createrepo -g /DVD/comps.xml .
    print ("Creating Custom Repo\n")
    p=subprocess.Popen(["createrepo", "-g", "comps.xml", dvd_dir], cwd=dvd_dir, stdout=FNULL)
    p.wait()
    print ("Creating ISO....")

    # print label
    st = os.stat(WORK_DIRECTORY + "/mkiso.sh")
    os.chmod(WORK_DIRECTORY + "/mkiso.sh", st.st_mode | stat.S_IEXEC)
    subprocess.call(["./mkiso.sh", args.output],cwd=WORK_DIRECTORY,stdout=FNULL)
    if args.output == "CentOS-7-x86_64-Minimal-1503-01-RDO.iso":
        print ("\n\nISO CREATION COMPLETE!!! FILE CAN BE FOUND AT: " + WORK_DIRECTORY + "/" +OUTPUT_FILENAME)
    else:
        print ("\n\nISO CREATION COMPLETE!!! FILE CAN BE FOUND AT: " + args.output + "\n DEFAULT PATH: " + WORK_DIRECTORY)

    # Cleanup Removes Downloaded ISO file, mounted directory (if -d not specified), DVD directory and downloaded Packages Directory
    file_names = os.listdir(os.curdir)
    for downloaded_iso in file_names:
        if os.path.isfile(downloaded_iso) and downloaded_iso.endswith(".iso"):
            os.remove(downloaded_iso)
    if not args.isodirectory:
        subprocess.call(["umount", "-f", iso_mount])
    if os.path.exists(dvd_dir):
         shutil.rmtree(dvd_dir)
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    if os.path.exists(WORK_DIRECTORY+"/var"):
        shutil.rmtree(WORK_DIRECTORY+"/var")
    os.remove(WORK_DIRECTORY+"/mkiso.sh")
    os.remove("/etc/yum.repos.d/cloud.repo")
    os.remove("RDO.zip")

if __name__ == "__main__":
    main(sys.argv)
