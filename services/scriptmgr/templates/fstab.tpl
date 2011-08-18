proc            /mnt/vm0/rootfs/proc         proc    nodev,noexec,nosuid 0 0
devpts          /mnt/vm0/rootfs/dev/pts      devpts defaults 0 0
sysfs           /mnt/vm0/rootfs/sys          sysfs defaults  0 0
/home/scriptrunner/startup /mnt/vm0/rootfs/home/startup bind defaults,bind 0 0
/home/scriptrunner/code/<%= name %> /mnt/vm0/rootfs/tmp bind defaults,bind 0 0
/home/scriptrunner/code/<%= name %> /mnt/vm0/rootfs/home/scriptrunner bind defaults,bind 0 0
