#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, signal, stat
import pyinotify

pid = None
watch_info = None

class WatchInfo(object):
    def __init__(self, watchdirs, handler, mask):
        super(WatchInfo, self).__init__()
        self.watchdirs = watchdirs
        self.wm = pyinotify.WatchManager()  # Watch Manager
        self.notifier = pyinotify.Notifier(self.wm, handler)
        self.wdd = self.wm.add_watch(watchdirs, mask, rec=True, auto_add=True)

    def exit(self):
        self.wm.rm_watch(self.wdd.values())
        raise KeyboardInterrupt();

    def start_watch(self):
        self.notifier.loop()

def die(msg):
    sys.stderr.write(msg + '\n')
    sys.exit(127)

def get_sync_dir(confdic, sectname):
    if not sectname in confdic:
        return None
    path = confdic[sectname]
    if not os.path.exists(path):
        return None
    return path

# args;
# 0, path to chroot
# 1, cmd to exec in chroot
# 2, src dir to sync from
# 3, dst dir to sync
def main():
    global watch_info, pid
    realuid = os.getuid()
    realgid = os.getgid()
    print("py: uid: {}, euid: {}".format(os.getuid(), os.geteuid()))

    try:
        confdic = get_configuration()
        ('chroot' in confdic and confdic['chroot'] \
                and os.path.exists(confdic['chroot'])) \
                or die('Could not find chroot path')
        src = get_sync_dir(confdic, 'syncsrcdir')
        if src:
            dst = get_sync_dir(confdic, 'syncdstdir')
    except Exception as e:
        die('Could not find a valid configuration file: sandbox.ini')

    x11_adjust_access(True)

    chroot = confdic['chroot']
    cmd = confdic['cmdinchroot']
    ret = exec_proc(chroot, cmd)
    if ret:
        pid = ret
        signal.signal(signal.SIGCHLD, sighandler)


    if pid and src and dst:
        print('Start sync src: {} to dst: {}'.format(src, dst))
        mask = pyinotify.IN_MOVED_TO | \
               pyinotify.IN_CLOSE_WRITE
        ev_handler = EventHandler(src, dst, realuid, realgid)
        watch_info = WatchInfo([src], ev_handler, mask)
        watch_info.start_watch()

        x11_adjust_access(False)
        cleanup_and_exit(src)

def rm_dir_contents(dirpath):
    import shutil
    for f in os.listdir(dirpath):
        file_path = os.path.join(dirpath, f)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception, e:
            print e

def cleanup_and_exit(downloadsdir):
    rm_dir_contents(downloadsdir)
    sys.exit(0)

def sighandler(signum, frame):
    wpid, st = os.waitpid(-1, os.WNOHANG)
    if wpid == pid and watch_info:
        # restore signal handler
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        watch_info.exit()

def exec_proc(chroot, cmd):
    pid = os.fork()
    if pid == 0:
        sys.stdin = open('/dev/null', 'rb')
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = open('/dev/null', 'w')
        args = ['systemd-nspawn', '--setenv=DISPLAY=:0', '-D']
        args.extend([chroot, cmd])
        os.execvp(args[0], args)
    return pid

class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, srcdir, dstdir, uid, gid):
        super(EventHandler, self).__init__()
        self.frm = None
        self.srcdir = srcdir
        self.dstdir = dstdir
        self.uid = uid
        self.gid = gid

    def process_IN_CLOSE_WRITE(self, event):
        st = os.lstat(event.pathname)
        print("Close write: {}, {}".format(event.pathname, st.st_size))
        if not st.st_size:
            return
        _, ext = os.path.splitext(event.pathname)
        print('extension: {}'.format(ext))
        if ext == '.part':
            return
        copy_file(self.srcdir, event.pathname,
                  self.dstdir, self.uid, self.gid)

    def process_IN_CREATE(self, event):
        print "Creating:", event.pathname
        st = os.lstat(event.pathname)
        if stat.S_ISLNK(st.st_mode):
            return
        if stat.S_ISDIR(st.st_mode):
            pass

    def process_IN_DELETE(self, event):
        print "Removing:", event.pathname

    def process_IN_MOVED_FROM(self, event):
        print "Moved from:", event.pathname
        self.frm = event.pathname

    def process_IN_MOVED_TO(self, event):
        print "Moved to:", event.pathname
        copy_file(self.srcdir, event.pathname,
                  self.dstdir, self.uid, self.gid)

def make_up_filename(dstpath):
    import errno
    max_try_count = 1024
    root, ext = os.path.splitext(dstpath)
    i = 0

    while True:
        if not os.path.exists(dstpath):
            return dstpath
        i += 1
        if i > max_try_count:
            raise OSError(errno.EEXIST, 'File already exists: ' + dstpath)
        dstpath = '{0}({1}){2}'.format(root, i, ext)

def copy_file(basedir, filepath, dstdir, uid=None, gid=None):
    import shutil
    subdir = os.path.relpath(os.path.dirname(filepath), basedir)
    if subdir is not '.':
        dstdir = os.path.join(dstdir, subdir)
        mkdir_p(dstdir)

    dstfilepath = os.path.join(dstdir, os.path.basename(filepath))
    if os.path.exists(dstfilepath):
        dstfilepath = make_up_filename(dstfilepath)
        shutil.copyfile(filepath, dstfilepath)
    else:
        shutil.copy(filepath, dstdir)
    print('copying: {} --> {}'.format(filepath, dstdir))
    if uid and gid:
        os.lchown(dstdir, uid, gid)
        os.lchown(dstfilepath, uid, gid)

def mkdir_p(path):
    import errno
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def app_dir_path():
    return os.path.dirname(os.path.realpath(__file__))

def parse_config_sect(configfile, section='default'):
    from ConfigParser import SafeConfigParser
    parser = SafeConfigParser()
    parser.read(os.path.join(app_dir_path(), configfile))

    dic = {}
    for opt in parser.options(section):
        dic[opt] = parser.get(section, opt)

    return dic

def get_configuration():
    savedexc = None
    appdirconf = os.path.join(app_dir_path(), 'sandbox.ini')
    for f in ['/etc/browser-sandbox/sandbox.ini', appdirconf]:
        try:
            return parse_config_sect(f, 'default')
        except Exception as e:
            savedexc = e

    raise savedexc

def x11_adjust_access(enable):
    import subprocess
    sign = '+' if enable else '-'
    subprocess.check_call(['xhost', sign])

if __name__ == '__main__':
    main()
