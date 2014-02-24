#!/usr/bin/env python

import os
import sys
import requests
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
    def __init__(self, caching=False, username=None, password=None):
        self.username = username
        self.password = password


    def get_one_page(self, url, usecache=False):
    
        """ Get a single page """
    
        print "# fetching: %s" % url
        if self.username and self.password:
            i = requests.get(url, auth=(self.username, self.password))
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

                # recurse through next page(s)
                if hasattr(i, 'links'):
                    if 'next' in i.links:
                        if i.links['next']['url'] not in [x.url for x in gpages]:
                            next_url = i.links['next']['url']
                            j, gpages = self.get_all_urls(next_url, 
                                            gpages=gpages, usecache=usecache)

            else:
                pass

        return url, gpages

    def data_to_dict(self, url, key=None, usecache=False):

        """ Paginate a REST url and convert all data to a dictionary """

        datadict = {}
        gpages = []
        pages = []

        # recursively get all pages for this resource
        thisurl, pages = self.get_all_urls(url, gpages=None)
        #import epdb; epdb.st()

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
                except TypeError, e:
                    epdb.st()
        return datadict
