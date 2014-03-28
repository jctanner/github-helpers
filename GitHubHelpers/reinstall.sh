#!/bin/bash

git pull --rebase

SITEDIR=$(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")

rm -rf $SITEDIR/githubhelpers
rm -f $SITEDIR/GitHubHelpers-*.egg-info

REPORTS=$(which runreports)
rm -rf $REPORTS
ISSUES=$(which issues)
rm -rf $ISSUES
TRIAGE=$(which triage)
rm -rf $TRIAGE

python setup.py install
