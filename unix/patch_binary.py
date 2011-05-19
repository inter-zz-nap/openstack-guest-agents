#!/usr/bin/env python

import os
import subprocess
import sys


def execute(*args):
    p = subprocess.Popen(args)
    status = os.waitpid(p.pid, 0)[1]

    if status:
        raise Exception(
                "failed to execute %s: status %d" % ' '.join(args), status)


def patch_binary(binary, libdir, interpreter=None):
    if interpreter:
        execute('patchelf', '--set-interpreter',
                os.path.join(libdir, interpreter), binary)
    execute('patchelf', '--set-rpath', libdir, binary)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "Usage: patch_binary.py <binary_name> <dest_dir> <lib_dir>"
        sys.exit(1)

    binary = sys.argv[1]
    destdir = sys.argv[2]
    libdir = sys.argv[3]

    interpreter = filter(lambda f: f.startswith('ld-'),
            os.listdir(destdir + libdir))
    if interpreter:
        interpreter = interpreter[0]

    patch_binary(binary, libdir, interpreter)
