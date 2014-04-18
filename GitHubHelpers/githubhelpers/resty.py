#!/usr/bin/env python

import os
import sys
import requests
import requests_cache
import urllib
import json
from pprint import pprint
import yaml
import epdb
import operator
import shlex
from datetime import *
from pprint import pprint
import time

class Resty(object):
    def __init__(self, caching=False, username=None, password=None, token=None):
        self.username = username
        self.password = password
        self.token = token
        self.fetched = []


    def get_one_page_old(self, url, usecache=False):
    
        """ Get a single page """
    
        print "# fetching: %s" % url
        if self.username and self.password:
            i = requests.get(url, auth=(self.username, self.password))
        elif token:
            i = requests.get(url, headers={'Authorization': "token %s" % self.token})
        else:
            i = requests.get(url)

        return i

    def get_all_urls(self, url, gpages=[], usecache=False):

        """ Recursively fetch all pages for a url """

        if not gpages:
            gpages = []

        i = None
        if url not in [x.url for x in gpages]:
            i = self.get_one_page(url, usecache=usecache)

            if i.url == url:

                if i.url in [x.url for x in gpages]:
                    print "WHAT!!!!"
                    epdb.st()
                else:
                    gpages.append(i)

                # TBD
                """
                if hasattr(i, 'links'):
                    if 'next' in i.links:
                        if i.links['next']['url'] not in self.fetched:
                            import epdb; epdb.st()
                            next_url = i.links['next']['url']
                            j, gpages = self.get_all_urls(next_url, pages=gpages, usecache=usecache)
                """

            else:
                pass

        return url, gpages

    # GET THE RAW RESPONSE FOR ALL PAGES
    def _get_all_urls(self, url, urls=[], pages=[], usecache=True):
        #print "url: %s" % url
        i = None
        if url not in urls:
            #print "\tfetching"
            #i = self.get_one_page(url, usecache=usecache)
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

    def data_to_dict(self, url, key=None, usecache=False):

        """ Paginate a REST url and convert all data to a dictionary """

        datadict = {}
        gpages = []
        pages = []

        # recursively get all pages for this resource
        thisurl, pages = self.get_all_urls(url, gpages=None)
        for gp in pages:
            thisdata = None
            try:
                thisdata = json.loads(gp.text or gp.content)
            except ValueError:
                epdb.st()
                sys.exit(1)

            # add each element to the dict by key
            for t in thisdata:
                try:
                    datadict[t[key]] = t
                except TypeError:
                    epdb.st()

        return datadict

    def get_one_page(self, url, usecache=True, ignoreerrors=True):

        limited = True

        while limited:
            if not usecache:
                if requests_cache.get_cache().has_url(url):
                    requests_cache.get_cache().delete_url(url)

            if self.username and self.password:
                print "# fetching (BASIC): %s" % url
                i = requests.get(url, auth=(self.username, self.password))
            elif self.token:
                print "# fetching (TOKEN): %s" % url
                i = requests.get(url, headers={'Authorization': "token %s" % self.token})
            else:
                print "# fetching (NONE): %s" % url
                i = requests.get(url)

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
                n_time = time.time()
                n_time = datetime.fromtimestamp(n_time).strftime('%Y-%m-%d $H:%M:%S')
                print "# %s sleeping %s" % (n_time, sleeptime)
                time.sleep(sleeptime)

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
