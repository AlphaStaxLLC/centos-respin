# CentOS-OpenStack Remix ISO Creator

Simple Python Script To Create a CentOS 7 Remix ISO with [OpenStack-Liberty](http://buildlogs.centos.org/centos/7/cloud/openstack-liberty/) Packages. The ISO also has an [addon](https://github.com/AlphaStaxLLC/org_centos_cloud) which allows users to specify the mode of installation of PackStack.

## Usage Instructions:
1. [Download respin-centos.py](https://github.com/AlphaStaxLLC/centos-respin/) and as root execute `./asx-respin-centos.py`.

This will download the CentOS minimal ISO from a mirror and then add CentOS Cloud Packages to this ISO. Optionally you can specify "-f [PATH-TO-ISO]" option to skip ISO download.

## System Requirements:
* Operating System: CentOS 7 x86_64 with Internet connectivity

## Script Options:
```bash
usage: respin-centos.py [-h] [-f ISOFILE | -d ISODIRECTORY | -l ISOLINK]
                        [-p PACKAGELIST]

Creates a Respin of CentOS. By Default fetches CentOS 7 Everything ISO from the
network and adds openstack packages from CentOS Cloud Repo to ISO

optional arguments:
  -h, --help            show this help message and exit
  -f ISOFILE, --isofile ISOFILE
                        ISO File
  -d ISODIRECTORY, --isodirectory ISODIRECTORY
                        DVD Directory
  -l ISOLINK, --isolink ISOLINK
                        ISO http Link [DEFAULT] = http://mirror.eu.oneandone.net/linux/distributions/centos/7/isos/x86_64/CentOS-7-x86_64-Minimal-1503-01.iso
  
-p PACKAGELIST, --packagelist PACKAGELIST
                        Package List (only arch x86_64) to be Added to ISO,
                        Make sure the packages you want to download have a
                        corresponding repo in /etc/yum.repos.d/ [DEFAULT] = ht
                        tps://github.com/asadpiz/org_centos_cloud/blob/master/
                        PackageList.md
  -o OUTPUT, --output OUTPUT
                        Output Filename [DEFAULT] =
                        CentOS-7-x86_64-RDO-1503.iso

```
## Future Work:

Modify this script to be a general CentOS Custom ISO Creator i.e., generating CentOS ISO with user provided package list/addons.
IRC: asad_ (#centos-devel)

