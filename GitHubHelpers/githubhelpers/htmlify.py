#!/usr/bin/env python

def HtmlGenerator(datadict, keys, title):
    print "<html>"
    print "<head>"
    print "<title>%s</title>" % title
    print """<style>
    #outer {
        margin: 0 ;
        background-color:white; /*just to display the example*/
    }

    #inner {
        /*or move the whole container 50px to the right side*/
        margin-left:50px;
        margin-right:-50px;
    }
</style>"""
    print "</head>"
    print "<body>"

    for k in sorted(keys):
        #print '<div id="outer">\n<div id="outer">%s : %s</div>\n' % (k, k)
        thisurl = datadict[k]['html_url']
        thisid = '<a href="%s">%s</a>' %(thisurl, k)
        try:
            print '<div id="outer">%s : %s</div>\n' % (thisid, datadict[k]['title'])
        except UnicodeEncodeError:
            print '<div id="outer">%s : %s</div>\n' % (thisid, "UNICODE")
        print '</div>\n'


    print "</body>"
    print "</html>"


def SortableTable(datadict, title):
    # http://www.kryogenix.org/code/browser/sorttable/
    pass


def PR_file_age_to_html(datadict, files):
    print "<html>"
    print "<head>"
    print "<title>PRs for files</title>"
    print """<style>
    #outer {
        margin: 0 ;
        background-color:white; /*just to display the example*/
    }

    #inner {
        /*or move the whole container 50px to the right side*/
        margin-left:50px;
        margin-right:-50px;
    }
</style>"""
    print "</head>"
    print "<body>"

    for k in sorted(files, key=lambda k: len(files[k]), reverse=True):
        print '<div id="outer">\n<div id="outer">%s : %s</div>\n' % (len(files[k]), k)
        for x in sorted(files[k]):
            #import epdb; epdb.st()
            thisurl = datadict[x]['html_url']
            thisid = '<a href="%s">%s</a>' %(thisurl, x)
            try:
                print '<div id="inner">%s : %s</div>\n' % (thisid, datadict[x]['title'])
            except UnicodeEncodeError:
                print '<div id="inner">%s : %s</div>\n' % (thisid, "UNICODE")
        print '</div>\n'


    print "</body>"
    print "</html>"
