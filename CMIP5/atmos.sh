# Author: Beto

LD_LIBRARY_PATH=/stornext/online2/ocean/software/uuid-1.6.2/lib:/stornext/online2/ocean/software/udunits-2.1.24/lib
PYTHON=/stornext/online2/ocean/software/Envs/science/bin/python
SCRIPT=/stornext/online2/ocean/software/CMIP5

FIXED="cmp034 cmp038 cmp042"
MAUNA="cmp035 cmp039 cmp043"
RCP45="cmp036 cmp040 cmp044"
RCP85="cmp037 cmp041 cmp045"
TABLES="Amon.yaml 3hr.yaml 6hrLev.yaml 6hrPlev.yaml LImon.yaml Lmon.yaml day.yaml"

EXP=`pwd | cut -d '/' -f6`
YEAR=`pwd | cut -d '/' -f9 | cut -c 3-`
IC=`pwd | cut -d '/' -f10`
if [[ $MAUNA =~ $EXP ]]; then PHYSICS=1; fi
if [[ $FIXED =~ $EXP ]]; then PHYSICS=2; fi
if [[ $RCP45 =~ $EXP ]]; then PHYSICS=3; fi
if [[ $RCP85 =~ $EXP ]]; then PHYSICS=4; fi
#PHYSICS=`[[ $FIXED =~ $EXP ]] && echo '2' || [[ $MAUNA =~ $EXP ]] && echo '1' || [[ $RCP45 =~ $EXP ]] && echo '3' || [[ $RCP85 =~ $EXP ]] && echo '4'`
DURATION=`[[ "cmp034 cmp035 cmp036 cmp037 cmp038 cmp039 cmp040 cmp041 cmp042 cmp043 cmp044 cmp045" =~ $EXP ]] && echo '100' || echo '30'`

echo "This is experiment $EXP, starting on $IC/12/$YEAR for $DURATION years."
echo "Physics used is $PHYSICS (1 is Mauna Loa, 2 is constant CO2, 3 is RCP4.5, 4 is RCP8.5)."

START=$[$YEAR+1]
END=$[$YEAR+$DURATION]
NAME=decadal${YEAR}
for YYYY in `seq -w $START $END`; do
    for MONTH in `seq -w 1 12`; do 
        for TABLE in $TABLES; do
            echo "Processing table $TABLE for $YYYY/$MONTH."
            $PYTHON $SCRIPT/atmos.py $NAME $IC $PHYSICS $SCRIPT/$TABLE $YYYY $MONTH
        done
    done
done
