#!/usr/bin/env python

import os
import shutil
import tempfile
import epdb
import pandas as pd
import matplotlib.pyplot as plt


def filter_csv(csv_data, columns, separator=';'):

    """ Split apart a block of csv text and delete unwanted columns """

    try:
        rows = csv_data.split('\n')    
    except ValueError:
        import epdb; epdb.st()
            
    rows = [ x.split(separator) for x in rows if x != '' ]
    #import epdb; epdb.st()

    while True:    
        remove_col = None

        headers = rows[0]          
        for idx, elem in enumerate(headers):
            if elem not in columns:
                remove_col = idx
        if remove_col:
            # delete the column
            for idx, valx in enumerate(rows):
                del rows[idx][remove_col]
        else:
            # exit the loop
            break        

    #import epdb; epdb.st()
    rows = [ ';'.join(x) for x in rows ]
    rows = '\n'.join(rows)
    return rows

def plot_csv(csv_data):

    # known to work with pandas 0.10.0

    this_file = tempfile.NamedTemporaryFile()
    this_filename = this_file.name
    #this_file.write(self.csv)
    this_file.close()
    f = open(this_filename, "wb")
    f.write(self.csv)
    f.close()
    #import epdb; epdb.st()

    print "# loading csv %s" % this_filename
    df = pd.read_csv(this_filename, sep=';', parse_dates=['date'], index_col='date')
    #import epdb; epdb.st()
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



def basic_plot_with_columns(csv_data, columns, filename, kind='bar', stacked=False, yrange=None):
    print "# making plot"
    new_csv = filter_csv(csv_data, columns)
    new_tmp = tempfile.NamedTemporaryFile()
    new_tmp_name = new_tmp.name
    new_tmp.close()
    f = open(new_tmp_name, "wb")
    f.write(new_csv)
    f.close()
    nf = pd.read_csv(new_tmp.name, sep=';', parse_dates=['date'], index_col='date')

    print "%s" % nf.head()
    print "%s" % nf.tail()

    if not yrange:
        bx = nf.plot(kind=kind, stacked=True, figsize=(30, 20))
    elif type(yrange) == tuple:
        y0, y1 = yrange
        if y1:
            bx = nf[y0:y1].plot(kind=kind, stacked=True, figsize=(30, 20))
        else:
            bx = nf[y0:].plot(kind=kind, stacked=True, figsize=(30, 20))
    else:
        # failsafe
        f.plot(kind='bar', stacked=True, figsize=(30, 20))

    print "# saving plot to file"
    new_fig = bx.get_figure()
    new_fig.tight_layout()
    new_fig.savefig(filename)

def basic_subplots(csv_data, columns, filename, yrange=None):
    print "# making plot"
    new_csv = filter_csv(csv_data, columns)
    new_tmp = tempfile.NamedTemporaryFile()
    new_tmp_name = new_tmp.name
    new_tmp.close()
    f = open(new_tmp_name, "wb")
    f.write(new_csv)
    f.close()
    nf = pd.read_csv(new_tmp.name, sep=';', parse_dates=['date'], index_col='date')

    print "%s" % nf.head()
    print "%s" % nf.tail()

    #bx = nf.plot(subplots=True, figsize=(30, 20))
    #import epdb; epdb.st()

    # figsize width,height

    for idx, bx in enumerate(nf.plot(subplots=True, fontsize=4, figsize=(13, 20))):
        print "# saving plot to file"
        new_fig = bx.get_figure()
        new_fig.tight_layout()
        #new_fig.xlabel(fontsize=4)
        #new_fig.ylabel(fontsize=4)
        this_file = filename.replace('.png', '-%s.png' % idx)
        new_fig.savefig(this_file)

         


