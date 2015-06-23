#!/bin/bash -eu

for log in workdir_prep/out/*.out.txt
do
  echo $log
  fp=$(tac $log | grep -m1 Copying | cut -d " " -f2 | sed "s/[^ ]*output\/\(.*\)/\1/g")
  if [ ! -z "$fp" ]
  then
    set +e
    echo rm /stornext/online14/ocean/cmip5_send/output/$fp.bz2
    set -e
    echo
  fi
done
