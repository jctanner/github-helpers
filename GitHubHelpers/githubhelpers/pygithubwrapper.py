#!/usr/bin/env python

import os
import requests

import cPickle as pickle
from github import Github

class PyGithubWrapper(object):

    def __init__(self):
        self.username = None
        self.password = None
        self.cli = None
        self.cachedir = None

    def load_pygithub_objects(self, datadict):

        if self.cli.pargs.username is not None:
            username = self.cli.pargs.username
        else:
            username = self.cli.config.get('github', 'username')
        self.username = username

        if self.cli.pargs.password is not None:
            password = self.cli.pargs.password
        else:
            password = self.cli.config.get('github', 'password')
        self.password = password

        if self.cli.pargs.repo is not None:
            repo_data = self.cli.pargs.repo
        else:
            repo_data = self.cli.config.get('github', 'repo')

        repo_data = repo_data.split('/', 1)
        repo_user = repo_data[0]
        repo_name = repo_data[1]

        g = Github(username, password)
        this_repo = g.get_user(repo_user).get_repo(repo_name)
        self.repo = this_repo

        for k in sorted([int(x) for x in datadict.keys()]):
            k = str(k)
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

    def _wait_for_limiting(self):
        # https://api.github.com/users/whatever
        url = 'https://api.github.com/users/' + self.username
        sleeptime = 0
        while sleeptime:
            i = requests.get(url, auth=(self.username, self.password))
            sleeptime = i.headers.get('X-RateLimit-Reset', None)
            if sleeptime:
                sleeptime = calendar.timegm(time.gmtime()) - int(sleeptime)
                print "# sleeping %s" % sleeptime
                time.sleep(sleeptime)
