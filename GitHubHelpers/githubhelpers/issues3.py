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
import calendar
import requests_cache
from stringfunctions import safe_string
from pygithubwrapper import *

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
        self.cache_age = None
        try:
            self.cache_max_age = int(self.cli.config.get('github', 'cache_max_age'))
        except:
            self.cache_max_age = 300
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
        self.cachedir = os.path.join(self.homedir, ".cache", "github", self.repo.replace("/", "_"))
        self.cachefile = os.path.join(self.cachedir, "requests_cache")
        if not os.path.isdir(self.cachedir):
            os.makedirs(self.cachedir)

        #if not self.cli.pargs.no_cache:
        #    requests_cache.install_cache(self.cachefile)
        #else:
        #    pass
        requests_cache.install_cache(self.cachefile)
            

    def _get_one_issue(self, k):
        url = self.openedurl = self.baseurl + "/" + self.repo + "/issues/" + k
        i = self.get_one_page(url)                
        data = json.loads(i.content)
        return data

    def get_all(self):

        os.environ['TZ'] = "BST"
        time.tzset()

        # load pickled cache
        datadict = self._get_datadict_cache()

        # figure out what needs to be updated
        last_closed = None
        for k in sorted(datadict.keys()):
            if 'closed_at' in datadict[k]:
                if datadict[k]['closed_at']:
                    if not last_closed:
                        last_closed = datadict[k]['closed_at']
                        last_closed = datetime.strptime(last_closed, "%Y-%m-%dT%H:%M:%SZ")
                    else:
                        if datadict[k].get('closed_at', None):
                            this_time = datetime.strptime(datadict[k]['closed_at'], "%Y-%m-%dT%H:%M:%SZ")
                            if this_time > last_closed:
                                last_closed = this_time


        new_combined = {}
        if not last_closed and datadict == {}:
            # fetch all history
            opendict = self.get_open()
            closeddict = self.get_closed()
            datadict =  dict(opendict.items() + closeddict.items())

        else:

            # create dict for updated issues
            new_open = self.get_new(closed=False, lasttime=last_closed)
            new_closed = self.get_new(closed=True, lasttime=last_closed)
            new_combined = dict(new_open.items() + new_closed.items())

            for k in sorted(new_combined.keys()):
                #k = str(k)
                datadict[str(k)] = new_combined[k]
                # kill the pygithub obj for this issue
                this_file = os.path.join(self.cachedir, k + ".pygithub")
                if os.path.isfile(this_file):
                    os.remove(this_file)

        # test for complete list
        sorted_keys = sorted([int(x) for x in datadict.keys()])
        #sorted_keys = [str(x) for x in sorted_keys]
        for kx in range(sorted_keys[0], sorted_keys[-1]):
            kx = str(kx)
            if kx not in datadict:
                #import epdb; epdb.st()
                datadict[kx] = self._get_one_issue(kx)
                #import epdb; epdb.st()

        # simple processing
        datadict = self._set_dict_keys_to_string(datadict)
        datadict = self._get_types(datadict)
        datadict = self._get_ages(datadict)
        datadict = self._get_usernames(datadict)
        datadict = self._get_labels(datadict)
        datadict = self._set_dict_keys_to_string(datadict)

        # get events+comments and save incrementally
        for k in sorted([int(x) for x in datadict.keys()]):
            k = str(k)
            try:
                if not 'events' in datadict[str(k)] or str(k) in new_combined.keys():
                    datadict[k]['events'] = self.get_events(datadict[k]['events_url'])
            except:
                import epdb; epdb.st()
            if not 'comments' in datadict[str(k)] or str(k) in new_combined.keys():    
                datadict[k]['comments']  = self.get_comments(datadict[k]['comments_url'])
            self._pickle_single_datadict_cache((k, datadict[k]))

        # closure stats for each issue
        datadict = self.get_closure_info(datadict)

        # fetch the pygithub data
        datadict = self.load_pygithub_objects(datadict)
        datadict = self._get_closed_by(datadict)

        # save everything
        self._put_datadict_cache(datadict)
        self.datadict = datadict

    def _set_dict_keys_to_string(self, datadict):
        newdict = {}
        for k in datadict.keys():
            newdict[str(k)] = datadict[k]
        return newdict

    def _load_single_datadict_cache(self, issueid):
        this_issue = None
        this_file = os.path.join(self.cachedir, issueid + '.datadict')
        if os.path.isfile(this_file):
            this_issue = pickle.load(open(this_file, "rb"))
        return this_issue        

    def _pickle_single_datadict_cache(self, issue):
        # issue == (id, data)
        issueid = str(issue[0])
        issuedata = issue[1]
        this_file =  os.path.join(self.cachedir, issueid + '.datadict')
        if os.path.isfile(this_file):
            os.remove(this_file)
        pickle.dump(issuedata, open(this_file, "wb"))

    def _get_datadict_cache(self):
        datadict = {}
        files = os.listdir(self.cachedir)
        files = [x for x in files if x.endswith('.datadict')]
        for d in files:
            issueid = d.split('.')[0]
            data = self._load_single_datadict_cache(issueid)
            if data:
                datadict[str(issueid)] = data                
        return datadict

    def _put_datadict_cache(self, datadict):
        print '# writing datadict caches'
        for i in datadict.items():
            self._pickle_single_datadict_cache(i)

    def get_open(self):
        # QUICK LOAD
        #self.openeddata = self.get_all_pages(self.openedurl)
        #datadict = self.data_to_dict(self.openeddata)
        thisurl, urlset, pages = self._get_all_urls(self.openedurl)
        datadict = self._pages_to_dict(pages)
        return datadict


    def get_closed(self):
        # SAFE LOAD
        thisurl, urlset, pages = self._get_all_urls(self.closedurl)
        datadict = self._pages_to_dict(pages)
        return datadict

    def get_new(self, closed=False, lasttime=None):
        """
        since   string  
        Only issues updated at or after this time are returned. 
        This is a timestamp in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ.
        """
        # https://api.github.com/repos/ansible/ansible/issues?state=open;since=2014-01-30T00:00:00Z        

        # * find newest "last updated" from datadict?
        # * find new updates since cache last modified?

        #from datetime import date, timedelta
        #ys = date.today() - timedelta(1)

        if not lasttime:
            ts = time.strftime("%Y-%m-%dT00:00:00Z")
            if os.path.isfile(self.cachefile + ".sqlite"):
                # match the github api timezone
                os.environ['TZ'] = "BST"
                time.tzset()

                # get the exact date of last cache modification
                st = os.stat(self.cachefile + ".sqlite")
                x = time.localtime(st.st_mtime)

                # make a suitable string for filtering updated tickets
                #ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", x)            
                ts = time.strftime("%Y-%m-%dT%H:%M:00Z", x)            
        else:
            ts = lasttime

        if not closed:
            newurl = self.baseurl + "/" + self.repo + "/issues?state=open;since=%s" % ts
        else:
            newurl = self.baseurl + "/" + self.repo + "/issues?state=closed;since=%s" % ts
            
        thisurl, urlset, pages = self._get_all_urls(newurl, usecache=False)
        datadict = self._pages_to_dict(pages)
        return datadict

    def load_pygithub_objects(self, datadict):
        #import epdb; epdb.st()
        pgw = PyGithubWrapper()        
        pgw.cli = self.cli
        pgw.cachedir = self.cachedir
        datadict = pgw.load_pygithub_objects(datadict)
        return datadict


    ##########################
    # PAGINATION
    ##########################

    def _pages_to_dict(self, pages):            
        datadict = {}

        for gp in pages:
            thisdata = None
            try:
                thisdata = json.loads(gp.text or gp.content)
            except ValueError:
                epdb.st()
                sys.exit(1)

            for t in thisdata:
                #TypeError: string indices must be integers
                try:
                    datadict[str(t['number'])] = t
                except TypeError, e:
                    import epdb; epdb.st()

        return datadict

    def _wait_for_limiting(self):
        # https://api.github.com/users/whatever
        url = 'https://api.github.com/users/' + self.username
        sleeptime = True
        while sleeptime:
            if requests_cache.get_cache().has_url(url):
                requests_cache.get_cache().delete_url(url)
            i = requests.get(url, auth=(self.username, self.password))
            sleeptime = i.headers.get('X-RateLimit-Reset', None)
            if sleeptime:
                sleeptime = calendar.timegm(time.gmtime()) - int(sleeptime)
                if sleeptime < 0:
                    sleeptime = sleeptime * -1
                print "# sleeping %s" % sleeptime
                time.sleep(sleeptime)
        #import epdb; epdb.st()
    
    def get_one_page(self, url, usecache=True, ignoreerrors=True):

        limited = True

        while limited:
            if not usecache:
                if requests_cache.get_cache().has_url(url):
                    requests_cache.get_cache().delete_url(url)

            print "# fetching: %s" % url
            i = requests.get(url, auth=(self.username, self.password))
            if not i.ok:
                print "# ERROR: %s for %s " % (i.reason, url)
                #import epdb; epdb.st()
                if 'rate limit exceeded' in i.content:
                    self._wait_for_limiting()
                elif i.reason == 'Not Found':
                    limited = False
                else:
                    import epdb; epdb.st()
                    sys.exit(1)
            else:
                data = None
                try: 
                    data = json.loads(i.content)
                except:
                    pass
                if data:
                    if 'documentation_url' in data:
                        limited = True
                        print "# hit rate limit, sleeping 300s"
                        time.sleep(300)
                    else:
                        limited = False
                else:
                    limited = False
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
    def _get_all_urls(self, url, urls=[], pages=[], usecache=True):
        #print "url: %s" % url                
        i = None
        if url not in urls:
            #print "\tfetching"            
            i = self.get_one_page(url, usecache=usecache)
            pages.append(i)
            urls.append(url)
        else:
            #print "\turl fetched already"            
            pass

        if hasattr(i, 'links'):
            if 'next' in i.links:
                #print i.links['next']
                if i.links['next']['url'] not in self.fetched:
                    #import epdb; epdb.st()
                    next_url = i.links['next']['url']
                    j, urls, pages = self._get_all_urls(next_url, urls=urls, pages=pages, usecache=usecache)
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

    def _get_types(self, datadict):
        for x in datadict.keys():
            if 'pull_request' in datadict[x]:
                if datadict[x]['pull_request']['html_url'] is not None:
                    datadict[x]['type'] = 'pull_request'
                else:
                    datadict[x]['type'] = 'issue'
            else:
                datadict[x]['type'] = 'issue'
        return datadict

    def _get_ages(self, datadict):
        for x in datadict.keys():
            # 2013-01-02T22:14:22Z

            if 'created_at' not in datadict[x]:
                import epdb; epdb.st()

            start = datadict[x]['created_at'] 
            start = eval(safe_string(start))
            start = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")

            end = datadict[x]['closed_at']
            end = eval(safe_string(end))
            if end is not 'None':
                end = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
            else:
                end = datetime.now()

            age = end - start
            age = age.days

            datadict[x]['age'] = age
        return datadict

    def _get_usernames(self, datadict):
        for x in datadict.keys():
            #epdb.st()
            thisuser = None
            if 'user' in datadict[x]:
                if 'login' in datadict[x]['user']:
                    thisuser = datadict[x]['user']['login']
            if thisuser is None:
                datadict[x]['user'] = "unknown"
            else:
                datadict[x]['user'] = thisuser
        return datadict                

    def _get_labels(self, datadict):
        for x in datadict.keys():
            #if x == 277:
            #    epdb.st()
            if 'labels_url' in datadict[x]:
                del datadict[x]['labels_url']
            if 'labels' in datadict[x]:
                labels = []
                if len(datadict[x]['labels']) > 0:
                    ilabels = datadict[x]['labels']
                    if type(ilabels) == str:
                        ilabels = eval(ilabels)
                    for l in ilabels:
                        try:
                            labels.append(l)
                        except:
                            import epdb; epdb.st()
                            #pass
                    datadict[x]['labels'] = str(labels)
                    #epdb.st()
            else:
                datadict[x]['labels'] = str([])
        return datadict                

    def _get_closed_by(self, datadict):

        for k in sorted(datadict.keys()):
            this_issue = datadict[k]['pygithub']
            this_creator = this_issue.user.login
            try:
                this_closer = this_issue.closed_by.login
            except:
                this_closer = None
            datadict[k]['creator'] = this_creator
            datadict[k]['closer'] = this_closer

            if this_creator == this_closer:
                datadict[k]['user_closed'] = True
            else:
                datadict[k]['user_closed'] = False
        return datadict

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

    def get_events(self, events_url):
        # FIXME: multiple pages
        i = self.get_one_page(events_url)
        idict = json.loads(i.content)
        return idict

    def get_closure_info(self, datadict):
        eventtypes = ['assigned', 'referenced', 'closed', 'subscribed', 'merged']
        found = []

        sortedkeys = sorted([int(x) for x in datadict.keys()]) 
        sortedkeys = [ str(x) for x in sortedkeys ]

        #for k in datadict.keys():
        for k in sortedkeys:

            if 'events' in datadict[k]:

                if 'documentation_url' in datadict[k]['events']:
                    # were we rate limited?
                    datadict[k]['events'] = self.get_events(datadict[k]['events_url'])
                    self._pickle_single_datadict_cache((k, datadict[k]))

                datadict[k]['merged'] = False
                datadict[k]['closure_count'] = 0
                datadict[k]['reopen_count'] = 0

                for ev in datadict[k]['events']:

                    #FIXME
                    if type(ev) == str or type(ev) == unicode:
                        # were we rate limited?
                        if ev == 'documentation_url':
                            import epdb; epdb.st()
                        else:
                            continue

                    try:
                        if ev['event'] not in found:
                            found.append(ev['event'])
                    except:
                        import epdb; epdb.st()

                    if ev['event'] == 'merged':
                        datadict[k]['merged'] = True
                        if ev['actor']:
                            if 'login' in ev['actor']:
                                datadict[k]['merged_by'] = ev['actor']['login']

                    if ev['event'] == 'closed':
                        datadict[k]['closed'] = True
                        datadict[k]['closure_count'] += 1
                        try:
                            if 'actor' in ev:
                                if ev['actor'] is not None:
                                    if 'login' in ev['actor']:
                                        datadict[k]['closed_by'] = ev['actor']['login']
                            else:
                                datadict[k]['closed_by'] = None
                        except TypeError:
                            print k
                            epdb.st()

                    if ev['event'] == 'reopened':
                        datadict[k]['reopened'] = True
                        datadict[k]['reopen_count'] += 1
                        datadict[k]['reopened_by'] = ev['actor']['login']

        return datadict
            


    ##########################
    # COMMENTS ENUMERATION
    ##########################

    def get_comments(self, usecache=True):
        for k in self.datadict.keys():
            if 'comments_url' in self.datadict[k]:

                if not usecache:
                    if requests_cache.get_cache().has_url(self.datadict[k]['comments_url']):
                        requests_cache.get_cache().delete_url(self.datadict[k]['comments_url'])

                i = self.get_one_page(self.datadict[k]['comments_url'])
                idict = json.loads(i.content)
                self.datadict[k]['comments'] = idict


