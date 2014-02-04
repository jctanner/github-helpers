github-helpers
==============

A helper library and set of tools for the github issues API.

* triage - a cli for automating ticket triage
* issues - a cli for making reports

##### CONFIG FILE
```bash
$ cat ~/github.cfg 
[github]
repo=<github-user>/<github-repo>
username=<USERNAME>
password=<PASSWORD>
cache_max_age=30000

[triage]
botname=GitHub Ansibot
template=https://raw2.github.com/jctanner/issuetests/master/ISSUE_TEMPLATE.md
cutoff=1
interval=120
fuzzy=true
```

##### CREATE HTML REPORTS
````bash
bin/issues showprfiles --html | egrep -v ^\# | egrep -v 1034h > /var/www/html/prs_by_file.html
bin/issues showprmergecommits --html | egrep -v ^\# | egrep -v 1034h > /var/www/html/pr_merge_commits.html
```

##### EXPORT ALL DATA TO CSV
```bash
bin/issues showall | egrep -v 1034h | egrep -v ^\# > /var/www/html/opentickets.csv
```

##### Install on an EL6 system
```bash
$ yum install git
$ yum install python-pip
$ yum install python-devel
$ yum install gcc
$ yum install libyaml-devel
$ pip install virtualenv

$ useradd ansibot
su - ansibot

mkdir venvs ; cd venvs
virtualenv --no-site-packages ansibot
source ansibot/bin/activate
pip install epdb
pip install argparse
pip install https://github.com/datafolklabs/cement/archive/2.0.2.tar.gz
pip install PyYaml
pip install requests
pip install requests_cache

cd ~ ; mkdir src ; cd src
git clone https://github.com/jctanner/github-helpers
cd github-helpers
python setup.py install

# triage descriptions
```
