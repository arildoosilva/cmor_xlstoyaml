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

TABLES = 'Tables'
TIME = 'days since 2005-01-01 00:00:00'

import datetime

def get_bounds(axis):
    bounds = np.zeros((len(axis)+1,), 'd')
    bounds[1:-1] = (axis[1:] + axis[:-1])/2.
    bounds[0] = (3*axis[0] - axis[1])/2.0
    bounds[-1] = (3*axis[-1] - axis[-2])/2.0
    return bounds


def adjust_units(source, target):
    out = commands.getoutput('units "%s" "%s"' % (source, target))
    factor = float(out[3:].split()[0])
    return factor


def average_data(data, n):
    shape = data.shape
    t = shape[0]
    rest = shape[1:]
    data = np.mean(data.reshape(t/n, n, -1), axis=1)
    data.shape = (t/n,) + rest
    return data


filename = sys.argv[1]
config = load(open(filename).read())

if not os.path.exists('cmip5'):
    os.mkdir('cmip5')

start_for_variable = datetime.datetime.now()
for variable in config['variables'].values():
    start_this_variable = datetime.datetime.now()
    if variable['realm'] in ['atmos', 'land', 'landIce land']:
        # setup output file
        cmor_setup_start = datetime.datetime.now()
        cmor.setup(inpath=TABLES, netcdf_file_action=cmor.CMOR_REPLACE)
        cmor.dataset( **config['description'] )
        cmor.load_table( variable['table'] )
        print "####prof cmor setup", datetime.datetime.now() - cmor_setup_start

        # read ctls
        files = glob.glob('*.ctl')
        n = len(files)
        bounds = []
        data = []
        for i, filename in enumerate(files):
            f = ctler.CTLReader(filename)
            values = f.variables[ variable['name in BMGCS'].upper() ][:]
            data.append(values * adjust_units(variable['units in BMGCS'], variable['desired units']))
            bounds.append(f.variables['time'][0])
        data = np.concatenate(data, axis=0)
        dt = (bounds[1] - bounds[0])
        #bounds.insert(0, bounds[0] - dt )
        bounds.append(bounds[-1] + dt)
        bounds = np.array([ to_udunits(v, TIME) for v in bounds ])
        time = (bounds[:-1] + bounds[1:])/2.
        levels = f.variables['levels'][:] * 100.

        cell_methods = variable['cell_methods'] or ''
        if re.search('3hr', variable['table']):
            if not re.match('time:\s*mean', cell_methods):
                bounds = None
        elif re.search('6hr', variable['table']):
            if re.match('time:\s*mean', cell_methods):
                data = average_data(data, 2)
                time = average_data(time, 2)
                bounds = bounds[::2]
            else:
                data = data[::2]  # sample every 6hr
                time = time[::2]
                bounds = None
        elif re.search('day', variable['table']):
            if re.match('time:\s*mean', cell_methods):
                data = average_data(data, 8)
                time = average_data(time, 8)
                bounds = bounds[::8]
            else:
                data = data[::8] 
                time = time[::8]
                bounds = None
        elif re.search('mon', variable['table']):
            if re.match('time:\s*mean', cell_methods):
                data = np.mean(data, axis=0)
                # replicate data because it expects more than one value, since
                # we're processing one month at a time.
                data.shape = (1,) + data.shape
                data = np.concatenate((data, data), 0)
                time = np.array([np.mean(time)])
                bounds = np.array([bounds[0], bounds[-1]])

        axis_ids = []
        if 'height2m' in variable['CMOR dimensions']:
            ilevels = cmor.axis(table_entry='height2m', units='m', coord_vals=[2.])
            axis_ids.append(ilevels)
        elif 'height10m' in variable['CMOR dimensions']:
            ilevels = cmor.axis(table_entry='height10m', units='m', coord_vals=[10.])
            axis_ids.append(ilevels)
        if 'time' in variable['CMOR dimensions']:
            itime = cmor.axis(table_entry='time', units=TIME, coord_vals=time, cell_bounds=bounds)
            axis_ids.append(itime)
        elif 'time1' in variable['CMOR dimensions']:
            itime = cmor.axis(table_entry='time1', units=TIME, coord_vals=time, cell_bounds=None)
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
            indices = np.array([ level in plev8 for level in levels ], bool)
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

        cmor_write_start = datetime.datetime.now()
        varid = cmor.variable(variable['output variable name'], variable['units'], axis_ids)
        cmor.write(varid, data)
        path = cmor.close(varid, file_name=True)
        print "####prof cmor write", datetime.datetime.now() - cmor_write_start
    print "####prof this variable (including cmor)", variable, datetime.datetime.now() - start_this_variable
print "####prof time for all", datetime.datetime.now() - start_for_variable
