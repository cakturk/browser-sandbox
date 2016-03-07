#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, signal
import pyinotify

uid = None
gid = None
pid = None

# args;
# 0, path to chroot
# 1, cmd to exec in chroot
# 2, src dir to sync from
# 3, dst dir to sync
def main():
    global uid, gid
    uid = os.getuid()
    gid = os.getgid()
    signal.signal(signal.SIGCHLD, sighandler)

    print("py: uid: {}, euid: {}".format(os.getuid(), os.geteuid()))
    exec_proc('/home/cakturk/dev/containers/debian-tree-firefox',
              'firefox')

def sighandler(signum, frame):
    print 'Signal handler called with signal', signum
    print 'frame', frame
    wpid, st = os.waitpid(-1, os.WNOHANG)
    print 'break loop ', wpid, pid, st
    if wpid == pid:
        print 'wait exit'

def exec_proc(chroot, cmd):
    global pid
    pid = os.fork()
    if pid == 0:
        args = ['systemd-nspawn', '--setenv=DISPLAY=:0', '-D']
        args.extend([chroot, cmd])
        os.execvp(args[0], args)
    else:
        print('child pid: {}'.format(pid))
        sync_dirs('/tmp', '/emtp')

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        print "Creating:", event.pathname

    def process_IN_DELETE(self, event):
        print "Removing:", event.pathname

def sync_dirs(src, dst):
    wm = pyinotify.WatchManager()  # Watch Manager
    mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE  # watched events

    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)
    wdd = wm.add_watch(src, mask, rec=True)

    notifier.loop()


if __name__ == '__main__':
    main()
