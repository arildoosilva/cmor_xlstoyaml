# -*- coding: utf-8 -*-
import yaml
import sys
import getopt
import os
import fileCheck
import getVariables

# vars
inpath = None
outpath = None
table_prefix = 'CMIP5_'
tables = []


# defs
def getArgs(argv):
    help = ('This script will generate yaml files from CMOR tables\n'
            'Modules used: pyyaml, sys, getopt, os')

    # prints the help text when -h or --help is used
    try:
        opts, args = getopt.getopt(argv, 'h', ['help'])
    except get.GetoptError:
        print(help)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(help)
            sys.exit()

    global inpath
    global outpath

    if len(sys.argv) < 3:
        print('Missing parameters\n')
        sys.exit(2)
    else:
        inpath = sys.argv[1]
        outpath = sys.argv[2]


# reads the inpath directory
def readIn(inpath):
    global tables
    global table_prefix
    for (dirpath, dirnames, filenames) in os.walk(inpath):
        for f in filenames:
            if (table_prefix in f):
                print("Adding file " + f + " to list")
                tables.append(f)


def clearOut(outpath):
    os.system('rm ' + outpath + "\/*")


def writeOut(inpath, outpath, tables):
    data = dict(
        A='a',
        B=dict(
            C='c',
            D='d',
            E='e'
        )
    )
    for item in tables:
        filename = outpath + "/" + item[6:] + ".yaml"
        print("Writing file " + filename)
        with open(filename, "w") as outfile:
            outfile.write(yaml.dump(data, default_flow_style=False))


def writeDescription(inpath, outpath, tables):
    data = dict(
        description=dict(
            outpath = "'/stornext/online13/ocean/simulations/CMIP'",
            experiment_id = "'decadal1960'",
            institution = "'INPE'",
            source = "'BESM-OA2.5.1 2014 atmosphere: CPTEC (T62L28); ocean: MOM (mom4p1_pubrel_18dec2009, 0.25-2xL50); land: SSIB'",
            calendar = "'julian'",
            realization = 1,
            contact = "'Dr. Paulo Nobre <paulo.nobre@cptec.inpe.br>'",
            history = "",
            comment = "",
            references = "",
            #leap_year =
            #leap_month =
            #month_lengths =
            model_id = "'BESM-OA2.5.1'",
            forcing = "'GHG, Sl'",
            initialization_method = 1,
            physics_version = 1,
            institute_id = "'INPE'",
            parent_experiment_id = "'N/A'",
            branch_time = 0.0,
            parent_experiment_rip = "'N/A'",
        )
    )
    for item in tables:
        filename = outpath + "/" + item[6:] + ".yaml"
        print("Writing file " + filename)
        with open(filename, "w") as outfile:
            outfile.write(yaml.dump(data, default_flow_style=False))
        outfile.close()
        for x in range(0, 2):
            fileCheck.check(filename)  # fixes some strings in the yaml files


# main
if __name__ == "__main__":
    getArgs(sys.argv[0:])
    readIn(inpath)
    #clearOut(outpath)
    #writeDescription(inpath, outpath, tables)
    getVariables.readTables(inpath, outpath, tables)
    #writeOut(inpath, outpath, tables)
    # for item in tables:
    #     print(item)
