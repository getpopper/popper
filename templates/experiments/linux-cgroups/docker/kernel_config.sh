#! /usr/bin/env bash
set -xe

# Set config options in kernel

# Manipulate options in a .config file from the command line.
# Usage:
# $myname options command ...
# commands:
#   --enable|-e option   Enable option
#   --disable|-d option  Disable option
#   --module|-m option   Turn option into a module
#   --set-str option string
#                        Set option to "string"
#   --set-val option value
#                        Set option to value
#   --undefine|-u option Undefine option
#   --state|-s option    Print state of option (n,y,m,undef)

#   --enable-after|-E beforeopt option
#                              Enable option directly after other option
#   --disable-after|-D beforeopt option
#                              Disable option directly after other option
#   --module-after|-M beforeopt option
#                              Turn option into module directly after other option

#   commands can be repeated multiple times

# options:
#   --file config-file   .config file to change (default .config)
#   --keep-case|-k       Keep next symbols' case (dont' upper-case it)

# $myname doesn't check the validity of the .config file. This is done at next
# make time.

# By default, $myname will upper-case the given symbol. Use --keep-case to keep
# the case of all following symbols unchanged.

# $myname uses 'CONFIG_' as the default symbol prefix. Set the environment
# variable CONFIG_ to the prefix to use. Eg.: CONFIG_="FOO_" $myname ...

# Debuginfo is only needed if you plan to use binary object tools like crash, kgdb, and SystemTap on the kernel.

scripts/config --disable DEBUG_INFO \
               --disable CONFIG_DEBUG_FS \
               --disable CONFIG_HAVE_DMA_API_DEBUG \
               --disable CONFIG_PM_DEBUG \
               --disable CONFIG_PM_ADVANCED_DEBUG \
               --disable CONFIG_PM_SLEEP_DEBUG \
               --disable CONFIG_NFS_DEBUG \
               --disable CONFIG_CIFS_DEBUG \
               --disable CONFIG_DLM_DEBUG \
               --disable CONFIG_SCHED_DEBUG \
               --disable CONFIG_HAVE_DMA_API_DEBUG \
               --disable CONFIG_ARCH_SUPPORTS_DEBUG_PAGEALLOC \
               --disable CONFIG_DEBUG_RODATA \
               --disable CONFIG_DEBUG_BLK_CGROUP \
               --disable CONFIG_CGROUP_DEBUG \
               --disable CONFIG_GRKERNSEC_AUDIT_GROUP \
               --disable CONFIG_GRKERNSEC_AUDIT_GID \
               --disable CONFIG_GRKERNSEC_EXECLOG \
               --disable CONFIG_GRKERNSEC_RESLOG \
               --disable CONFIG_GRKERNSEC_CHROOT_EXECLOG \
               --disable CONFIG_GRKERNSEC_AUDIT_PTRACE \
               --disable CONFIG_GRKERNSEC_AUDIT_CHDIR \
               --disable CONFIG_GRKERNSEC_AUDIT_MOUNT \
               --disable CONFIG_GRKERNSEC_SIGNAL \
               --disable CONFIG_GRKERNSEC_FORKFAIL \
               --disable CONFIG_GRKERNSEC_TIME \
               --disable CONFIG_GRKERNSEC_PROC_IPADDR \
               --disable CONFIG_GRKERNSEC_RWXMAP_LOG

# Ensure Keys and Signature are unique to this build, see https://lists.debian.org/debian-kernel/2016/04/msg00579.html
scripts/config --disable CONFIG_SYSTEM_TRUSTED_KEYS

# RTL8821AE is a buggy module
scripts/config --disable RTL8821AE


### Virtualisation Helper ###

scripts/config --set-str CONFIG_UEVENT_HELPER_PATH ""
scripts/config --set-str CONFIG_DEFAULT_IOSCHED "noop"
scripts/config --enable CONFIG_UEVENT_HELPER


### Storage Helper ###

scripts/config   --enable CONFIG_SCSI_MQ_DEFAULT \
                 --enable CONFIG_DM_MQ_DEFAULT \
                 --enable CONFIG_DEFAULT_NOOP


if [ "$GRSEC" = "true" ]; then

  ### GRSecurity ###

  scripts/config --set-val CONFIG_TASK_SIZE_MAX_SHIFT 47

  scripts/config --enable CONFIG_PAX_USERCOPY_SLABS \
                 --enable CONFIG_GRKERNSEC \
                 --enable CONFIG_GRKERNSEC_CONFIG_AUTO \
                 --enable CONFIG_GRKERNSEC_CONFIG_SERVER \
                 --enable CONFIG_GRKERNSEC_CONFIG_VIRT_GUEST \
                 --enable CONFIG_GRKERNSEC_CONFIG_VIRT_EPT \
                 --enable CONFIG_GRKERNSEC_CONFIG_VIRT_XEN \
                 --enable CONFIG_GRKERNSEC_CONFIG_PRIORITY_PERF

  #
  # Default Special Groups
  #
  scripts/config --set-val CONFIG_GRKERNSEC_PROC_GID 1001 \
                 --set-val CONFIG_GRKERNSEC_TPE_UNTRUSTED_GID 1005 \
                 --set-val CONFIG_GRKERNSEC_SYMLINKOWN_GID 1006

  #
  # PaX
  #
  scripts/config --enable CONFIG_PAX \
                 --enable CONFIG_PAX_EI_PAX \
                 --enable CONFIG_PAX_PT_PAX_FLAGS \
                 --enable CONFIG_PAX_XATTR_PAX_FLAGS \
                 --enable CONFIG_PAX_HAVE_ACL_FLAGS

  #
  # Non-executable pages
  #
  scripts/config --enable CONFIG_PAX_NOEXEC \
                 --enable CONFIG_PAX_PAGEEXEC \
                 --enable CONFIG_PAX_EMUTRAMP \
                 --enable CONFIG_PAX_MPROTECT

  scripts/config --set-str CONFIG_PAX_KERNEXEC_PLUGIN_METHOD ""

  #
  # Address Space Layout Randomization
  #
  scripts/config --enable CONFIG_PAX_ASLR \
                 --enable CONFIG_PAX_RANDKSTACK \
                 --enable CONFIG_PAX_RANDUSTACK \
                 --enable CONFIG_PAX_RANDMMAP

  #
  # Miscellaneous hardening features
  #
  scripts/config --enable CONFIG_PAX_REFCOUNT \
                 --enable CONFIG_PAX_USERCOPY \
                 --enable CONFIG_PAX_SIZE_OVERFLOW \
                 --enable CONFIG_PAX_LATENT_ENTROPY

  #
  # Memory Protections
  #
  scripts/config --enable CONFIG_GRKERNSEC_KMEM \
                 --enable CONFIG_GRKERNSEC_IO \
                 --enable CONFIG_GRKERNSEC_BPF_HARDEN \
                 --enable CONFIG_GRKERNSEC_PERF_HARDEN \
                 --enable CONFIG_GRKERNSEC_RAND_THREADSTACK \
                 --enable CONFIG_GRKERNSEC_PROC_MEMMAP \
                 --enable CONFIG_GRKERNSEC_KSTACKOVERFLOW \
                 --enable CONFIG_GRKERNSEC_BRUTE \
                 --enable CONFIG_GRKERNSEC_MODHARDEN \
                 --enable CONFIG_GRKERNSEC_HIDESYM \
                 --enable CONFIG_GRKERNSEC_RANDSTRUCT \
                 --enable CONFIG_GRKERNSEC_RANDSTRUCT_PERFORMANCE \
                 --enable CONFIG_GRKERNSEC_KERN_LOCKOUT

  #
  # Role Based Access Control Options
  #
  scripts/config --set-val CONFIG_GRKERNSEC_ACL_MAXTRIES 3 \
                 --set-val CONFIG_GRKERNSEC_ACL_TIMEOUT 30

  #
  # Filesystem Protections
  #
  scripts/config --enable CONFIG_GRKERNSEC_PROC \
                 --enable CONFIG_GRKERNSEC_PROC_USERGROUP \
                 --enable CONFIG_GRKERNSEC_PROC_ADD \
                 --enable CONFIG_GRKERNSEC_LINK \
                 --enable CONFIG_GRKERNSEC_SYMLINKOWN \
                 --enable CONFIG_GRKERNSEC_FIFO \
                 --enable CONFIG_GRKERNSEC_SYSFS_RESTRICT \
                 --enable CONFIG_GRKERNSEC_DEVICE_SIDECHANNEL \
                 --enable CONFIG_GRKERNSEC_CHROOT \
                 --enable CONFIG_GRKERNSEC_CHROOT_MOUNT \
                 --enable CONFIG_GRKERNSEC_CHROOT_DOUBLE \
                 --enable CONFIG_GRKERNSEC_CHROOT_PIVOT \
                 --enable CONFIG_GRKERNSEC_CHROOT_CHDIR \
                 --enable CONFIG_GRKERNSEC_CHROOT_CHMOD \
                 --enable CONFIG_GRKERNSEC_CHROOT_FCHDIR \
                 --enable CONFIG_GRKERNSEC_CHROOT_MKNOD \
                 --enable CONFIG_GRKERNSEC_CHROOT_SHMAT \
                 --enable CONFIG_GRKERNSEC_CHROOT_UNIX \
                 --enable CONFIG_GRKERNSEC_CHROOT_FINDTASK \
                 --enable CONFIG_GRKERNSEC_CHROOT_NICE \
                 --enable CONFIG_GRKERNSEC_CHROOT_SYSCTL \
                 --enable CONFIG_GRKERNSEC_CHROOT_CAPS \
                 --enable CONFIG_GRKERNSEC_CHROOT_INITRD

  #
  # Kernel Auditing
  #
  scripts/config --enable CONFIG_GRKERNSEC_RESLOG \
                 --enable CONFIG_GRKERNSEC_SIGNAL \
                 --enable CONFIG_GRKERNSEC_TIME \
                 --enable CONFIG_GRKERNSEC_PROC_IPADDR \
                 --enable CONFIG_GRKERNSEC_RWXMAP_LOG

  #
  # Executable Protections
  #
  scripts/config --enable CONFIG_GRKERNSEC_DMESG \
                 --enable CONFIG_GRKERNSEC_HARDEN_PTRACE \
                 --enable CONFIG_GRKERNSEC_PTRACE_READEXEC \
                 --enable CONFIG_GRKERNSEC_SETXID \
                 --enable CONFIG_GRKERNSEC_HARDEN_IPC \
                 --enable CONFIG_GRKERNSEC_TPE

  scripts/config --set-val CONFIG_GRKERNSEC_TPE_GID 1005

  #
  # Network Protections
  #
  scripts/config --enable CONFIG_GRKERNSEC_BLACKHOLE \
                 --enable CONFIG_GRKERNSEC_NO_SIMULT_CONNECT

  #
  # Physical Protections
  #
  scripts/config --enable CONFIG_GRKERNSEC_DENYUSB

  #
  # Sysctl Support
  #
  scripts/config --enable CONFIG_GRKERNSEC_SYSCTL \
                 --enable CONFIG_GRKERNSEC_SYSCTL_ON

  #
  # Logging Options
  #
  scripts/config --set-val CONFIG_GRKERNSEC_FLOODTIME 10 \
                 --set-val CONFIG_GRKERNSEC_FLOODBURST 6

  # Modules
  scripts/config --enable  CONFIG_MODULE_SIG \
                 --enable  CONFIG_MODULE_SIG_SHA256 \
                 --enable  CONFIG_MODULES_TREE_LOOKUP \
                 --enable  CONFIG_MODVERSIONS \
                 --set-val CONFIG_MODULE_SIG_HASH "sha256" \
                 --set-val CONFIG_MODULE_SIG_KEY ""

fi
