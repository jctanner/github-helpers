#!/usr/bin/env python

import os
import shutil
import tempfile
import epdb
#import cPickle as pickle
#from github import Github
from issues import GithubIssues
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

        self.find_date_ranges()
        self.make_time_series()
        self.count_open_and_closed()
        self.count_close_times()


        #self.create_csv()
        #self.plot_csv()

        self.plot_closure_histogram()
        

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


    def count_close_times(self):

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
                 


        for k in self.gh.datadict.keys():

            if self.gh.datadict[k]['closed_at']:
            
                i = self.gh.datadict[k]

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
                  
        self.closure_data = x
        #import epdb; epdb.st()

    def plot_closure_histogram(self):


        csvs = {}

        for k in self.closure_data.keys():

            kx = k + "subset"

            thisdata = self.closure_data[k]
            csvs[k] = '%s;count\n' % k
            csvs[kx] = '%s;count\n' % k

            keys = [ int(x) for x in self.closure_data[k].keys() ]
            keys = sorted(keys)
            subkeys = keys[1:] #get rid of the first day

            for k2 in keys:
                try:
                    this_line = "%d;%d\n" % (int(k2), int(self.closure_data[k][k2]))
                except:
                    this_line = "%d;0\n" % int(k2)
                csvs[k] += this_line

            for k2 in subkeys:
                this_line = "%d;%d\n" % (int(k2), int(self.closure_data[k][k2]))
                csvs[kx] += this_line


            this_file = "/var/www/html/ansible/stats/closures/%s.svg" % k
            print "# plot %s" % this_file
            ph.bar_chart(csvs[k], this_file)

            this_file = "/var/www/html/ansible/stats/closures/%s.svg" % kx
            print "# plot %s" % this_file
            ph.bar_chart(csvs[kx], this_file)

    def plot_csv(self):


        this_file = tempfile.NamedTemporaryFile()
        this_filename = this_file.name
        this_file.close()
        f = open(this_filename, "wb")
        f.write(self.csv)
        f.close()

        print "# loading csv %s" % this_filename
        df = pd.read_csv(this_filename, sep=';', parse_dates=['date'], index_col='date')
        shutil.copyfile(this_filename, 
            "/var/www/html/ansible/stats/open_closure_rates/latest-data.csv")
        this_file.close()
        #import epdb; epdb.st()

        ################################
        #           TOTALS
        ################################

        '''
        print "# making plot"
        ax = df.plot(y=['total_closed','total_opened', 'total_open'], 
                                legend=False, figsize=(30, 20), grid=True)
        opened, closed = ax.get_legend_handles_labels()
        ax.legend(opened, closed, loc='best')
        fig = ax.get_figure()
        fig.tight_layout()
        print "# saving plot to file"
        fig.savefig('/var/www/html/ansible/stats/open_closure_rates/cumulative-totals.png')
        '''


        ################################
        #       PULL vs. ISSUE 
        ################################


        """
        columns = ['issues_opened', 'prs_opened']
        filename = "/var/www/html/ansible/stats/open_closure_rates/pr-vs-issue-graph.png"
        ph.basic_plot_with_columns(self.csv, columns, filename, 
                                kind='bar', stacked=True, yrange=(-30, None))

        columns = ['total_opened', 'total_closed', 'total_open', 
                    'prs_opened', 'prs_closed', 'issues_opened', 'issues_closed']
        filename = "/var/www/html/ansible/stats/open_closure_rates/test-totals.png"
        ph.basic_subplots(self.csv, columns, filename)
        """

        """
        columns = ['total_opened']
        basedir = "/var/www/html/ansible/stats/open_closure_rates"
        filename = basedir + "/total_opened_regresion.png"
        ph.resample(self.csv, columns, filename)
        """

        # resample median for stats
        columns = ['total_opened', 'prs_opened', 'issues_opened']
        basedir = "/var/www/html/ansible/stats/open_closure_rates"
        filename = basedir + "/opened_resampled.png"
        ph.simple_resample(self.csv, columns, filename, offset="A")

        # resample median for stats
        columns = ['total_closed', 'prs_closed', 'issues_closed']
        basedir = "/var/www/html/ansible/stats/open_closure_rates"
        filename = basedir + "/closed_resampled.png"
        ph.simple_resample(self.csv, columns, filename)

        # resample median for stats
        columns = ['total_closed', 'prs_closed', 'issues_closed'
                   'total_opened', 'prs_opened', 'issues_opened']
        basedir = "/var/www/html/ansible/stats/open_closure_rates"
        filename = basedir + "/totals_resampled.png"
        ph.simple_resample(self.csv, columns, filename)

        # resample median for stats
        columns = ['prs_closed', 'prs_closed_by_admin', 'prs_closed_by_user']
        basedir = "/var/www/html/ansible/stats/open_closure_rates"
        filename = basedir + "/pr_closure_admin_vs_user.png"
        ph.simple_resample(self.csv, columns, filename)

        # resample median for stats
        columns = ['issues_closed', 'issues_closed_by_admin', 'issues_closed_by_user']
        basedir = "/var/www/html/ansible/stats/open_closure_rates"
        filename = basedir + "/issue_closure_admin_vs_user.png"
        ph.simple_resample(self.csv, columns, filename)



"""
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
"""













