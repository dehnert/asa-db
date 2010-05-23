import traceback
import os, errno

def log_and_ignore_failures(logfile):
    def decorator(f):
        def new_f(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception:
                fd = open(logfile, 'a')
                traceback.print_exc(file=fd, )
                fd.close()
        return new_f
    return decorator

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise
