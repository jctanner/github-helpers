#!/usr/bin/env python

import os
import sys
import requests
import json
from pprint import pprint
import yaml
import epdb
import operator
import shlex
from datetime import *
from pprint import pprint
import time

SAMPLE = """
Version: ( The output from ansible --version )
Environment: ( RHEL 5/6, Centos 5/6, Ubuntu 12.04/13.07, *BSD, Solaris ) 
Issue Type: ( Bug, Feature Idea, Feature Pull Request, Bugfix Pull Request )

Description: 

    ( vars are not loaded in roles marked as dependencies )

Steps To Reproduce:

    (* install ansible)
    (* create playbook)
    (* run ansible-playbook)
    (* check file contents)

Example Playbook:
    ````
    hosts: all
    tasks:
       - raw: uname -a
    ```
"""

WARNING = """Please rewrite the issue description based on our issue template ...\n%s""" % SAMPLE


class Triage(object):
    def __init__(self, cli=None, issues=None):

        self.cli = cli #cement cli object
        self.issues = issues

        # get all api data
        self.issues.get_open()
        self.issues._get_types()
        self.issues._get_ages()
        self.issues._get_usernames()
        self.issues.get_events()
        self.issues.get_comments()

        # run triage
        self.main()

    def main(self):        
        self.issues.get_open()
        self.issues._get_types()
        self.issues._get_ages()
        self.issues._get_usernames()
        self.issues.get_events()
        self.issues.get_comments()

        issues = self.issues.datadict
        sorted_keys = sorted(issues.keys())
        reversed(sorted_keys)

        for k in sorted_keys:
            i = issues[k]
            itype = i['type'] # pull_request / issue
            labels = [ x['name'] for x in i['labels'] ]
            title = i['title']
            body = i['body']
            comments = i['comments']

            #import epdb; epdb.st()
            print k,i.keys()
            print "age: %s" % i['age']

            if not self.template_check(body):
                print "ISSUE %s DOES NOT HAVE TEMPLATE!!!" % k
                if not self.warning_check(comments):
                    print "ISSUE %s DOES NOT HAVE A WARNING!!!" % k
                    self.add_template_warning(k)
                elif i['age'] > 7:
                    print "ISSUE %s IS BEING CLOSED!!!" % k
                    self.close_ticket(k)
            else:
                if self.warning_check(comments):
                    print "REMOVE WARNING FROM ISSUE %s!!!" % k
                    self.remove_template_warning(k, comments)
                    
            

    def template_check(self, text):
        #print SAMPLE
        skeys = SAMPLE.split("\n")
        skeys = [ x for x in skeys if x and not x.startswith(" ") ]
        skeys = [ x.split(":")[0] for x in skeys ]

        dkeys = text.split("\n")
        dkeys = [ x for x in dkeys if x and not x.startswith(" ") ]
        dkeys = [ x.split(":")[0] for x in dkeys ]

        #import epdb; epdb.st()

        result = True
        for k in skeys:
            if k not in dkeys:
                result = False
        return result           

    def warning_check(self, comments):
        #import epdb; epdb.st()
        result = False
        for com in comments:
            #import epdb; epdb.st()
            if com['body'] == WARNING:
                result = True
        return result

    def add_template_warning(self, issue):
        #pass        
        result = self.issues.add_comment(issue, WARNING)
        if not result:
            print 'Failed to add warning to issue: %s' % issue

    def remove_template_warning(self, issue, comments):
        for com in comments:
            if com['body'] == WARNING:
                #import epdb; epdb.st()
                i = self.issues.delete_comment(com['id'])
                if not i:
                    print "Failed to remove warning from issue: %s" % issue

    def close_ticket(self, issue):
        pass










