#!/usr/bin/env python

import epdb
from issues import GithubIssues
from datetime import datetime as DT
import datetime

class TicketRates(object):
    def __init__(self, cli=None):
        self.gh = GithubIssues(cli=cli)
        #self.gh.get_open()
        #self.gh.get_closed()
        self.gh.get_all()
        self.gh._get_types()
        self.gh.get_closure_info()

        self.find_date_ranges()
        self.make_time_series()
        self.count_open_and_closed()
        self.show_csv()

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

            created_date = None
            closed_date = None
            od = None
            cd = None

            created_date = self.gh.datadict[i]['created_at']
            od = DT.strptime(created_date, "%Y-%m-%dT%H:%M:%SZ")
            od_str = od.strftime('%Y-%m-%d')
            if od_str not in self.time_series:
                self.time_series[od_str] = {}
                self.time_series[od_str]['opened'] = 1
            else:
                if 'opened' not in self.time_series[od_str]:
                    self.time_series[od_str]['opened'] = 1
                else:
                    self.time_series[od_str]['opened'] += 1

            if self.gh.datadict[i]['closed_at']:
                closed_date = self.gh.datadict[i]['closed_at']
                cd = DT.strptime(closed_date, "%Y-%m-%dT%H:%M:%SZ")
                cd_str = cd.strftime('%Y-%m-%d')

                if cd_str not in self.time_series:
                    self.time_series[cd_str] = {}
                    self.time_series[cd_str]['closed'] = 1
                else:
                    if 'closed' not in self.time_series[cd_str]:
                        self.time_series[cd_str]['closed'] = 1
                    else:
                        self.time_series[cd_str]['closed'] += 1

        total = 0
        for i in sorted(self.time_series.keys()):
            if 'opened' in self.time_series[i]:
                total += self.time_series[i]['opened']

            if 'closed' in self.time_series[i]:
                total -= self.time_series[i]['closed']

            self.time_series[i]['open'] = total


    def show_csv(self):

        print "date;opened;closed;total_open"

        for k in sorted(self.time_series.keys()):
            if 'opened' in self.time_series[k]:
                opened = self.time_series[k]['opened']
            else:
                opened = 0

            if 'closed' in self.time_series[k]:
                closed = self.time_series[k]['closed']
            else:
                closed = 0

            total = self.time_series[k]['open']

            #print k,";",opened,";",closed
            print "%s;%d;%d;%d" % (k, opened, closed, total)



    '''
    def panda_test(self):
        import pandas as pd
        df = pd.read_csv('/var/www/html/ansible/issue_rate.csv', 
                sep=';', 
                parse_dates=['date'], 
                index_col='date')
    '''






