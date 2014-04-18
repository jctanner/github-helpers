#!/bin/bash 

set +x

killall Xvfb
export DISPLAY=:1
Xvfb $DISPLAY -auth /dev/null &


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

rm -f $WEBDIR/*

issues showrates --html --no-cache --repo=$REPO --token="$TOKEN" --outputdir=$OUTPUTDIR

deactivate
killall Xvfb
