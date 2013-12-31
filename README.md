github-helpers
==============

github helpers


# CONFIG FILE
$ cat ~/test.cfg 
[github]
repo=ansible/ansible
username=<USERNAME>
password=<PASSWORD>

# CREATE HTML REPORTS
bin/issues showprfiles --html | egrep -v ^\# | egrep -v 1034h > /var/www/html/prs_by_file.html
bin/issues showprmergecommits --html | egrep -v ^\# | egrep -v 1034h > /var/www/html/pr_merge_commits.html

# EXPORT ALL DATA TO CSV
bin/issues showall | egrep -v 1034h | egrep -v ^\# > /var/www/html/opentickets.csv
