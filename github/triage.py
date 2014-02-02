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
import requests



WARNING = """Thanks for filing a ticket! I am the friendly GitHub Ansibot. I see you did not fill out your issue description based on our new issue template. Please copy the contents of this [template](%s) and **paste it into the description** of your ticket. 

Our system will automatically close tickets that do not have an issue template filled out within 7 days. Please note that due to large interest in Ansible, humans may not comment on your ticket if you ask them questions. Don't worry, you're still in the queue and the robots are looking after you."""

RELOCATE = """It appears that you put the issue template in as a comment. Please use the issue template in the -description-, not a comment"""

CLOSEMSG = """Hi, I am the friendly GitHub Ansibot. We've noticed that you did not fill out the issue form for this ticket. We are going to assume this ticket is no longer important to you, and will be closing it. Feel free to open a new ticket with the proper issue template if you would re-raise this issue at a later time. We should also point out to anyone reading this bug report that comments on closed tickets are not likely to be read by the project team, so please raise questions to one of the mailing lists. You can see more information about ways to communicate on %s. Thank you!"""

DEADMSG = """Hi, I am the friendly GitHub Ansibot. This is a closed ticket so this is just a friendly heads up that if you have a question about this, comments on closed tickets are unlikely to be read.  If you would like to discuss this further, please ask questions on one of the mailing lists, or raise a new issue if you believe you are seeing a similar but different problem.  You can see more information about ways to communicate on <link to contributing.md>.  Thank you!"""

class Triage(object):
    def __init__(self, cli=None, issues=None):

        self.cli = cli #cement cli object
        self.template_url = self.cli.config.get_section_dict('triage')['template']
        self.botname = self.cli.config.get_section_dict('triage')['botname']
        self.cutoff = int(self.cli.config.get_section_dict('triage')['cutoff'])
        self.WARNING = WARNING % self.template_url
        self.CLOSEMSG = CLOSEMSG % "https://github.com/ansible/ansible/blob/devel/CONTRIBUTING.md"
        self.DEADMSG = DEADMSG
        self.RELOCATE = RELOCATE
        self.header = "#####"
        self.template_headers = []
        self.required_headers = ['ansible version', 'issue type', 'summary']
        self.issues = issues

    def cleanjenkins(self, username=None, comment=None):

        """ Remove a comment of a username """

        assert username is not None
        assert comment is not None

        self.issues.get_open()
        self.issues._get_ages()
        self.issues._get_usernames()
        self.issues.get_comments()

        issues = self.issues.datadict
        sorted_keys = sorted(issues.keys())
        reversed(sorted_keys)

        to_remove = []

        for k in sorted_keys:
            i = issues[k]
            #itype = i['type'] # pull_request / issue
            labels = [ x['name'] for x in i['labels'] ]
            title = i['title']
            body = i['body']
            comments = i['comments']

            for comm in comments:
                if comm['user']['login'] == username:
                    thisid = comm['url'].split("/")[-1]
                    thisbody = comm['body']
                    to_remove.append((thisid, thisbody))

        for x in to_remove:
            print x
        print "Ok to remove the comments listed above? (YES/no)"
        answer = raw_input()
        if answer != "YES":
            sys.exit(1)
        elif answer == "YES":
            for x in to_remove:
                i, b = x
                r = self.issues.delete_comment(i)
                if not r:
                    print "Failed to remove comment %s" % i


    #############################################################
    #                       TRIAGE CODE                         #      
    #############################################################

    def triage(self):        

        while True:
            print "#=====================================================#"
            print "#                    NEW RUN LOOP                     #"
            print "#=====================================================#"
            self._triage()
            print "#---------------------- SLEEP ------------------------#"
            time.sleep(10)  # Delay for 1 minute (60 seconds)        

    def _triage(self):
        self.fetch_template()


        # get all api data
        #self.issues.get_open()
        self.issues.get_new()
        self.issues._get_types()
        self.issues._get_ages()
        self.issues._get_usernames()
        #self.issues.get_events()
        self.issues.get_comments(usecache=False)
        self.issues.get_pull_request_patches()
        self.issues.get_pull_request_commits()

        issues = self.issues.datadict
        sorted_keys = sorted(issues.keys())
        reversed(sorted_keys)

        # limit processesing to newer issues
        if self.cutoff > -1:
            sorted_keys = [ x for x in sorted_keys if issues[x]['age'] < self.cutoff ]

        for k in sorted_keys:
            #import epdb; epdb.st()
            i = issues[k]

            print "#+++++++++++++++++++++++++++++++++++++++#"
            print "#",k,"--",i['title']

            # no labels
            if not 'labels' in i:
                pass
                #continue

            self.handle_missing_template(k)

            if len(i['labels']) < 1:
                # is PR?
                if i['type'] == "pull_request":
                    self.triage_pull_request(k)
                    continue

                if i['type'] == 'issue':
                    pass

    def triage_bug_report(self, k):
        pass

    def triage_feature_request(self, k):
        pass

    def triage_pull_request(self, k):

        # pr: cloud
        # pr: core code
        # pr: new module
        # pr: enhanced module
        # pr: bugfix
        # pr: docfix

        # pr: merge commits
        # pr: merge conflicts
        # pr: stray conflicts

        pass

    def triage_unknown(self, k):

        """ This is a last resort that shouldn't happen
            if the users fill out the template """

        i = self.issues.datadict[k]
        itype = i['type'] # pull_request / issue
        labels = [ x['name'] for x in i['labels'] ]
        title = i['title']
        body = i['body']
        comments = i['comments']

        if body is None:
            import epdb; epdb.st()

    def handle_missing_template(self, k):

        """ Business logic for deciding what to do
            when an issue description does not have 
            the required templated data """

        i = self.issues.datadict[k]
        title = i['title']
        body = i['body']
        comments = i['comments']
        user = i['user']
        #import epdb; epdb.st()

        actions = []

        if not self.template_check(body):

            missing = self.template_check(body, return_missing_headers=True)
            template_id = None   # which comment ID the template is in
            template_text = None # the filled out template string

            # MAKE SURE USER DIDN'T PUT TEMPLATE IN COMMENT
            #if self.template_in_comments(comments):
            if self.template_in_comments(k):
                print "\t* found template in a comment"
                #template_id, template_text = self.template_in_comments(comments, return_data=True)
                template_id, template_text = self.template_in_comments(k, return_data=True)
                actions.append("relocate")
                actions.append("unwarn")
            else:
                #actions.append("unrelocate")
                pass

            # ADD WARNING OR CLOSE           
            #import epdb; epdb.st()
            if not self.warning_check(comments) and "relocate" not in actions:
                print "\t* will get a warning" 
                actions.append("warn")
            elif i['age'] > 7:
                print "\t* will be closed (%s days old)" % i['age']
                actions.append("close")
            elif self.warning_check(comments):
                print "\t* previously warned"
        else:
            if self.warning_check(comments):
                print "\t* warning will be removed" 
                actions.append("unwarn")

        print "\tactions: %s" % actions

        answer = "n"
        if len(actions) > 0:
            print "Apply these actions? (Y/n)",
            answer = raw_input()

        if answer == "Y":

            for a in actions:
                if a == "warn":
                    self.add_template_warning(k)
                if a == "unwarn":
                    self.remove_template_warning(k, comments)
                if a == "relocate":
                    self.relocate_template(k, template_id, template_text)                
                if a == "close":
                    self.close_ticket(k)
                    
    def template_check(self, text, return_missing_headers=False):

        missing = []
        try:
            dkeys = text.split("\n")
        except AttributeError:
            import epdb; epdb.st()

        # make a dict with keys for lines that start with '###'
        dkeys = [ x.replace(self.header, '') for x in dkeys if x.startswith(self.header) ]
        dkeys = [ x.split(":")[0].strip().lower() for x in dkeys ]

        result = True
        #for k in self.template_headers:
        for k in self.required_headers:
            if k not in dkeys:
                missing.append(k)
                result = False
        #import epdb; epdb.st()                
        if not return_missing_headers:
            return result           
        else:
            return missing

    def template_in_comments(self, k, return_data=False):
        found = False
        commid = None
        content = None
        comments = self.issues.datadict[k]['comments']
        user = self.issues.datadict[k]['user']

        # find template in any comments from issue owner
        for comm in comments:
            #import epdb; epdb.st()
            if comm['user'] == user and self.template_check(comm['body']):
                found = True
                commid = comm['id']
                content = comm['body']
        if return_data == False:                
            return found
        else:
            return (commid, content)

    def warning_check(self, comments):
        #import epdb; epdb.st()
        result = False
        for com in comments:
            #import epdb; epdb.st()
            #print com['body']
            if com['body'] == self.WARNING:
                result = True
        return result

    def add_template_warning(self, issue):
        #pass        
        result = self.issues.add_comment(issue, self.WARNING)
        if not result:
            print 'Failed to add warning to issue: %s' % issue

    def relocate_template(self, k, template_id, template_text):
        #self.relocate_template(k, template_id, template_text)

        # edit description, set the body to template_text
        i = self.issues.set_description(k, template_text)
        if not i:
            print "Failed to set issue description: %s" % issue
        else:
            # remove old comment
            i = self.issues.delete_comment(template_id)
            if not i:
                print "Failed to delete template comment in %s" % issue

    def remove_template_warning(self, issue, comments):
        for com in comments:
            if com['body'] == self.WARNING:
                #import epdb; epdb.st()
                i = self.issues.delete_comment(com['id'])
                if not i:
                    print "Failed to remove warning from issue: %s" % issue

    def remove_relocate_warning(self, issue, comments):
        for com in comments:
            if com['body'] == self.RELOCATE:
                #import epdb; epdb.st()
                i = self.issues.delete_comment(com['id'])
                if not i:
                    print "Failed to remove relocate comment from issue: %s" % issue

    def close_ticket(self, issue):
        pass

    def fetch_template(self):

        """ Fetch the template and transcribe it to keys """
            
        i = requests.get(self.template_url)
        if not i.ok:
            if len(self.template_headers) == 0:
                print "fetching template failed: %s" % i.reason
                return
            else:
                assert i.ok, "Unable to fetch template from %s, %s" % (self.template_url, i.reason)

        for line in i.text.split("\n"):
            if line.startswith(self.header):
                thisheader = line.replace(self.header, "")
                thisheader = thisheader.split(':')[0]
                thisheader = thisheader.strip().lower()                
                self.template_headers.append(thisheader)
        assert len(self.template_headers) is not 0, "No headers were found in %s" % self.template_url                
        #import epdb; epdb.st()



