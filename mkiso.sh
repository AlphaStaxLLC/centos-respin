#!/bin/bash

genisoimage -U -r -v -T -J -joliet-long -V "CentOS 7 x86_64" -volset "CentOS 7 x86_64" -A "CentOS 7 x86_64" -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -eltorito-alt-boot -e images/efiboot.img -no-emul-boot -o CentOS-7-x86_64-Minimal-1503-01-RDO.iso DVD/

implantisomd5 CentOS-7-x86_64-Minimal-1503-01-RDO.iso

