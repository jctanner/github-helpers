#!/usr/bin/env python

import os
import shutil
import tempfile
import epdb
import cPickle as pickle
from github import Github
from issues import GithubIssues
from datetime import datetime as DT
import datetime
from prtests import PRTest
from htmlify import HtmlGenerator

import pandas as pd
import matplotlib.pyplot as plt

time_dict = { 'total_opened': 0,
              'total_closed': 0,
              'total_open': 0,
              'closed_by_user': 0,
              'closed_by_admin': 0,
              'prs_opened': 0,
              'prs_closed': 0,
              'prs_closed_by_user': 0,
              'prs_closed_by_admin': 0,
              'issues_opened': 0,
              'issues_closed': 0,
              'issues_closed_by_user': 0,
              'issues_closed_by_admin': 0
            }

class TicketRates(object):
    def __init__(self, cli=None):
        self.cli = cli
        self.gh = GithubIssues(cli=cli)
        #self.gh.get_open()
        #self.gh.get_closed()
        self.gh.get_all()
        self.gh._get_types()
        self.gh.get_closure_info()

        self.find_date_ranges()
        self.make_time_series()
        self.load_pygithub_objects()
        self.closed_by()
        self.count_open_and_closed()
        self.create_csv()
        self.plot_csv()

        #self.closed_by()

    def find_date_ranges(self):
        sorted_keys = sorted(self.gh.datadict.keys())
        first_key = sorted_keys[0]
        last_key = sorted_keys[-1]
        self.start_date = self.gh.datadict[first_key]['created_at']                
        self.end_date = self.gh.datadict[last_key]['created_at']                

    def make_time_series(self):

        """ Make a time series for all days """

        ts = DT.strptime(self.start_date, "%Y-%m-%dT%H:%M:%SZ")
        te = DT.strptime(self.end_date, "%Y-%m-%dT%H:%M:%SZ")
        step = datetime.timedelta(days=1)

        result = []

        while ts < te:
            result.append(ts.strftime('%Y-%m-%d'))
            ts += step

        self.dates = result
        self.time_series = {}

    def count_open_and_closed(self):

        for i in self.gh.datadict.keys():
            created_date = self.gh.datadict[i]['created_at']
            od = DT.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ")
            od_str = od.strftime('%Y-%m-%d')
            if od_str not in self.time_series:
                self.time_series[od_str] = time_dict.copy()

            if 'closed_at' in self.gh.datadict[i] :
                if self.gh.datadict[i]['closed_at']:
                    closed_date = self.gh.datadict[i]['closed_at']
                    cd = DT.strptime(closed_date, "%Y-%m-%dT%H:%M:%SZ")
                    cd_str = cd.strftime('%Y-%m-%d')
                    if cd_str not in self.time_series:
                        self.time_series[cd_str] = time_dict.copy()

        for i in self.gh.datadict.keys():

            created_date = None
            closed_date = None
            od = None
            cd = None

            ## OPEN
            created_date = self.gh.datadict[i]['created_at']
            od = DT.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ")
            od_str = od.strftime('%Y-%m-%d')
            self.time_series[od_str]['total_opened'] += 1

            if self.gh.datadict[i]['type'] == 'issue':
                self.time_series[od_str]['issues_opened'] += 1
            if self.gh.datadict[i]['type'] == 'pull_request':
                self.time_series[od_str]['prs_opened'] += 1

            ## CLOSED
            if self.gh.datadict[i]['closed_at']:
                closed_date = self.gh.datadict[i]['closed_at']
                cd = DT.strptime(closed_date, "%Y-%m-%dT%H:%M:%SZ")
                cd_str = cd.strftime('%Y-%m-%d')
                self.time_series[cd_str]['total_closed'] += 1

                if self.gh.datadict[i]['user_closed']:
                    self.time_series[cd_str]['closed_by_user'] += 1
                else:
                    self.time_series[cd_str]['closed_by_admin'] += 1

                #if self.time_series[cd_str]['closed_by_admin'] > 100:
                #    import epdb; epdb.st()

                if self.gh.datadict[i]['type'] == 'issue':
                    self.time_series[od_str]['issues_closed'] += 1
                    if self.gh.datadict[i]['user_closed']:
                        self.time_series[cd_str]['issues_closed_by_user'] += 1
                    else:
                        self.time_series[cd_str]['issues_closed_by_admin'] += 1
                if self.gh.datadict[i]['type'] == 'pull_request':
                    self.time_series[od_str]['prs_closed'] += 1
                    if self.gh.datadict[i]['user_closed']:
                        self.time_series[cd_str]['prs_closed_by_user'] += 1
                    else:
                        self.time_series[cd_str]['prs_closed_by_admin'] += 1

        total = 0
        for i in sorted(self.time_series.keys()):
            total += self.time_series[i]['total_opened']
            total -= self.time_series[i]['total_closed']

            self.time_series[i]['total_open'] = total

    def create_csv(self):
        
        all_keys = []
        for k in self.time_series.keys():
            for l in self.time_series[k].keys():
                if l not in all_keys:
                    all_keys.append(l)                

        all_keys = sorted(all_keys)
        self.csv = "date;" + ';'.join(all_keys) + "\n"

        for k in sorted(self.time_series.keys()):
            this_string = "%s" % k
            for l in sorted(all_keys):
                this_string += ";%d" % self.time_series[k][l] 
            self.csv += this_string + "\n"

    def load_pygithub_objects(self):

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

        for k in sorted(self.gh.datadict.keys()):
            # set cache file path
            this_issue = None               
            this_cache = os.path.join(self.gh.cachedir, "%s.pygithub" % k)

            # does it exist? load it ... FIXME: what if it is out of date?
            if os.path.isfile(this_cache):
                print "# loading pygithub obj for %s" % k
                this_issue = pickle.load(open(this_cache, "rb"))
                #import epdb; epdb.st()
                if this_issue.state != self.gh.datadict[k]['state']:
                    this_issue = this_repo.get_issue(int(k))
                    pickle.dump(this_issue, open(this_cache, "wb"))
            else:
                print "# retriving pygithub obj for %s" % k
                this_issue = this_repo.get_issue(int(k))                
                pickle.dump(this_issue, open(this_cache, "wb"))
            #import epdb; epdb.st()

            # set the obj in the datadict
            self.gh.datadict[k]['pygithub'] = this_issue


    def closed_by(self):

        # FIXME: refactor to issues.py

        # this_repo.get_issue(1).user.login
        # this_repo.get_issue(1).closed_by.login

        # self.repo.organization.get_members()

        for k in sorted(self.gh.datadict.keys()):
            this_issue = self.gh.datadict[k]['pygithub']
            this_creator = this_issue.user.login
            try:
                this_closer = this_issue.closed_by.login
            except:
                this_closer = None
            self.gh.datadict[k]['creator'] = this_creator
            self.gh.datadict[k]['closer'] = this_closer

            #import epdb; epdb.st()
            if this_creator == this_closer:
                self.gh.datadict[k]['user_closed'] = True
            else:
                self.gh.datadict[k]['user_closed'] = False

            #import epdb; epdb.st()


    """
    def panda_test(self):
        import pandas as pd
        df = pd.read_csv('/var/www/html/ansible/issue_rate.csv', 
                sep=';', 
                parse_dates=['date'], 
                index_col='date')
    """

    def plot_csv(self):

        # known to work with pandas 0.10.0

        this_file = tempfile.NamedTemporaryFile()
        this_filename = this_file.name
        this_file.write(self.csv)

        print "# loading csv %s" % this_filename
        df = pd.read_csv(this_filename, sep=';', parse_dates=['date'], index_col='date')
        shutil.copyfile(this_filename, 
            "/var/www/html/ansible/stats/open_closure_rates/latest-data.csv")
        this_file.close()
        #import epdb; epdb.st()

        ################################
        #           TOTALS
        ################################
        print "# making plot"
        ax = df.plot(y=['total_closed','total_opened', 'total_open'], 
                                legend=False, figsize=(30, 20), grid=True)
        opened, closed = ax.get_legend_handles_labels()
        ax.legend(opened, closed, loc='best')
        fig = ax.get_figure()
        fig.tight_layout()
        print "# saving plot to file"
        fig.savefig('/var/www/html/ansible/stats/open_closure_rates/cumulative-totals.png')


        ################################
        #       PULL vs. ISSUE 
        ################################
        print "# making plot"
        nf = pd.DataFrame()
        columns = ['issues_opened', 'issues_closed', 'prs_opened', 'prs_closed']

        nf = nf + df.issues_opened
        nf = nf + df.issues_closed
        nf = nf + df.prs_opened
        nf = nf + df.prs_closed

        #ax = df.plot(y=columns, legend=False, figsize=(30, 20), grid=True)
        #bx = df[-90:].plot(y=*columns, kind='bar', stacked=False, 
        #                legend=False, figsize=(30, 20))
        bx = nf[-90:].plot(kind='bar', stacked=False, legend=False, 
                          figsize=(30, 20))
        import epdb; epdb.st()
        #opened, closed = bx.get_legend_handles_labels()
        
        #issues_opened, issues_closed, prs_opened, prs_closed = bx.get_legend_handles_labels()
        #bx.legend(issues_opened, issues_closed, prs_opened, prs_closed, loc='best')
        bx.legend(loc='best')
        fig2 = bx.get_figure()
        fig2.tight_layout()
        print "# saving plot to file"
        fig2.savefig('/var/www/html/ansible/stats/open_closure_rates/pr-vs-issue-graph.png')


