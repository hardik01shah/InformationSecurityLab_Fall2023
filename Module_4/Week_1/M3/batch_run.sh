#!/bin/bash
echo "Bash version ${BASH_VERSION}..."
echo "Running $1 times"
for i in $(seq 1 $1);
do 
  REMOTE=True sage lab1m3.py 
done