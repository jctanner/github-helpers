#!/bin/bash

ACTIVATE=$1
TOKEN=$GITHUB_API_TOKEN
REPO=$2
OUTPUTDIR=$3
WEBDIR=$OUTPUTDIR

echo "sourcing $ACTIVATE"
source $ACTIVATE


which issues
RC=$?

if [ $RC != 0 ]; then
    echo "issues command is not in the path"
    exit 1
fi


subcommands=( showprfiles showprusers showunlabeled showbadcloud showunprioritized )

rm -f $WEBDIR/*


for subcommand in "${subcommands[@]}"; do
    issues ${subcommand} --html --no-cache --token="$TOKEN" --outputdir=$OUTPUTDIR
done

deactivate
