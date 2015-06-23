#!/bin/bash

PYTHON=/usr/bin/python
INPATH=$1
OUTPATH=$2

echo "This script will create yaml files for all tables in $INPATH."
echo "The new tables will be stored in $OUTPATH."

$PYTHON createYaml.py $INPATH $OUTPATH
