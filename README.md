github-helpers
==============

github helpers


##### CONFIG FILE
```bash
$ cat ~/test.cfg 
[github]
repo=ansible/ansible
username=<USERNAME>
password=<PASSWORD>
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
