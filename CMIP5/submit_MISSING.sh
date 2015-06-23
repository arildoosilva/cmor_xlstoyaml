#!/bin/bash -eu

source cmip5_functions

./check_ok_cmip_nodes | grep TODO | cut -d " " -f1 | sort | while read exp_data;
do
  LEN=$(echo ${#exp_data} - 4 | bc -l)
  exp_name=$(echo $exp_data | cut -c1-$LEN)

  exp_begin=`echo $exp_data | cut -c$(echo $LEN + 1|bc -l)-`
  MONTH=${exp_begin:2:2}
  YEAR_CI=${exp_name:0:2}
  YEAR=${exp_begin:0:2}

  if [ $YEAR -le $YEAR_CI ]
  then
    YEAR=$(echo $YEAR + 100 | bc -l)
  fi

  if [ $YEAR_CI -eq 05 ]
  then
    YEAR=$(echo $YEAR + 2000 | bc -l)
  else
    YEAR=$(echo $YEAR + 1900 | bc -l)
  fi

  ./submit_nodes -s ${YEAR}/${MONTH} -e ${YEAR}/${MONTH} $ARCHIVE_OCEAN/$(decode_cmip5_name $exp_name)/CGCM/ $WORK_HOME/saida_cmip5/
done
