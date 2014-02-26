#!/usr/bin/env python

from processhelper import run_command

def runAnsiblePlaybook(playbook, inventory=None, argsfile=None, checkout=None, version=None):
    pass

    basecmd = "ansible-playbook"

    # inventory string requires -i "content"
    # inventory isfile requires -i <file>
    # argsfile requires -e "@<file>"
    # checkout requires source hacking/env-setup
    # verison requires checkout <version>

    rc, so, se = run_command(basecmd)
