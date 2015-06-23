# -*- coding: utf-8 -*-
import re
import yaml

inpath = None
outpath = None
yamltable = None

def makeDict(variable_entry):
    variable_holder = []  # holds the list after the regex is applied
    variable = ""
    variable_entry = variable_entry.split('\n')
    variable_entry = [x for x in variable_entry if not x.startswith(('!', ':'))]
    for line in variable_entry:
        line = re.sub(' +', ' ', line)
        #print((line.partition(' ')[0]).replace(':', ' - ') + line.partition(' ')[2])
        linekey = (line.partition(' ')[0]).replace(':', ' - ')
        linevalue = line.partition(' ')[2]
        line = linekey + linevalue
        variable_holder.append(re.sub(' +', ' ', line))
    variable_holder = filter(None, variable_holder)
    #print(variable_holder)
    for line in variable_holder:
        variable += (line + ", " )
    variable = variable[:-2]
    print(variable)
    #variable = dict(e.split(' - ') for e in variable.split(', '))
    #print(yaml.dump(variable, default_flow_style=False))


def getTheSentences(infile):
    """ Uses regex to find the variables in every file, then
    send each variable to makeDict
    """
    with open(infile) as fp:
        for variable_entry in re.findall('variable_entry(.*?)variable_entry', fp.read(), re.S):
            makeDict(variable_entry)
            break  # DELETE test with one var


def readTables(inpath, outpath, tables):
    """ Reads the table list and send each file from the list to the
    getTheSentences def
    """
    for item in tables:
        global yamltable
        yamltable = item
        print(item + "\n")
        filename = inpath + '/' + item
        getTheSentences(filename)
        break  # DELETE test with one file
