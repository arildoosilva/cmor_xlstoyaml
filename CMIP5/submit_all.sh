#!/bin/bash -eu

DIR_IN=$(readlink -e $1)

DIR_TEST=$(find "$DIR_IN"/dataout/ic12/ic*/?? -maxdepth 0 -type d|head)
if [ "" = "$DIR_TEST" ]
then
  echo "Wrong dir structure"
  exit 1
fi

for ic in $(find $DIR_IN/dataout/ic12 -maxdepth 1 -name "ic*" -type d| sort)
do
  for member in $(find -L $ic -maxdepth 1 -name "??" -type d| sort)
  do
      ./submit_aux $member/atmos/CGCM
      ./submit_aux $member/ocean/CGCM
  done
done
