#!/usr/bin/python
import sys
import os, errno
from subprocess import Popen, PIPE
import tempfile
import re
import traceback

wkhtml_safe_pattern = re.compile(r'^[] !#-[^-~]+$')
wkhtml_args = ['--margin-bottom', '0mm', '--margin-top', '0mm', '--margin-left', '0mm', '--margin-right', '0mm', ]

def is_safe_for_wkhtml(url):
    print "Checking %s" % (url, )
    return wkhtml_safe_pattern.match(url)

def convert_pdf_to_jpg(pdf, dest, ):
    # pdftoppm < $pdf | pnmcrop | pnmscale  0.75 | pnmtojpeg --optimize > $dest
    pdffile = open(pdf, 'r', )
    try:
        os.unlink(dest)
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            pass
        else: raise
    jpgfile = open(dest, 'w', )
    p1 = Popen(['pdftoppm'],                    stdin=pdffile,   stdout=PIPE, )
    p2 = Popen(['pnmcrop'],                     stdin=p1.stdout, stdout=PIPE, )
    p3 = Popen(['pnmscale', '0.75', ],          stdin=p2.stdout, stdout=PIPE, )
    p4 = Popen(['pnmtojpeg', '--optimize', ],   stdin=p3.stdout, stdout=jpgfile, )
    p4.wait()
    print "Theoretically, wrote JPG to '%s'" % (dest, )

def generate_webpage_previews(websites):
    """
    Generate previews of websites.

    Takes one argument --- a list of (source url, destination image
    location) pairs.

    Returns a list of (url, errmsg, ) pairs indicating failed conversions.
    """

    preview_requests = []
    jpg_convert_requests = []
    tmpfiles = []
    failures = []
    for url, dest in websites:
        if is_safe_for_wkhtml(url):
            tmpfile = tempfile.NamedTemporaryFile(delete=False)
            assert(is_safe_for_wkhtml(tmpfile.name))
            preview_requests.append('"%s" "%s"' % (url, tmpfile.name,))
            jpg_convert_requests.append((url, tmpfile.name, dest,))
            tmpfiles.append(tmpfile.name)
            tmpfile.close()
        else:
            failures.append((url, "URL '%s' not safe for wkhtml" % (url, ), ))
    wkhtml = Popen(['util/wkhtmltopdf', '--read-args-from-stdin', ] + wkhtml_args, stdin=PIPE, )
    wkhtml.communicate("\n".join(preview_requests))

    for url, pdf, dest in jpg_convert_requests:
        try:
            convert_pdf_to_jpg(pdf, dest)
        except Exception, e:
            raise
            failures.append((
                url,
                "URL '%s' not JPGized:\n%s" % (url, traceback.format_exc()),
            ))

    return failures

def generate_webpage_preview(url, dest):
    failures = generate_webpage_previews([(url, dest), ])
    if failures:
        return failures[0][1]
    else:
        return None

if __name__ == '__main__':
    print "In main"
    test_pairs = [
        ("http://ua.mit.edu/", "/tmp/uamitedu.jpg", ),
        ("http://scripts.mit.edu/", "/tmp/scripts.jpg", ),
    ]
    generate_webpage_previews(test_pairs)
