#!/bin/bash -eu

source cmip5_functions

TODO=$(./check_ok_cmip | grep TODO | cut -d " " -f1,3 --output-delimiter="|")
for exp_data in $TODO
do
  exp_name=$(echo $exp_data | cut -d "|" -f1)
  exp_begin=$(echo $exp_data | cut -d "|" -f2 | cut -d "/" -f1)
  ./submit_aux $ARCHIVE_OCEAN/$(decode_cmip5_name $exp_name)/CGCM $exp_begin &
  #./submit_aux $ARCHIVE_OCEAN/$(decode_cmip5_name 2000_r5i1p1_a)/CGCM 117
  #./submit_aux $ARCHIVE_OCEAN/$(decode_cmip5_name 1985_r5i1p1_o)/CGCM 118
done
