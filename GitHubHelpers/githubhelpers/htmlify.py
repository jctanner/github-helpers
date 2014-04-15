#!/usr/bin/env python

def HtmlGenerator(datadict, keys, title, outfile=None):

    if outfile:
        f = open(outfile, "rb")

    header = "<html>\n"
    header += "<head>\n"
    header += "<title>%s</title>\n" % title
    header += """<style>
    #outer {
        margin: 0 ;
        background-color:white; /*just to display the example*/
    }

    #inner {
        /*or move the whole container 50px to the right side*/
        margin-left:50px;
        margin-right:-50px;
    }
</style>\n"""
    header += "</head>"
    header += "<body>"

    if not outfile:
        print header
    else:
        f.write(header)

    for k in sorted(keys):
        #print '<div id="outer">\n<div id="outer">%s : %s</div>\n' % (k, k)
        thisurl = datadict[k]['html_url']
        thisid = '<a href="%s">%s</a>' %(thisurl, k)
        line = None
        try:
            line = '<div id="outer">%s : %s</div>\n' % (thisid, datadict[k]['title'])
        except UnicodeEncodeError:
            line ='<div id="outer">%s : %s</div>\n' % (thisid, "UNICODE")

        if not outfile:
            print line
            print '</div>\n'
        else:
            f.write(line)
            f.write('</div>\n')


    if not outfile:
        print "</body>"
        print "</html>"
    else:
        f.write("</body>\n")
        f.write("</html>\n")
        f.close()


def SortableTable(datadict, title):
    # http://www.kryogenix.org/code/browser/sorttable/
    pass


def PR_files_to_html(datadict, files, outfile=None):

    if outfile:
        f = open(outfile, "wb")

    header = "<html>\n"
    header += "<head>\n"
    header += "<title>PRs for files</title>\n"
    header += """<style>
    #outer {
        margin: 0 ;
        background-color:white; /*just to display the example*/
    }

    #inner {
        /*or move the whole container 50px to the right side*/
        margin-left:50px;
        margin-right:-50px;
    }
</style>\n"""
    header += "</head>\n"
    header += "<body>\n"

    if not outfile:
        print header
    else:
        f.write(header)

    for k in sorted(files, key=lambda k: len(files[k]), reverse=True):
        if not outfile:
            print '<div id="outer">\n<div id="outer">%s : %s</div>\n' % (len(files[k]), k)
        else:
            f.write('<div id="outer">\n<div id="outer">%s : %s</div>\n' % (len(files[k]), k))
        for x in sorted(files[k]):
            #import epdb; epdb.st()
            thisurl = datadict[x]['html_url']
            thisid = '<a href="%s">%s</a>' %(thisurl, x)
            try:
                line = '<div id="inner">%s : %s</div>\n' % (thisid, datadict[x]['title'])
            except UnicodeEncodeError:
                line = '<div id="inner">%s : %s</div>\n' % (thisid, "UNICODE")
            if not outfile:
                print line
            else:
                f.write(line)
        if not outfile:
            print '</div>\n'
        else:
            f.write('</div>\n')


    if not outfile:
        print "</body>"
        print "</html>"
    else:
        f.write("</body>\n")
        f.write("</html>\n")
