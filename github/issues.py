#!/usr/bin/python

import sys
import requests
import json
from pprint import pprint
import yaml
import epdb
import operator
import shlex

# caching magic
import requests_cache
requests_cache.install_cache('/tmp/github_cache')

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
        self.baseurl = baseurl

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

        self.fullurl = baseurl + "/" + self.repo + "/issues?state=open"

        self.pagedata = self.get_all_pages(self.fullurl)
        self.datadict = self.data_to_dict(self.pagedata)
        self.get_pull_request_patches()
        self.get_pull_request_commits()

        #import epdb; epdb.st()

    def display(self, sort_by=None):

        self.show_pr_sorted(sort_by=sort_by)

    def showkeys(self):
        keys = []
        for k1 in self.datadict.keys():
            for k2 in self.datadict[k1].keys():
                keys.append(k2)           
        keys = sorted(set(keys))

        for k in keys:
            print k

    def get_one_page(self, url):
        print "# fetching: %s" % url
        i = requests.get(url, auth=(self.username, self.password))
        return i


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

    def data_to_dict(self, data):
        datadict = {}
        for d in data:
            datadict[d['number']] = d
        return datadict
      
    def show_data(self, datadict):
        for k in sorted(datadict.keys()):
            print str(k) + " - " + datadict[k]['title']
        print "\n## %s issues total ##\n" % len(sorted(datadict.keys()))

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

    def get_pull_request_patches(self):
        for k in self.datadict.keys():
            #epdb.st()
            i = self.datadict[k]['number']
            pr = self.datadict[k]['pull_request']
            
            if pr['patch_url'] is not None:

                patch_page = self.get_one_page(pr['patch_url'])
                self.datadict[k]['patch_text'] = patch_page.text

                # generate synthetic meta            
                patch_meta = self.parse_patch(patch_page.text)
                for pk in patch_meta.keys():
                    self.datadict[k][pk] = patch_meta[pk]
                    
                try:
                    open("/tmp/%s.patch" % k, "wb").write(patch_page.text)
                except UnicodeEncodeError:
                    pass
                except:
                    import epdb; epdb.st()


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
