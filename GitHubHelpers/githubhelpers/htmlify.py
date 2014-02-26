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

