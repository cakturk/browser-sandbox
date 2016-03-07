#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

uid = None
gid = None

# args;
# 0, path to chroot
# 1, cmd to exec in chroot
# 2, src dir to sync from
# 3, dst dir to sync
def main():
    print("py: uid: {}, euid: {}".format(os.getuid(), os.geteuid()))
    exec_proc('/home/cakturk/dev/containers/debian-tree-firefox',
              'firefox')

def exec_proc(chroot, cmd):
    pid = os.fork()
    if pid == 0:
        args = ['systemd-nspawn', '--setenv=DISPLAY=:0', '-D']
        args.extend([chroot, cmd])
        os.execvp(args[0], args)
    else:
        print os.waitpid(-1, 0)

if __name__ == '__main__':
    main()
