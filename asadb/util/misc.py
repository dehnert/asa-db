import traceback

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
