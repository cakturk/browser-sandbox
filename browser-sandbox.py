#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

uid = None
gid = None

def main():
    print("py: uid: {}, euid: {}".format(os.getuid(), os.geteuid()))
    exec_proc()

def exec_proc(args):
    pid = os.fork()
    if pid == 0:
        pass
    else:
        # child
        pass

if __name__ == '__main__':
    main()
