#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, signal, stat
import pyinotify

uid = None
gid = None
pid = None
wm = None
wdd = None
notifier = None
copy_in_progress = False
exit_app = False
downloadsdirsrc = None

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
    global uid, gid
    uid = os.getuid()
    gid = os.getgid()
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

    signal.signal(signal.SIGCHLD, sighandler)

    chroot = confdic['chroot']
    cmd = confdic['cmdinchroot']
    ret = exec_proc(chroot, cmd)
    ret = True

    if ret and src and dst:
        global downloadsdirsrc
        downloadsdirsrc = src
        print('Start sync src: {} to dst: {}'.format(src, dst))
        sync_dirs(src, dst)

def rm_dir_contents(dirpath):
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
    if wpid == pid and wm:
        # restore signal handler
        signal.signal(signal.SIG_IGN, sighandler)
        wm.rm_watch(wdd.values())
        if copy_in_progress:
            exit_app = True
        else:
            cleanup_and_exit(downloadsdirsrc)

def exec_proc(chroot, cmd):
    global pid
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
    def __init__(self, srcdir, dstdir):
        super(EventHandler, self).__init__()
        self.frm = None
        self.srcdir = srcdir
        self.dstdir = dstdir

    def is_downloaded(self, path, ext='.part'):
        l = len(ext)
        if len(self.frm) < l:
            return False
        if self.frm[-l:] != ext:
            return False
        return self.frm[:-l] == path

    def process_IN_CLOSE_WRITE(self, event):
        st = os.lstat(event.pathname)
        print("Close write: {}, {}".format(event.pathname, st.st_size))
        if not st.st_size:
            return
        _, ext = os.path.splitext(event.pathname)
        print('extension: {}'.format(ext))
        if ext == '.part':
            return
        copy_file(event.pathname, self.dstdir, uid, gid)

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
        if self.is_downloaded(event.pathname):
            print('file downloaded: {}'.format(event.pathname))
        copy_file(event.pathname, self.dstdir, uid, gid)

def copy_file(filepath, dstdir, uid=None, gid=None):
    import shutil
    copy_in_progress = True
    print('copying: {} --> {}'.format(filepath, dstdir))
    shutil.copy(filepath, dstdir)
    if uid and gid:
        os.lchown(os.path.join(dstdir, os.path.basename(filepath)), uid, gid)
    copy_in_progress = False
    if exit_app:
       cleanup_and_exit(self.srcdir)

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

def sync_dirs(src, dst):
    global wm, wdd, notifier
    wm = pyinotify.WatchManager()  # Watch Manager
    mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | \
           pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO | \
           pyinotify.IN_CLOSE_WRITE

    handler = EventHandler(src, dst)
    notifier = pyinotify.Notifier(wm, handler)
    wdd = wm.add_watch(src, mask, rec=True)

    notifier.loop()

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

if __name__ == '__main__':
    main()
