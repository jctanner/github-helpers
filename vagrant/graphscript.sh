#!/bin/bash

killall Xvfb
export DISPLAY=:1 
Xvfb $DISPLAY -auth /dev/null &

ACTIVATE=$1
USERNAME=$2
PASSWORD=$3
REPO=$4
OUTPUTDIR=$5

source $ACTIVATE 
#echo --username="$USERNAME" --password="$PASSWORD" --repo="$REPO" --outputdir="$OUTPUTDIR" >> /tmp/awx.log
issues showrates --username="$USERNAME" --password="$PASSWORD" --repo="$REPO" --outputdir="$OUTPUTDIR"


killall Xvfb
