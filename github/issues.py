#!/usr/bin/python

import os
import sys
import requests
import json
from pprint import pprint
import yaml
import epdb
import operator
import shlex
from datetime import *
from pprint import pprint
import time

# caching magic
#import requests_cache
#requests_cache.install_cache('/tmp/github_cache')

# ISSUES
"""
* id
* number
* comments
* html_url
* labels
* title
* updated_at
* closed_at
* state
* pull_request
"""

"""
pagedata = get_all_pages(baseurl + "/issues?state=open")
pagedict = data_to_dict(pagedata)
show_data(pagedict)
pagedict = get_pull_request_patches(pagedict)
show_pr_sorted(pagedict)
show_pr_sorted(pagedict, sort_by="patch_has_tests")
"""

class GithubIssues(object):
    def __init__(self, cli=None, baseurl="https://api.github.com/repos"):

        self.cli = cli #cement cli object
        self.datadict = {}
        self.baseurl = baseurl
        self.fetched = []
        self.repo_admins = ['mpdehaan', 'jctanner', 'jimi-c']

        #import epdb; epdb.st()
        if self.cli.pargs.repo is not None:
            self.repo = self.cli.pargs.repo
        else:
            self.repo = self.cli.config.get('github', 'repo')

        if self.cli.pargs.username is not None:
            self.username = self.cli.pargs.username
        else:
            self.username = self.cli.config.get('github', 'username')

        if self.cli.pargs.password is not None:
            self.password = self.cli.pargs.password
        else:
            self.password = self.cli.config.get('github', 'password')

        self.openedurl = baseurl + "/" + self.repo + "/issues?state=open"
        self.closedurl = baseurl + "/" + self.repo + "/issues?state=closed"

        self.homedir = os.path.expanduser("~")
        self.cachedir = os.path.join(self.homedir, ".cache", "github")
        self.cachefile = os.path.join(self.cachedir, "requests_cache")
        if not os.path.isdir(self.cachedir):
            os.makedirs(self.cachedir)

        #import epdb; epdb.st()
        # requests caching magic
        #import requests_cache
        if not self.cli.pargs.no_cache:
            import requests_cache
            if os.path.isfile(self.cachefile + ".sqlite"):
                st = os.stat(self.cachefile + ".sqlite")
                age = time.time() - st.st_mtime
                print "# CACHE-AGE: ",age
                if age > 30000:
                    os.remove(self.cachefile + ".sqlite")
            requests_cache.install_cache(self.cachefile)
        else:
            #if os.path.isfile(self.cachefile):
            #    os.remove(self.cachefile)
            #requests_cache.install_cache(self.cachefile)
            pass
            

    def get_open(self):
        # QUICK LOAD
        self.openeddata = self.get_all_pages(self.openedurl)
        self.datadict = self.data_to_dict(self.openeddata)


    def get_closed(self):
        # SAFE LOAD
        thisurl, urlset, pages = self._get_all_urls(self.closedurl)
        self._pages_to_dict(pages)


    ##########################
    # PAGINATION
    ##########################

    def _pages_to_dict(self, pages):            
        for gp in pages:
            #import epdb; epdb.st()
            thisdata = None
            try:
                thisdata = json.loads(gp.text or gp.content)
            except ValueError:
                epdb.st()
                sys.exit(1)

            #print thisdata
            #pprint(thisdata)
            for t in thisdata:
                #print t['number'] 
                self.datadict[t['number']] = t
    
    def get_one_page(self, url):
        print "# fetching: %s" % url
        i = requests.get(url, auth=(self.username, self.password))
        #print "# fetched: %s" % url
        return i

    # NOT SAFE FOR TOO MANY PAGES AT ONCE
    def get_all_pages(self, url, fetched=[], data=[]):
        next_page = None
        i = self.get_one_page(url)
        fetched.append(url)
        if not i.ok:
            pprint(i)
            sys.exit(1)

        try:
            thisdata = json.loads(i.text or i.content)
        except ValueError:
            epdb.st()
            sys.exit(1)
    
        for t in thisdata:
            data.append(t)

        if 'link' in i.headers:
            #print "# %s" % i.headers['link']
            next_page = i.headers['link'].split(';')[0]
            next_page = next_page.replace('<', '')        
            next_page = next_page.replace('>', '')        

        if next_page is None or next_page in fetched:
            return data
        else:
            data += self.get_all_pages(next_page, fetched=fetched, data=data)
            return data

    # GET THE RAW RESPONSE FOR ALL PAGES
    def _get_all_urls(self, url, urls=[], pages=[]):
        #print "url: %s" % url                
        if url not in urls:
            i = self.get_one_page(url)
            pages.append(i)
            urls.append(url)

        if 'next' in i.links:
            #print i.links['next']
            if i.links['next']['url'] not in self.fetched:
                #import epdb; epdb.st()
                next_url = i.links['next']['url']
                j, urls, pages = self._get_all_urls(next_url, urls=urls, pages=pages)
            #pass
        return url, urls, pages

    # FIXME: USELESS?
    def data_to_dict(self, data):
        datadict = {}
        for d in data:
            datadict[d['number']] = d
        return datadict
      

    ##########################
    # PROCESSING
    ##########################

    def _get_types(self):
        for x in self.datadict.keys():
            if self.datadict[x]['pull_request']['html_url'] is not None:
                self.datadict[x]['type'] = 'pull_request'
            else:
                self.datadict[x]['type'] = 'bug_report'

    def _get_ages(self):
        for x in self.datadict.keys():
            # 2013-01-02T22:14:22Z

            start = self.datadict[x]['created_at'] 
            start = eval(self._safe_string(start))
            start = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")

            end = self.datadict[x]['closed_at']
            end = eval(self._safe_string(end))
            end = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")

            age = end - start
            age = age.days
            if age > 1000:
                epdb.st()

            self.datadict[x]['age'] = age
            #epdb.st()

    def _get_usernames(self):
        for x in self.datadict.keys():
            #epdb.st()
            thisuser = None
            if 'user' in self.datadict[x]:
                if 'login' in self.datadict[x]['user']:
                    thisuser = self.datadict[x]['user']['login']
            if thisuser is None:
                self.datadict[x]['user'] = "unknown"
            else:
                self.datadict[x]['user'] = thisuser

    def _get_labels(self):
        for x in self.datadict.keys():
            #if x == 277:
            #    epdb.st()
            if 'labels_url' in self.datadict[x]:
                del self.datadict[x]['labels_url']
            if 'labels' in self.datadict[x]:
                labels = []
                if len(self.datadict[x]['labels']) > 0:
                    for l in self.datadict[x]['labels']:
                        labels.append(l['name'])
                    self.datadict[x]['labels'] = str(labels)
                    #epdb.st()
            else:
                self.datadict[x]['labels'] = str([])


    ##########################
    # OUTPUTS
    ##########################

    # FIXME
    def display(self, sort_by=None):
        self.show_pr_sorted(sort_by=sort_by)

    #FIXME
    def showkeys(self):
        keys = []
        for k1 in self.datadict.keys():
            for k2 in self.datadict[k1].keys():
                keys.append(k2)           
        keys = sorted(set(keys))

        for k in keys:
            print k

    # GOOD
    def show_all(self):
        #import epdb; epdb.st()
        self.get_open()
        self.get_pull_request_patches()
        self.get_pull_request_commits()
        self._print_datadict()

    # GOOD
    def show_closed(self):
        #pass
        self.get_closed()
        self._get_types()
        self._get_ages()
        self._get_usernames()
        self._get_labels()
        self.get_pull_request_patches()
        self.get_pull_request_commits()
        self.get_events()
        self.get_closure_info()
        self.get_comments()
        #self.merged_or_not()
        self._print_datadict()

    # GOOD
    def _print_datadict(self):
        columns = ['number', 'created_at', 'closed_at', 'title']
        sorted_x = sorted(set(self.datadict.keys()))
        for x in sorted_x:
            for k in self.datadict[x].keys():
                if k not in columns:
                    if k != 'body':
                        columns.append(str(k))

        header = ""
        for col in columns:
            header += col + ";"
        print header

        for x in sorted_x:
            outline = ""
            for col in columns:
                if col not in self.datadict[x]:
                    self.datadict[x][col] = None

                outline += self._safe_string(self.datadict[x][col]) + ";"

            try:             
                print outline
            except UnicodeEncodeError:
                #epdb.st()
                pass

            """
            if x == 16:
                epdb.st()
            """


    def _safe_string(self, data):

        if type(data) is unicode:
            try:
                data = data.encode('ascii')
            except UnicodeEncodeError:
                data = "UNICODE"

        if type(data) == int:
            data = str(data)
        if type(data) == list:
            if len(data) > 0:
                data = data[0]
            data = "%s" % str(data)                

        if type(data) == str:
            if '\n' in data:
                data = str(data.split('\n')[0])

        if type(data) == dict:
            #epdb.st()
            data = "DICT"
   
        if type(data) == bool:
            data = str(data)
    
        if data is None:
            data = "None"

        if type(data) != str:
            epdb.st()

        if ':' in data and '{' in data and len(data) > 100:
            #epdb.st()
            data = "DICT"

        if data.startswith("https://"):
            pass

        data = data.replace('"', '')
        data = data.replace("'", "")

        return "\"" + data + "\""
        

    # FIXME: REFACTOR
    def show_data(self, datadict):
        for k in sorted(datadict.keys()):
            print str(k) + " - " + datadict[k]['title']
        print "\n## %s issues total ##\n" % len(sorted(datadict.keys()))

    # FIXME: REFACTOR
    def show_pr_sorted(self, sort_by=None):
        x = {}

        for k in self.datadict.keys():
            if sort_by in self.datadict[k]:
                x[k] = self.datadict[k][sort_by]

        if sort_by is None:
            sorted_x = sorted(set(self.datadict.keys()))
            print "\n#ISSUE;TITLE\n"
            for x in sorted_x:
                print "%s;\"%s\"" % (x, self.datadict[x]['title'])

        else:
            sorted_x = sorted(x.iteritems(), key=operator.itemgetter(1))
            print "\n#ISSUE;%s;TITLE\n" % sort_by
            for x in sorted_x:
                number, sort_val = x
                print "%s;%s;\"%s\"" % (number, sort_val, self.datadict[number]['title'])

    def show_pr_by_file(self):
        self.get_open()
        self.get_pull_request_patches()
        self.get_pull_request_commits()

        files = {}

        for k in self.datadict.keys():
            #print k
            if 'patch_files_filenames' not in self.datadict[k]:
                continue
            kfiles = self.datadict[k]['patch_files_filenames']
            tmpfiles = []

            # remove a/
            for x in kfiles:
                xtmp = list(x)
                xtmp[0] = ''
                xtmp[1] = ''
                xnew = "".join(x)
                tmpfiles.append(xnew)

            # add this PR# to the files list
            for x in tmpfiles:
                if x not in files:
                    files[x] = []
                if k not in files[x]:
                    files[x].append(k)

        if not self.cli.pargs.html:
            #import epdb; epdb.st()
            for k in sorted(files, key=lambda k: len(files[k]), reverse=True):
                print len(files[k]),":",k
                for x in files[k]:
                    try:
                        print "\t",x,self.datadict[x]['title']
                    except UnicodeEncodeError:
                        print "\t",x," non-ascii title"
                    #import epdb; epdb.st()

        else:
            self._pr_file_age_to_html(files)

    def _pr_file_age_to_html(self, files):
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
                thisurl = self.datadict[x]['html_url']
                thisid = '<a href="%s">%s</a>' %(thisurl, x)
                try:
                    print '<div id="inner">%s : %s</div>\n' % (thisid, self.datadict[x]['title'])
                except UnicodeEncodeError:
                    print '<div id="inner">%s : %s</div>\n' % (thisid, "UNICODE")
            print '</div>\n' 


        print "</body>"
        print "</html>"



    ##########################
    # PATCH ENUMERATION
    ##########################

    def get_pull_request_commits(self):
        # http://developer.github.com/v3/pulls/
        # https://api.github.com/repos/ansible/ansible/pulls/2476/commits
        #import epdb; epdb.st()
        for x in self.datadict.keys():
            if self.datadict[x]['pull_request']['patch_url'] is not None:
                self.datadict[x]['pr_commit_merge_count'] = 0
                self.datadict[x]['pr_commit_count'] = 0
                commits_url = self.baseurl + "/" + self.repo + "/pulls/" + str(x) + "/commits"
                y = self.get_one_page(commits_url)
                #import epdb; epdb.st()
                if y.ok:
                    self.datadict[x]['pull_commits'] = json.loads(y.content)

                    for pc in self.datadict[x]['pull_commits']:
                        self.datadict[x]['pr_commit_count'] += 1
                        #import epdb; epdb.st()
                        if pc['commit']['message'].startswith('Merge branch'):
                            self.datadict[x]['pr_commit_merge_count'] += 1

    def get_pull_request_patches(self):
        for k in self.datadict.keys():
            #epdb.st()
            i = self.datadict[k]['number']
            pr = self.datadict[k]['pull_request']
            
            if pr['patch_url'] is not None:

                patchfile = os.path.join(self.cachedir, "%s.patch" % k)

                if not os.path.isfile(patchfile):
                    patch_page = self.get_one_page(pr['patch_url'])
                    self.datadict[k]['patch_text'] = patch_page.text
                else:
                    patch_text = open(patchfile).read()
                    self.datadict[k]['patch_text'] = patch_text

                # generate synthetic meta            
                patch_meta = self.parse_patch(self.datadict[k]['patch_text'])
                for pk in patch_meta.keys():
                    self.datadict[k][pk] = patch_meta[pk]
                    
                try:
                    open(patchfile, "wb").write(self.datadict[k]['patch_text'])
                except UnicodeEncodeError:
                    pass
                except:
                    import epdb; epdb.st()

    def parse_patch(self, rawtext):
        rdict = {}

        patch_lines = rawtext.split('\n')
        rdict['patch_length'] = len(patch_lines)
        rdict['patch_files_filenames'] = []
        rdict['patch_files_new'] = 0
        rdict['patch_has_tests'] = False

        for line in patch_lines:
            if 'files changed' in line \
                and 'insertions' in line \
                and 'deletions' in line:

                sections = line.split(',')
                for section in sections:
                    section = section.replace('(+)','')
                    section = section.replace('(-)','')

                    if 'files changed' in section:
                        rdict['patch_files_changed'] = shlex.split(section)[0]

                    if 'insertions' in section:
                        rdict['patch_insertions'] = shlex.split(section)[0]

            if line.startswith('new file mode'):
                rdict['patch_files_new'] += 1
            if line.startswith('diff --git'):
                tmpline = line.replace('diff --git ', '')
                thisfilename = shlex.split(tmpline)[0]
                rdict['patch_files_filenames'].append(thisfilename)
                if thisfilename.startswith('a/test/'):
                    rdict['patch_has_tests'] = True

        return rdict

                         
    ##########################
    # EVENTS ENUMERATION
    ##########################

    def get_events(self):
        for k in self.datadict.keys():
            if 'events_url' in self.datadict[k]:
                i = self.get_one_page(self.datadict[k]['events_url'])
                idict = json.loads(i.content)
                self.datadict[k]['events'] = idict
                del self.datadict[k]['events_url']

    def get_closure_info(self):
        eventtypes = ['assigned', 'referenced', 'closed', 'subscribed', 'merged']
        found = []

        for k in self.datadict.keys():
            if 'events' in self.datadict[k]:

                self.datadict[k]['merged'] = False
                self.datadict[k]['closure_count'] = 0
                self.datadict[k]['reopen_count'] = 0

                for ev in self.datadict[k]['events']:

                    if ev['event'] not in found:
                        found.append(ev['event'])

                    if ev['event'] == 'merged':
                        self.datadict[k]['merged'] = True
                        self.datadict[k]['merged_by'] = ev['actor']['login']

                    if ev['event'] == 'closed':
                        self.datadict[k]['closed'] = True
                        self.datadict[k]['closure_count'] += 1
                        try:
                            if 'actor' in ev:
                                if ev['actor'] is not None:
                                    if 'login' in ev['actor']:
                                        self.datadict[k]['closed_by'] = ev['actor']['login']
                            else:
                                self.datadict[k]['closed_by'] = None
                        except TypeError:
                            print k
                            epdb.st()

                    if ev['event'] == 'reopened':
                        self.datadict[k]['reopened'] = True
                        self.datadict[k]['reopen_count'] += 1
                        self.datadict[k]['reopened_by'] = ev['actor']['login']

                    #if ev['event'] not in eventtypes:                    
                    #    epdb.st()
        #epdb.st()
        return None
            


    ##########################
    # COMMENTS ENUMERATION
    ##########################

    def get_comments(self):
        for k in self.datadict.keys():
            if 'comments_url' in self.datadict[k]:
                i = self.get_one_page(self.datadict[k]['comments_url'])
                idict = json.loads(i.content)
                self.datadict[k]['comments'] = idict
                #import epdb; epdb.st()

        self.get_closure_comment()

    def get_closure_comment(self):

        for k in self.datadict.keys():
            # created_at == timestamp for this comment
            # self.datadict[k]['events'][0]['created_at'] 

            #if self.datadict[k]['type'] == 'pull_request' and self.datadict[k]['state'] == 'closed':
            if self.datadict[k]['state'] == 'closed':

                # result
                closure_comment_ids = []
                closure_comment_texts = []
                closure_comment_objs = []

                closed_times = []

                for ev in self.datadict[k]['events']:
                    if ev['event'] == 'closed':
                        thisdate = ev['created_at']
                        thisdate = datetime.strptime(thisdate, "%Y-%m-%dT%H:%M:%SZ")
                        closed_times.append(thisdate)

                for closed_time in closed_times:
                    first_comment_id = None
                    first_comment_obj = None
                    first_comment_author = None
                    first_comment_date = None
                    exact_match = False

                    for com in self.datadict[k]['comments']:
                        if com['user']['login'] in self.repo_admins:

                            thisid = com['id']
                            this_author = com['user']['login']
                            thisdate = com['created_at']
                            thisdate = datetime.strptime(thisdate, "%Y-%m-%dT%H:%M:%SZ")

                            #epdb.st()
                            #if thisdate == closed_time and k == '875':
                            if thisdate == closed_time:
                                #print "DEBUG"
                                #epdb.st()
                                exact_match = True
                                first_comment_date =  thisdate
                                first_comment_obj = com
                                frist_comment_author = this_author
                                first_comment_id = thisid

                            if thisdate > closed_time and not exact_match:
                                #epdb.st()
                                if first_comment_date is None or thisdate < first_comment_date:
                                    first_comment_date =  thisdate
                                    first_comment_obj = com
                                    frist_comment_author = this_author
                                    first_comment_id = thisid

                    if first_comment_id is not None and first_comment_id not in closure_comment_ids:
                        closure_comment_ids.append(first_comment_id)
                        closure_comment_objs.append(first_comment_obj)
                        try:
                            closure_comment_texts.append(first_comment_obj['body'])
                        except:
                            epdb.st()

                # more than one closure comment? What now?
                if len(closure_comment_ids) > 0 \
                    and self.datadict[k]['type'] == 'pull_request' \
                    and not self.datadict[k]['merged'] \
                    and self.datadict[k]['closed_by'] in self.repo_admins:

                    #pass
                    #epdb.st()
                    for t in closure_comment_texts:
                        tmpstring = t.replace('\n', '')
                        open("/tmp/reasons.txt", "a").write("##########################\n")
                        try:
                            open("/tmp/reasons.txt", "a").write("%s:: %s\n" % (k, tmpstring))
                        except UnicodeEncodeError:
                            open("/tmp/reasons.txt", "a").write("%s:: UNICODEERROR\n" % k)
                        open("/tmp/reasons.txt", "a").write("##########################\n")
                        #if '?' in t:
                        #    epdb.st()
