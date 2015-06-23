#!/usr/bin/env python

import subprocess
import glob
import locale
locale.setlocale(locale.LC_ALL, "")

TOTAL_SIZE = 1921986052

#for exp in glob.glob('/stornext/online14/ocean/cmip5_send/output/INPE/BESM-OA2-3/decadal*'):
for exp in glob.glob('/stornext/online14/ocean/cmip5_send/output/INPE/BESM-OA2-3/decadal1960/'):
    output = subprocess.check_output(['du', '--max-depth=1', exp])

    data = {}
    for line in output.split('\n'):
        if line:
            size, path = line.split('\t') 
            path = path.split('/')[-1] 
            if 'decadal' not in path:
                data[path] = int(size.strip())
    print data

    smallest_comb = None
    smallest = None

    sum_all = sum(data.values())
    for key in data:
        part_sum = sum_all - data[key] 
        if not smallest_comb:
            smallest = TOTAL_SIZE - part_sum
            smallest_comb = key

        result = TOTAL_SIZE - part_sum
        #print 'minus', key, ':', locale.format('%d', result, True)
     
        if result < smallest and result > 0:
            smallest = TOTAL_SIZE - part_sum
            smallest_comb = key

    print exp
    print 'smallest:', smallest_comb, locale.format('%d', smallest, True) 
    print
