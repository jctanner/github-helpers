#!/usr/bin/env python

import os
import shutil
import tempfile
import epdb
#import cPickle as pickle
#from github import Github
from issues3 import GithubIssues
from datetime import datetime as DT
import datetime
from prtests import PRTest
from htmlify import HtmlGenerator
import csv


#from pandashelpers import *
import pandashelpers as ph
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
        self.gh.get_all()

        if self.cli.pargs.outputdir is not None:
            self.outputdir = self.cli.pargs.outputdir
            if not self.outputdir.endswith('/'):
                self.outputdir += '/'
        else:
            self.outputdir = os.path.join('/tmp/', self.gh.repo)

        if not os.path.isdir(self.outputdir):
            os.makedirs(self.outputdir)

        start, end = self.find_date_ranges()
        timeseries = self.make_time_series(start, end)
        open_closure_series = self.count_open_and_closed(timeseries)

        # cumulative totals
        open_closure_csv = self.timeseries_to_csv(open_closure_series)
        self.plot_totals_csv(open_closure_csv, 
            self.outputdir + "/stats/open_closure_rates/cumulative-totals.png")

        # counts per day
        closuredata = self.count_close_times(self.gh.datadict)
        self.plot_closure_histogram(closuredata)

        # everything else
        self.plot_csv(open_closure_csv)
        

    def find_date_ranges(self):
        sorted_keys = sorted([int(x) for x in self.gh.datadict.keys()])
        sorted_keys = [str(x) for x in sorted_keys]
        first_key = sorted_keys[0]
        last_key = sorted_keys[-1]
        start_date = self.gh.datadict[first_key]['created_at']                
        end_date = self.gh.datadict[last_key]['created_at']                
        return (start_date, end_date)

    def make_time_series(self, start, end):

        """ Make a time series for all days """

        ts = DT.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
        te = DT.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
        step = datetime.timedelta(days=1)

        result = []

        while ts < te:
            result.append(ts.strftime('%Y-%m-%d'))
            ts += step
        
        return result

    def count_open_and_closed(self, timeseries):

        this_series = {}
        for t in timeseries:
            this_series[t] = time_dict.copy()

        for i in self.gh.datadict.keys():
            created_date = self.gh.datadict[i]['created_at']
            od = DT.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ")
            od_str = od.strftime('%Y-%m-%d')
            if od_str not in timeseries:
                this_series[od_str] = time_dict.copy()

            if 'closed_at' in self.gh.datadict[i] :
                if self.gh.datadict[i]['closed_at']:
                    closed_date = self.gh.datadict[i]['closed_at']
                    cd = DT.strptime(closed_date, "%Y-%m-%dT%H:%M:%SZ")
                    cd_str = cd.strftime('%Y-%m-%d')
                    if cd_str not in this_series:
                        this_series[cd_str] = time_dict.copy()

        for i in self.gh.datadict.keys():

            created_date = None
            closed_date = None
            od = None
            cd = None

            ## OPEN
            created_date = self.gh.datadict[i]['created_at']
            od = DT.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ")
            od_str = od.strftime('%Y-%m-%d')
            this_series[od_str]['total_opened'] += 1

            if self.gh.datadict[i]['type'] == 'issue':
                this_series[od_str]['issues_opened'] += 1
            if self.gh.datadict[i]['type'] == 'pull_request':
                this_series[od_str]['prs_opened'] += 1

            ## CLOSED
            if self.gh.datadict[i]['closed_at']:
                closed_date = self.gh.datadict[i]['closed_at']
                cd = DT.strptime(closed_date, "%Y-%m-%dT%H:%M:%SZ")
                cd_str = cd.strftime('%Y-%m-%d')
                this_series[cd_str]['total_closed'] += 1

                if self.gh.datadict[i]['user_closed']:
                    this_series[cd_str]['closed_by_user'] += 1
                else:
                    this_series[cd_str]['closed_by_admin'] += 1

                #if self.time_series[cd_str]['closed_by_admin'] > 100:
                #    import epdb; epdb.st()

                if self.gh.datadict[i]['type'] == 'issue':
                    this_series[od_str]['issues_closed'] += 1
                    if self.gh.datadict[i]['user_closed']:
                        this_series[cd_str]['issues_closed_by_user'] += 1
                    else:
                        this_series[cd_str]['issues_closed_by_admin'] += 1
                if self.gh.datadict[i]['type'] == 'pull_request':
                    this_series[od_str]['prs_closed'] += 1
                    if self.gh.datadict[i]['user_closed']:
                        this_series[cd_str]['prs_closed_by_user'] += 1
                    else:
                        this_series[cd_str]['prs_closed_by_admin'] += 1

        total = 0
        for i in sorted(this_series.keys()):
            total += this_series[i]['total_opened']
            total -= this_series[i]['total_closed']

            this_series[i]['total_open'] = total
        return this_series

    def timeseries_to_csv(self, time_series):
        
        all_keys = []
        for k in sorted(time_series.keys()):
            for l in time_series[k].keys():
                if l not in all_keys:
                    all_keys.append(l)                

        all_keys = sorted(all_keys)
        csv = "date;" + ';'.join(all_keys) + "\n"

        for k in sorted(time_series.keys()):
            this_string = "%s" % k
            for l in sorted(all_keys):
                this_string += ";%d" % time_series[k][l] 
            csv += this_string + "\n"
        return csv

    def count_close_times(self, datadict):

        x = { 'time_close': {},
              'time_close_pr': {},
              'time_close_issue': {},
              'time_user_close': {},
              'time_admin_close': {},
              'time_user_close_pr': {},
              'time_user_close_issue': {},
              'time_admin_close_pr': {},
              'time_admin_close_issue': {},
              'time_merge_pr': {},
              'time_reject_pr': {}
            }
                 


        for k in datadict.keys():

            if datadict[k]['closed_at']:
            
                i = datadict[k]

                if i['age'] not in x['time_close']:
                    x['time_close'][i['age']] = 1
                else:
                    x['time_close'][i['age']] += 1


                if i['user_closed']:
                    if i['age'] not in x['time_user_close']:
                        x['time_user_close'][i['age']] = 1
                    else:
                        x['time_user_close'][i['age']] += 1
                else:
                    if i['age'] not in x['time_admin_close']:
                        x['time_admin_close'][i['age']] = 1
                    else:
                        x['time_admin_close'][i['age']] += 1


                if i['type'] == 'pull_request':
                    #import epdb; epdb.st()
                    if i['age'] not in x['time_close_pr']:
                        x['time_close_pr'][i['age']] = 1
                    else:    
                        x['time_close_pr'][i['age']] += 1

                    if i['user_closed']:
                        if i['age'] not in x['time_user_close_pr']:
                            x['time_user_close_pr'][i['age']] = 1
                        else:
                            x['time_user_close_pr'][i['age']] += 1
                    else:
                        #import epdb; epdb.st()
                        if i['age'] not in x['time_admin_close_pr']:
                           x['time_admin_close_pr'][i['age']] = 1
                        else:
                           x['time_admin_close_pr'][i['age']] += 1

                        if 'merged' in [y['event'] for y in i['events']]:
                            if i['age'] not in x['time_merge_pr']:
                                 x['time_merge_pr'][i['age']] = 1
                            else:
                                 x['time_merge_pr'][i['age']] += 1

                        else:
                            if i['age'] not in x['time_reject_pr']:
                                x['time_reject_pr'][i['age']] = 1
                            else:
                                x['time_reject_pr'][i['age']] += 1
                            

                if i['type'] == 'issue':
                    if i['age'] not in x['time_close_issue']:
                        x['time_close_issue'][i['age']] = 1
                    else:    
                        x['time_close_issue'][i['age']] += 1

                    if i['user_closed']:
                        if i['age'] not in x['time_user_close_issue']:
                            x['time_user_close_issue'][i['age']] = 1
                        else:
                            x['time_user_close_issue'][i['age']] += 1
                    else:
                         if i['age'] not in x['time_admin_close_issue']:
                            x['time_admin_close_issue'][i['age']] = 1
                         else:
                            x['time_admin_close_issue'][i['age']] += 1
                  
        return x

    def plot_closure_histogram(self, closure_data):


        csvs = {}

        for k in sorted(closure_data.keys()):
            k = str(k)
            kx = k + "subset"

            thisdata = closure_data[k]
            csvs[k] = '%s;count\n' % k
            csvs[kx] = '%s;count\n' % k

            keys = [ int(x) for x in closure_data[k].keys() ]
            keys = sorted(keys)
            subkeys = keys[1:] #get rid of the first day

            for k2 in keys:
                #k2 = str(k2)
                try:
                    this_line = "%d;%d\n" % (int(k2), int(closure_data[k][k2]))
                except:
                    import epdb; epdb.st()
                    this_line = "%d;0\n" % int(k2)
                csvs[k] += this_line

            for k2 in subkeys:
                #k2 = str(k2)
                this_line = "%d;%d\n" % (int(k2), int(closure_data[k][k2]))
                csvs[kx] += this_line

            #if k == 'time_admin_close':
            #    import epdb; epdb.st()

            #import epdb; epdb.st()
            this_file = "/var/www/html/ansible/stats/closures/%s.svg" % k
            print "# plot %s" % this_file
            ph.bar_chart(csvs[k], this_file)

            this_file = "/var/www/html/ansible/stats/closures/%s.svg" % kx
            print "# plot %s" % this_file
            ph.bar_chart(csvs[kx], this_file)

    def plot_totals_csv(self, csv, filename):

        this_dir = os.path.dirname(filename):
        if not os.path.isdir(this_dir):
            os.makedirs(this_dir)

        this_file = tempfile.NamedTemporaryFile()
        this_filename = this_file.name
        this_file.close()
        f = open(this_filename, "wb")
        f.write(csv)
        f.close()

        print "# loading csv %s" % this_filename
        df = pd.read_csv(this_filename, sep=';', parse_dates=['date'], index_col='date')
        shutil.copyfile(this_filename, filename)
        this_file.close()

        ################################
        #           TOTALS
        ################################

        print "# making cumulative totals plot"
        ax = df.plot(y=['total_closed','total_opened', 'total_open'], 
                                legend=False, figsize=(30, 20), grid=True)
        opened, closed = ax.get_legend_handles_labels()
        ax.legend(opened, closed, loc='best')
        fig = ax.get_figure()
        fig.tight_layout()
        print "# saving cumulative totals plot to file"
        fig.savefig('/var/www/html/ansible/stats/open_closure_rates/cumulative-totals.png')

    def plot_csv(self, csv):

        this_file = tempfile.NamedTemporaryFile()
        this_filename = this_file.name
        this_file.close()

        f = open(this_filename, "wb")
        f.write(csv)
        f.close()

        print "# loading csv %s" % this_filename

        if not os.path.isdir(self.outputdir + "stats/open_closure_rates"):
            os.makedirs(self.outputdir + "stats/open_closure_rates")

        df = pd.read_csv(this_filename, sep=';', parse_dates=['date'], index_col='date')
        shutil.copyfile(this_filename, 
            self.outputdir + "stats/open_closure_rates/latest-data.csv")
        this_file.close()


        ################################
        #       PULL vs. ISSUE 
        ################################

        columns = ['issues_opened', 'prs_opened']
        filename = self.outputdir + "stats/open_closure_rates/pr-vs-issue-graph.png"
        ph.basic_plot_with_columns(csv, columns, filename, 
                                kind='bar', stacked=True, yrange=(-30, None))

        columns = ['total_opened', 'total_closed', 'total_open', 
                    'prs_opened', 'prs_closed', 'issues_opened', 'issues_closed']
        filename = self.outputdir + "stats/open_closure_rates/test-totals.png"
        ph.basic_subplots(csv, columns, filename)

        columns = ['total_opened']
        basedir = self.outputdir + "stats/open_closure_rates"
        filename = basedir + "/total_opened_regresion.png"
        ph.simple_resample(csv, columns, filename)

        # resample median for stats
        columns = ['total_opened', 'prs_opened', 'issues_opened']
        basedir = self.outputdir + "stats/open_closure_rates"
        filename = basedir + "/opened_resampled.png"
        ph.simple_resample(csv, columns, filename, offset="A")

        # resample median for stats
        columns = ['total_closed', 'prs_closed', 'issues_closed']
        basedir = self.outputdir + "stats/open_closure_rates"
        filename = basedir + "/closed_resampled.png"
        ph.simple_resample(csv, columns, filename)

        # resample median for stats
        columns = ['total_closed', 'prs_closed', 'issues_closed'
                   'total_opened', 'prs_opened', 'issues_opened']
        basedir = self.outputdir + "stats/open_closure_rates"
        filename = basedir + "/totals_resampled.png"
        ph.simple_resample(csv, columns, filename)

        # resample median for stats
        columns = ['prs_closed', 'prs_closed_by_admin', 'prs_closed_by_user']
        basedir = self.outputdir + "stats/open_closure_rates"
        filename = basedir + "/pr_closure_admin_vs_user.png"
        ph.simple_resample(csv, columns, filename)

        # resample median for stats
        columns = ['issues_closed', 'issues_closed_by_admin', 'issues_closed_by_user']
        basedir = self.outputdir + "stats/open_closure_rates"
        filename = basedir + "/issue_closure_admin_vs_user.png"
        ph.simple_resample(csv, columns, filename)


class CommentReport(object):
    def __init__(self, cli=None):
        self.cli = cli
        self.gh = GithubIssues(cli=cli)
        self.gh.get_all()

        self.list_comments()

    def list_comments(self):
        for k in sorted(self.gh.datadict.keys()):
            i = self.gh.datadict[k]
            if not 'comments' in i:
                continue

            if i['type'] == "issue":
                #import epdb; epdb.st()
                pass

            for com in i['comments']:
                body = com['body']
                commenter = com['user']['login']
                if commenter == 'mpdehaan':
                    #import epdb; epdb.st()
                    print body
                    open("/tmp/mpdehaan.comments", "a").write("# %s\n" % k)
                    open("/tmp/mpdehaan.comments", "a").write("%s\n" % body.encode('utf-8'))

            #if i['closed_by'] == 'mpdehann':
            if i['type'] == "pull_request" and i['merged']:
                # must have been kosher... why?
                #import epdb; epdb.st()
                open("/tmp/admin.pr.approved", "a").write("# %s\n" % k)
                open("/tmp/admin.pr.approved", "a").write("TITLE: %s\n" % i['title'].encode('utf-8'))
                if 'closure_comment_texts' in i and len(i['closure_comment_texts']) > 0:
                    open("/tmp/admin.pr.approved", "a").write("REASON: %s\n" % i['closure_comment_texts'][-1].encode('utf-8'))
                else:                    
                    open("/tmp/admin.pr.approved", "a").write("REASON: None\n")
            elif i['type'] == "pull_request":
                # why was it rejected?
                open("/tmp/admin.pr.rejected", "a").write("# %s\n" % k)
                open("/tmp/admin.pr.rejected", "a").write("TITLE: %s\n" % i['title'].encode('utf-8'))
                if 'closure_comment_texts' in i and len(i['closure_comment_texts']) > 0:
                    #import epdb; epdb.st()
                    open("/tmp/admin.pr.rejected", "a").write("REASON: %s\n" % i['closure_comment_texts'][-1].encode('utf-8'))
                else:                    
                    open("/tmp/admin.pr.rejected", "a").write("REASON: None\n")

            if i['type'] == 'issue' and i['state'] == 'closed' and not i['user_closed']:
                # fixed issues usually have an event with a commit_id key
                commit_ids = [ x for x in i['events'] if x['commit_id'] ]
                if len(commit_ids) > 0:
                    # assume fixed
                    open("/tmp/bugs.txt", "a").write("# %s ; fixed\n" % k)
                    open("/tmp/bugs.txt", "a").write("TITLE: %s\n" % i['title'].encode('utf-8'))
                    if 'closure_comment_texts' in i and len(i['closure_comment_texts']) > 0:
                        open("/tmp/bugs.txt", "a").write("REASON: %s\n" % i['closure_comment_texts'][-1].encode('utf-8'))
                    else:
                        open("/tmp/bugs.txt", "a").write("REASON: None\n")
                else:
                    # assume rejected    
                    #import epdb; epdb.st()
                    open("/tmp/bugs.txt", "a").write("# %s ; rejected\n" % k)
                    open("/tmp/bugs.txt", "a").write("TITLE: %s\n" % i['title'].encode('utf-8'))
                    if 'closure_comment_texts' in i and len(i['closure_comment_texts']) > 0:
                        open("/tmp/bugs.txt", "a").write("REASON: %s\n" % i['closure_comment_texts'][-1].encode('utf-8'))
                    else:
                        open("/tmp/bugs.txt", "a").write("REASON: None\n")
                






