#!/usr/bin/env python

import os
import sys
import shlex
import subprocess

def run_command(cmd, cwd=None):

    if type(cmd) is not list:
        cmd = shlex.split(cmd)

    if not cwd:
         p = subprocess.Popen(cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
    else:
         p = subprocess.Popen(cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd)

    out, err = p.communicate()
    return p.returncode, out, err
