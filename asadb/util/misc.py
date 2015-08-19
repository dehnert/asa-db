import logging
import os, errno


def log_and_ignore_failures(logger_name):
    def decorator(f):
        def new_f(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception:
                logger = logging.getLogger(logger_name)
                logger.exception('error in log_and_ignore_failures; ignoring')
        return new_f
    return decorator

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise
