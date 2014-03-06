#!/usr/bin/env python

import os
import cPickle as pickle
from github import Github

class PyGithubWrapper(object):

    def __init__(self):
        self.cli = None
        self.cachedir = None

    def load_pygithub_objects(self, datadict):

        # FIXME -- refactor to a new class

        username = self.cli.config.get('github', 'username')
        password = self.cli.config.get('github', 'password')
        repo_data = self.cli.config.get('github', 'repo')
        repo_data = repo_data.split('/', 1)
        repo_user = repo_data[0]
        repo_name = repo_data[1]

        g = Github(username, password)
        this_repo = g.get_user(repo_user).get_repo(repo_name)
        self.repo = this_repo

        for k in sorted(datadict.keys()):
            # set cache file path
            this_issue = None
            this_cache = os.path.join(self.cachedir, "%s.pygithub" % k)

            # does it exist? load it ... FIXME: what if it is out of date?
            if os.path.isfile(this_cache):
                print "# loading pygithub obj for %s" % k
                this_issue = pickle.load(open(this_cache, "rb"))
                #import epdb; epdb.st()
                if this_issue.state != datadict[k]['state']:
                    this_issue = this_repo.get_issue(int(k))
                    pickle.dump(this_issue, open(this_cache, "wb"))
            else:
                print "# retriving pygithub obj for %s" % k
                this_issue = this_repo.get_issue(int(k))
                pickle.dump(this_issue, open(this_cache, "wb"))
            #import epdb; epdb.st()

            # set the obj in the datadict
            datadict[k]['pygithub'] = this_issue

        return datadict