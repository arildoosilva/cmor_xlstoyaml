#!/stornext/online2/ocean/software/Envs/science/bin/python
# Author: Beto
import os
import sys
import glob
import commands
import re

import numpy as np
from pupynere import netcdf_file
import cmor
from yaml import load
from coards import to_udunits, from_udunits

import datetime

# signature is $PYTHON $SCRIPT/ocean.py $NAME $IC $PHYSICS $SCRIPT/$TABLE $YYYY $MONTH $OUTPATH
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


TABLES = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), 'Tables'))
TIME = 'days since %d-01-01 00:00:00' % year
MISSING = 1.e+20


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


# Get the time frequency based on the table name
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
    if config['variables'][var]['realm'] not in ['ocean', 'seaIce']:
        continue
    filename = '%(outpath)s/CMIP5/output/INPE/BESM-OA2.3.1/%(exp)s/%(freq)s/%(realm)s/%(var)s/r%(realization)di1p%(physics)d/%(var)s_%(table)s_BESM-OA2-3-1_%(exp)s_r%(realization)di1p%(physics)d_%(year)04d%(month)02d*-%(year)04d%(month)02d*.nc' % dict(
            outpath=config['description']['outpath'],
            exp=exp,
            freq=freq,
            realm=config['variables'][var]['realm'],
            var=config['variables'][var]['CMOR variable name'],
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

# read data from netcdf
mm = month
yyyy = year
if freq in ['mon', 'monClim']: 
    mm = (month % 12) + 1  # get next month
    if mm == 1:
        yyyy += 1
filename = "cgcm2.2_CMIP5_%s_%04d_%02d.nc" % (os.path.splitext(os.path.split(table)[1])[0], yyyy, mm)
print 'Opening %s' % filename
inp = netcdf_file(filename)

time = [ from_udunits(value, inp.variables['time'].units) for value in inp.variables['time'][:] ]
time = np.array([ to_udunits(v, TIME) for v in time ])
if 'time_bounds' in inp.variables:
    bounds = np.concatenate((inp.variables['time_bounds'][:,0], inp.variables['time_bounds'][-1:,1]), axis=0)
    bounds = [ from_udunits(value, inp.variables['time'].units) for value in bounds ]
    bounds = np.array([ to_udunits(v, TIME) for v in bounds ])
else:
    bounds = None

# now save data
start_for_variable = datetime.datetime.now()
for variable in config['variables'].values():
    start_this_variable = datetime.datetime.now()
    if variable['realm'] in ['ocean', 'seaIce']:
        if variable['output variable name'] == 'thetao':
            temp_salt_file = 'cgcm2.2_tempsalt_%04d_%02d.nc' % (year, month)
            f = netcdf_file(temp_salt_file)
            data = np.ma.masked_values(
                    f.variables['temp'][:], f.variables['temp'].missing_value)
            data = np.ma.masked_values(data, 9.9692e+36)
        elif variable['output variable name'] == 'thetaoga':
            temp_salt_file = 'cgcm2.2_tempsalt_%04d_%02d.nc' % (year, month)
            f = netcdf_file(temp_salt_file)
            data = np.ma.masked_values(
                    f.variables['temp'][:], f.variables['temp'].missing_value)
            data = np.ma.masked_values(data, 9.9692e+36)
            while len(data.shape) > 1:
                data = np.ma.mean(data, axis=1)
        elif variable['output variable name'] == 'omldamax' and freq == 'mon':
            f = netcdf_file('cgcm2.2_CMIP5_day_%04d_%02d.nc' % (year, month))
            data = np.ma.masked_values(
                    f.variables['omldamax'][:], f.variables['omldamax'].missing_value)
            data = np.ma.mean(data, axis=0)
            data.shape = (1,) + data.shape
        else:
            f = inp
            data = np.ma.masked_values(
                    f.variables[ variable['output variable name'] ][:],
                    f.variables[ variable['output variable name'] ].missing_value)

        # fix units
        data = adjust_units(
                variable['units in BMGCS'], variable['desired units'],
                data)

        print variable['output variable name']

        # setup output file
        cmor.setup(inpath=TABLES, netcdf_file_action=cmor.CMOR_REPLACE)
        cmor.dataset( **config['description'] )
        cmor.load_table( variable['table'] )

        axis_ids = []
        if 'time' in variable['CMOR dimensions']:
            itime = cmor.axis(table_entry='time', units=TIME, coord_vals=time, cell_bounds=bounds)
            axis_ids.append(itime)
        elif 'time1' in variable['CMOR dimensions']:
            itime = cmor.axis(table_entry='time1', units=TIME, coord_vals=time, cell_bounds=None)
            axis_ids.append(itime)
        elif 'time2' in variable['CMOR dimensions']:
            itime = cmor.axis(table_entry='time2', units=TIME, coord_vals=time, cell_bounds=bounds)
            axis_ids.append(itime)
        if 'olevel' in variable['CMOR dimensions']:
            levels = f.variables['st_ocean'][:].astype('f')
            levelsb = f.variables['st_edges_ocean'][:].astype('f')
            ilevels = cmor.axis(table_entry='olevel', units=f.variables['st_ocean'].units, coord_vals=levels, cell_bounds=levelsb)
            axis_ids.append(ilevels)
        if 'latitude' in variable['CMOR dimensions']:
            if variable['output variable name'] == 'thetao':
                name = f.variables['temp'].dimensions[-2]
            else:
                name = f.variables[ variable['output variable name'] ].dimensions[-2]
            lat = f.variables[name][:].astype('f')
            if name in ['yv']:
                latb = f.variables['yb'][:].astype('f')
            else:
                latb = get_bounds(lat)
            ilat = cmor.axis(table_entry='latitude', units='degrees_north', coord_vals=lat, cell_bounds=latb)
            axis_ids.append(ilat)
        if 'longitude' in variable['CMOR dimensions']:
            if variable['output variable name'] == 'thetao':
                name = f.variables['temp'].dimensions[-1]
            else:
                name = f.variables[ variable['output variable name'] ].dimensions[-1]
            lon = f.variables[name][:].astype('f')
            if name in ['xv']:
                lonb = f.variables['xb'][:].astype('f')
            else:
                lonb = get_bounds(lon)
            ilon = cmor.axis(table_entry='longitude', units='degrees_east', coord_vals=lon, cell_bounds=lonb)
            axis_ids.append(ilon)

        # fix some variables
        if variable['output variable name'] == 'sic':
            data = np.ma.sum(data, axis=1)  # sum over ct

        data = data.filled(MISSING).astype('f')

        if freq in ['mon', 'monClim']:
            if not data.shape[0] == 1:
                data.shape = (1,) + data.shape
            data = np.concatenate((data, data), axis=0)

        varid = cmor.variable(variable['CMOR variable name'], variable['units'], axis_ids, positive=variable.get('positive'), comment=variable.get('comment'), missing_value=MISSING)
        cmor.write(varid, data)
        path = cmor.close(varid, file_name=True)
    end_this_variable = datetime.datetime.now()
    print "####prof time for: ", variable, end_this_variable - start_this_variable
print "####prof time for all: ", datetime.datetime.now() - start_for_variable
