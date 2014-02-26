#!/usr/bin/env python

import epdb
from github import Github
from issues import GithubIssues
from datetime import datetime as DT
import datetime
from patchtests import PatchTest
from htmlify import HtmlGenerator

class PullRequests(object):
    
    def __init__(self, cli):
        self.cli = cli
        self.gh = GithubIssues(cli=cli)
        self.gh.get_open()
        self.gh._get_types()
        self.gh.get_pull_request_patches()

        #import epdb; epdb.st()

    def check_merge_conflicts(self):
        #import epdb; epdb.st()

        clean = []
        unclean = []

        sorted_keys = sorted(self.gh.datadict.keys())
        #sorted_keys = sorted_keys[:20]
        for k in sorted_keys:    
            #import epdb; epdb.st()
            this_type = self.gh.datadict[k]['type']
            if this_type == 'pull_request':
                #import epdb; epdb.st()
                this_url = "https://github.com/%s" % self.gh.repo
                this_patch = self.gh.datadict[k]['patch_text']
                print "# testing PR merge: %s" % k
                prc = PatchTest(this_url)
                prc.makecheckout()
                res = prc.trypatch(this_patch)
                #import epdb; epdb.st()
                print "# \t%s" % res
                self.gh.datadict[k]['clean_merge'] = res
                if res:
                    clean.append(k)
                else:
                    unclean.append(k)

        HtmlGenerator(self.gh.datadict, unclean, "PRs with merge conflicts")


