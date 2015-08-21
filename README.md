# CentOS ISO Creator: Simple Python Script to create CentOS ISO with Custom Packages

This script creates CentOS 7 ISO with [CentOS Cloud](http://buildlogs.centos.org/centos/7/cloud/openstack-kilo/) Packages.

## Usage Instructions:
1. [Download Repo](https://github.com/asadpiz/centos-respin/archive/master.zip) and Unzip.
2. As root execute: `./respin-centos.py`

This will download the CentOS minimal ISO from a mirror and then add CentOS Cloud Packages to this ISO. Optionally you can specify -f <PATH-TO-ISO> option to skip ISO download.

## Script Options:
respin-centos.py [-h] [-f ISOFILE | -d ISODIRECTORY | -l ISOLINK]
                        [-o OUTPUT] [-p PACKAGELIST]

Creates a Respin of CentOS. By Default fetches CentOS 7 minimal ISO from the
network and adds openstack packages from CentOS Cloud Repo to ISO

optional arguments:
  -h, --help            show this help message and exit
  -f ISOFILE, --isofile ISOFILE
                        CentOS ISO File
  -d ISODIRECTORY, --isodirectory ISODIRECTORY
                        CentOS DVD Directory
  -l ISOLINK, --isolink ISOLINK
                        CentOS ISO Link [DEFAULT] = http://mirror.eu.oneandone
                        .net/linux/distributions/centos/7/isos/x86_64/CentOS-7
                        -x86_64-Minimal-1503-01.iso
  -o OUTPUT, --output OUTPUT
                        Output filename [DEFAULT] =
                        CentOS-7-x86_64-Minimal-1503-01-RDO.iso
  -p PACKAGELIST, --packagelist PACKAGELIST
                        Package List to be Added to ISO [DEFAULT] = https://gi
                        thub.com/asadpiz/org_centos_cloud/blob/master/PackageL
                        ist.md


IRC: asad_ (#centos-devel)

