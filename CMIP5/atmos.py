#!/stornext/online2/ocean/software/Envs/science/bin/python
# Author: Beto
import os
import sys
import glob
import commands
import re

import numpy as np
import ctler
import cmor
from yaml import load
from coards import to_udunits, from_udunits


import datetime

# signature is $PYTHON $SCRIPT/process.py $NAME $IC $PHYSICS $SCRIPT/$TABLE $YYYY $MONTH $OUTPATH
exp = sys.argv[1]
realization = int(sys.argv[2])
physics = int(sys.argv[3])
table = sys.argv[4]
year = int(sys.argv[5])
month = int(sys.argv[6])
try:
    outpath = sys.argv[7]
except IndexError:
    outpath = None

files = glob.glob("GPOSNMC*%04d%02d????C.fct.TQ0062L028.ctl" % (year, month))
files.sort()
print 'Found %d files to process.' % len(files)

TABLES = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), 'Tables'))
TIME = 'days since %d-01-01 00:00:00' % year


def get_bounds(axis):
    bounds = np.zeros((len(axis)+1,), 'd')
    bounds[1:-1] = (axis[1:] + axis[:-1])/2.
    bounds[0] = (3*axis[0] - axis[1])/2.0
    bounds[-1] = (3*axis[-1] - axis[-2])/2.0
    return bounds


def adjust_units(source, target, data):
    if source == target:
        return data

    try:
        out = commands.getoutput('/scratchin/grupos/ocean/home/ocean/software/units-1.88/bin/units "%s" "%s"' % (source, target))
        factor = float(out[3:].split()[0])
        return data * factor
    except:
        if source == "kg/m2/day" and target == "kg/m2":
            return np.cumsum(data/8., axis=0)
        elif source == "mbar-1000" and target == "Pa":
            return (data+1000)*100
        else:
            raise Exception('Unable to parse units "%s" to "%s"!' % (source, target))


def average_data(data, n):
    shape = data.shape
    t = shape[0]
    rest = shape[1:]
    data = np.mean(data.reshape(t/n, n, -1), axis=1)
    data.shape = (t/n,) + rest
    return data


config = load(open(table).read())
config['description']['experiment_id'] = exp
config['description']['realization'] = realization
config['description']['physics_version'] = physics
if outpath:
    config['description']['outpath'] = outpath

freq = {
        '3hr.yaml': '3hr',
        '6hrLev.yaml': '6hr',
        '6hrPlev.yaml': '6hr',
        'Amon.yaml': 'mon',
        'Omon.yaml': 'mon',
        'OImon.yaml': 'mon',
        'Oclim.yaml': 'monClim',
        'LImon.yaml': 'mon',
        'Lmon.yaml': 'mon',
        'day.yaml': 'day',
}[os.path.split(table)[1]]

# check if we have work to do
for var in config['variables']:
    if config['variables'][var]['realm'] not in ['atmos', 'land']:
        continue
    filename = '%(outpath)s/CMIP5/output/INPE/BESM-OA2.3.1/%(exp)s/%(freq)s/%(realm)s/%(var)s/r%(realization)di1p%(physics)d/%(var)s_%(table)s_BESM-OA2-3-1_%(exp)s_r%(realization)di1p%(physics)d_%(year)04d%(month)02d*-%(year)04d%(month)02d*.nc' % dict(
            outpath=config['description']['outpath'],
            exp=exp,
            freq=freq,
            realm=config['variables'][var]['realm'],
            var=var,
            realization=realization,
            physics=physics,
            table=os.path.splitext(os.path.split(table)[1])[0],
            year=year,
            month=month)
    if not glob.glob(filename):
        print 'Missing file %s.' % filename
        break
else:
    print 'All files processed, skipping!'
    sys.exit()

if not os.path.exists(config['description']['outpath']):
    os.mkdir(config['description']['outpath'])

# read data from ctls
vars = dict((variable['output variable name'], []) for variable in config['variables'].values())
n = len(files)
bounds = []
print 'Reading %d files into memory...' % n
for i, filename in enumerate(files):
    f = ctler.CTLReader(filename)
    for variable in config['variables'].values():
        if variable['realm'] in ['atmos', 'land']:
            vars[ variable['output variable name'] ].append(
                    adjust_units(variable['units in BMGCS'], variable['desired units'],
                        f.variables[ variable['name in BMGCS'].upper() ][:]))
    bounds.append(f.variables['time'][0])

lat = f.variables['latitude'][:]
lon = f.variables['longitude'][:]
levels = f.variables['levels'][:] * 100.

dt = (bounds[1] - bounds[0])
bounds.append(bounds[-1] + dt)
bounds = np.array([ to_udunits(v, TIME) for v in bounds ])
time = (bounds[:-1] + bounds[1:])/2.

# now save data
start_for_variable = datetime.datetime.now()
for variable in config['variables'].values():
    start_this_variable = datetime.datetime.now()
    if variable['realm'] in ['atmos', 'land']:
        data = np.concatenate(vars[ variable['output variable name'] ], axis=0)
        print variable['output variable name']

        # setup output file
        cmor.setup(inpath=TABLES, netcdf_file_action=cmor.CMOR_REPLACE)
        cmor.dataset( **config['description'] )
        cmor.load_table( variable['table'] )

        cell_methods = variable['cell_methods'] or ''
        if re.search('3hr', variable['table']):
            #if not re.match('time:\s*mean', cell_methods):
            #    bounds = None
            time_ = time
            bounds_ = bounds
        elif re.search('6hr', variable['table']):
            if re.match('time:\s*mean', cell_methods):
                data = average_data(data, 2)
                time_ = average_data(time, 2)
                bounds_ = bounds[::2]
            else:
                data = data[::2]  # sample every 6hr
                time_ = time[::2]
                bounds_ = None
        elif re.search('day', variable['table']):
            if re.match('time:\s*mean', cell_methods):
                data = average_data(data, 8)
                time_ = average_data(time, 8)
                bounds_ = bounds[::8]
            else:
                data = data[::8] 
                time_ = time[::8]
                bounds_ = None
        elif re.search('mon', variable['table']):
            if re.match('time:\s*mean', cell_methods):
                if (28*8) <= data.shape[0] <= (31*8):
                    data = np.mean(data, axis=0)
                    # replicate data because it expects more than one value, since
                    # we're processing one month at a time.
                    data.shape = (1,) + data.shape
                    data = np.concatenate((data, data), 0)
                    time_ = np.array([np.mean(time)])
                    bounds_ = np.array([bounds[0], bounds[-1]])
                else:
                    out = np.empty((12,) + data.shape[1:], 'f')
                    bounds_ = []
                    for l in range(12):
                        valid = np.array([ from_udunits(v, TIME).month == l+1 for v in time ], bool)
                        out[l] = np.mean(data[valid], axis=0)
                        bounds_.append(bounds[valid][0])
                    data = out
                    bounds_.append(bounds[-1])
                    bounds_ = np.array(bounds_)
                    time_ = (bounds_[:-1] + bounds_[1:])/2.

        axis_ids = []
        if 'height2m' in variable['CMOR dimensions']:
            ilevels = cmor.axis(table_entry='height2m', units='m', coord_vals=[2.])
            axis_ids.append(ilevels)
        elif 'height10m' in variable['CMOR dimensions']:
            ilevels = cmor.axis(table_entry='height10m', units='m', coord_vals=[10.])
            axis_ids.append(ilevels)
        if 'time' in variable['CMOR dimensions']:
            itime = cmor.axis(table_entry='time', units=TIME, coord_vals=time_, cell_bounds=bounds_)
            axis_ids.append(itime)
        elif 'time1' in variable['CMOR dimensions']:
            itime = cmor.axis(table_entry='time1', units=TIME, coord_vals=time_, cell_bounds=None)
            axis_ids.append(itime)
        if 'plevs' in variable['CMOR dimensions']:
            plevs = [100000, 92500, 85000, 70000, 60000, 50000, 40000, 30000, 25000, 20000, 15000, 10000, 7000, 5000, 3000, 2000, 1000,]
            ilevels = cmor.axis(table_entry='plevs', units='Pa', coord_vals=plevs)
            axis_ids.append(ilevels)
            indices = np.array([ level in plevs for level in levels ], bool)
            data = data[...,indices,:,:]
        elif 'plev8' in variable['CMOR dimensions']:
            plev8 = [100000, 85000, 70000, 50000, 25000, 10000, 5000, 1000,]
            ilevels = cmor.axis(table_entry='plev8', units='Pa', coord_vals=plev8)
            axis_ids.append(ilevels)
            indices = np.array([ level in plev8 for level in levels ], bool)
            data = data[...,indices,:,:]
        elif 'plev3' in variable['CMOR dimensions']:
            plev3 = [85000, 50000, 25000,]
            ilevels = cmor.axis(table_entry='plev3', units='Pa', coord_vals=plev3)
            axis_ids.append(ilevels)
            indices = np.array([ level in plev3 for level in levels ], bool)
            data = data[...,indices,:,:]
        elif 'alevel' in variable['CMOR dimensions']:
            ilevels = cmor.axis(table_entry='alevel', units='Pa', coord_vals=levels)
            axis_ids.append(ilevels)
        if 'latitude' in variable['CMOR dimensions']:
            lat = f.variables['latitude'][:]
            ilat = cmor.axis(table_entry='latitude', units='degrees_north', coord_vals=lat, cell_bounds=get_bounds(lat))
            axis_ids.append(ilat)
        if 'longitude' in variable['CMOR dimensions']:
            lon = f.variables['longitude'][:]
            ilon = cmor.axis(table_entry='longitude', units='degrees_east', coord_vals=lon, cell_bounds=get_bounds(lon))
            axis_ids.append(ilon)

        # fix some variables
        if variable['output variable name'] == 'clwvi' and len(data.shape) == 4 and len(axis_ids) == 3:
            data = np.mean(data, axis=1)  # percent integrated over the column

        varid = cmor.variable(variable['output variable name'], variable['units'], axis_ids, positive=variable.get('positive'), comment=variable.get('comment'))
        cmor.write(varid, data)
        path = cmor.close(varid, file_name=True)
    end_this_variable = datetime.datetime.now()
    print "####prof time for: ", variable, end_this_variable - start_this_variable
print "####prof time for all: ", datetime.datetime.now() - start_for_variable
