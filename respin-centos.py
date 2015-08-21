#!/usr/bin/env python
"""
Python Script to create a respin CentOS ISO with Custom Packages

"""

import sys
import argparse
import yum
import urllib, urllib2
import re
import subprocess
import os
from distutils.dir_util import copy_tree
import shutil
import fileinput
import glob
import xml.etree.ElementTree as ET


OUTPUT_FILENAME = "CentOS-7-x86_64-Minimal-1503-01-RDO.iso"
PACKAGES = ['yum-utils', 'genisoimage', 'createrepo']
PACKAGE_LIST = "https://github.com/asadpiz/org_centos_cloud/blob/master/PackageList.md"
WORK_DIRECTORY = "/tmp/centos-respin"
REPO_LINK = "https://raw.githubusercontent.com/asadpiz/centos-respin/master/cloud.repo"

def mount_iso(args, iso_mount):
    if not args.isofile:
        urllib.urlretrieve(str(args.isolink), "CentOS-7-x86_64-Minimal-1503-01.iso")
        args.isofile = "CentOS-7-x86_64-Minimal-1503-01.iso"
    if os.path.exists(iso_mount):
        if os.path.ismount(iso_mount):
            subprocess.call(["umount", "-f", iso_mount])
        shutil.rmtree(iso_mount)
    os.makedirs(iso_mount)
    subprocess.call(["mount", "-t", "iso9660", "-o", "loop", args.isofile, iso_mount])

def indent(elem, level=0):
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
    tree = ET.parse(str(file))

    root = tree.getroot()
    group = ET.SubElement(root, 'group')
    id = ET.SubElement(group, 'id')
    id.text = "Cloud"
    name = ET.SubElement(group, 'name')
    name.text = "CentOS Cloud"
    description = ET.SubElement(group, 'description')
    description.text = "Packages from CentOS cloud Repo"
    default=ET.SubElement(group, 'default')
    uservisible=ET.SubElement(group, 'uservisible')
    packagelist=ET.SubElement(group, 'packagelist')
    default.text = "true"
    uservisible.text = "true"
    for elem in plist[1:]: # TODO EDIT For custom packages
        packagereq = ET.SubElement(packagelist, 'packagereq')
        packagereq.text = elem
        packagereq.set("type","mandatory")

    indent(group)
    tree.write(WORK_DIRECTORY + "/DVD/comps.xml")
    # TODO: Add new packages to a category that appears during install

def main(argv):
    parser = argparse.ArgumentParser(
        description="Creates a Respin of CentOS. By Default fetches CentOS 7 minimal ISO from the network and adds openstack packages from CentOS Cloud Repo to ISO")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-f", "--isofile", help="CentOS ISO File", default=None)
    group.add_argument("-d", "--isodirectory", help="CentOS DVD Directory", default=None)
    group.add_argument("-l", "--isolink",
                       help="CentOS ISO Link [DEFAULT] = http://mirror.eu.oneandone.net/linux/distributions/centos/7/isos/x86_64/CentOS-7-x86_64-Minimal-1503-01.iso",
                       default="http://mirror.eu.oneandone.net/linux/distributions/centos/7/isos/x86_64/CentOS-7-x86_64-Minimal-1503-01.iso", )
    parser.add_argument("-o", "--output", help="Output filename [DEFAULT] = CentOS-7-x86_64-Minimal-1503-01-RDO.iso",
                        default="CentOS-7-x86_64-Minimal-1503-01-RDO.iso")
    parser.add_argument("-p", "--packagelist",
                        help="Package List to be Added to ISO [DEFAULT] = https://github.com/asadpiz/org_centos_cloud/blob/master/PackageList.md",
                        default=PACKAGE_LIST)
    # group.add_argument("-c", "--cleanup",action="store_true", help="Cleanup Working Directory", default=False)
    args = parser.parse_args()

    iso_mount = "/mnt/cent-respin"
    dvd_dir = WORK_DIRECTORY + "/DVD"
    package_dir = WORK_DIRECTORY + "/Packages"

    # Handling ISO
    if os.path.exists(dvd_dir):
        # raw_input("Existing DVD Directory Found! Do you want to Keep this directory or ")
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

    # Create Cloud Repo
    shutil.copy("cloud.repo", "/etc/yum.repos.d/cloud.repo")

    # Download Required Packages
    yb = yum.YumBase()
    installed = [x.name for x in (yb.rpmdb.returnPackages())]
    for package in PACKAGES:
        if package in installed:
            pass
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
    plist = ["", ]
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
    #   shutil.copy(file, WORK_DIRECTORY + "/comps.xml")
    shutil.rmtree(dvd_dir + "/repodata")
    for line in fileinput.input(dvd_dir + "/TRANS.TBL", inplace=True):
        print ""

    if not args.isodirectory:
        subprocess.call(["umount", "-f", iso_mount])

    # TODO: check if packages already present in directory prompt
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
        os.makedirs(package_dir)
    else:
        os.makedirs(package_dir)

    # TODO: ERROR HANDLING & USE DNF
    print ("Downloading %d Packages For ISO, Please Wait...\n" % (len(plist)))
    process = subprocess.Popen(
        ["yum", "install", "--installroot=", WORK_DIRECTORY, "-x *.i686", "--downloadonly", "--downloaddir=" + str(package_dir)] + plist[1:],
        stdout=subprocess.PIPE)
    process = subprocess.Popen(["yumdownloader", "--installroot=", WORK_DIRECTORY, "-x *.i686", "--resolve",
                                "--destdir=" + str(package_dir)] + plist[1:],
                               stdout=subprocess.PIPE)
    for line in iter(process.stdout.readline, ''):
        sys.stdout.write(line)

    copy_tree(package_dir, dvd_dir + "/Packages")
    if os.path.exists(dvd_dir + "/Packages/RDO"):
        shutil.rmtree(dvd_dir + "/Packages/RDO")
    shutil.copytree("RDO/", dvd_dir + "/Packages/RDO")
    shutil.copy("mkiso.sh", WORK_DIRECTORY)
    # TODO: Fetch Latest Updates.img and place it in <DVD/>images/directory
    print ("Done Downloading Packages\n")

    #  createrepo -g /DVD/comps.xml .
    print ("Creating Custom Repo\n")
    p=subprocess.Popen(["createrepo", "-g", "comps.xml", dvd_dir], cwd=dvd_dir)
    p.wait()
    print ("Creating ISO....")
    #TODO: Get the geniso command to work from here
    subprocess.call(["./mkiso.sh"],cwd=WORK_DIRECTORY)
    # cmd = "-U -r -v -T -J -joliet-long -V \"CentOS 7 x86_64\" -volset \"CentOS 7 x86_64\" -A \"CentOS 7 x86_64\" -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -eltorito-alt-boot -e images/efiboot.img -no-emul-boot -o ../Cent.iso ."
    # subprocess.call("genisoimage " + cmd,cwd=dvd_dir)
    # p = subprocess.Popen(
    #     ["genisoimage", "-U", "-r", "-v", "-T", "-J", "-joliet-long", "-V", "\"CentOS\ 7\ x86_64\"", "-volset",
    #      "\"CentOS\ 7\ x86_64\"", "-A", "\"CentOS\ 7\ x86_64\"", "-b", "isolinux/isolinux.bin", "-c", "isolinux/boot.cat",
    #      "-no-emul-boot", "-boot-load-size", "4", "-boot-info-table", "-eltorito-alt-boot", "-e", "images/efiboot.img",
    #      "-no-emul-boot", "-o", WORK_DIRECTORY + "/" + OUTPUT_FILENAME, "."], cwd=dvd_dir)
    # p.wait()
    # p = subprocess.Popen(["implantisomd5", WORK_DIRECTORY + "/" +OUTPUT_FILENAME])
    # p.wait()
    print ("Completed ISO FILE CAN BE FOUND AT: " + WORK_DIRECTORY + "/" +OUTPUT_FILENAME)
    # Cleanup
    if os.path.exists(dvd_dir):
        shutil.rmtree(dvd_dir)
    os.remove(WORK_DIRECTORY+"/mkiso.sh")
    # TODO: Download Packages via yum API



if __name__ == "__main__":
    main(sys.argv)
