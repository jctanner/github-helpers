#!/bin/bash

ACTIVATE=$1
USERNAME=$2
PASSWORD=$3
REPO=$4
OUTPUTDIR=$5
WEBDIR=$OUTPUTDIR

rm -f $WEBDIR/prs_by_file.html
issues showprfiles --html --no-cache | egrep -v ^\# | egrep -v 1034h | tee -a $WEBDIR/prs_by_file.html

rm -f $WEBDIR/prs_by_user.html
issues showprusers --html --no-cache | egrep -v ^\# | egrep -v 1034h | tee -a $WEBDIR/prs_by_user.html

rm -rf $WEBDIR/pr_merge_commits.html
issues showprmergecommits --html --no-cache | egrep -v ^\# | egrep -v 1034h | tee -a $WEBDIR/pr_merge_commits.html

rm -rf $WEBDIR/unlabeled_issues.html
issues showunlabeled --html  --no-cache | egrep -v ^\# | egrep -v 1034h | tee -a $WEBDIR/unlabeled_issues.html

rm -rf $WEBDIR/unlabeled_cloud_issues.html
issues showbadcloud --html  --no-cache | egrep -v ^\# | egrep -v 1034h | tee -a $WEBDIR/unlabeled_cloud_issues.html
