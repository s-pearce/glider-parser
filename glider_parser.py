#!/usr/bin/env python

"""
@package glider_parser.py
@file glider_parser.py
@author Stuart Pearce & Chris Wingard
@brief Module containing parser scripts for glider data set agents
"""
__author__ = 'Stuart Pearce & Chris Wingard'
__license__ = 'Apache 2.0'
import numpy as np
import warnings
import pdb

from mi.core.exceptions import InstrumentException

from mi.core.common import BaseEnum
from mi.core.instrument.data_particle import DataParticle
from mi.core.instrument.data_particle import DataParticleKey


class GliderParsedData(object):
    """
    A class that parses a glider data file and holds it in dictionaries.

    GliderParsedData parses a Slocum Electric Glider data file that has
    been converted to ASCII from binary, and holds the self describing
    header data in a header dictionary and the data in a data dictionary
    using the column labels as the dictionary keys.

    Construct an instance of GliderParsedData using the filename of the
    ASCII file containing the glider data.
    E.g.:
        glider_data = GliderParsedData('glider_data_file.mbd')

    glider_data.hdr_dict holds the header dictionary with the self
    describing ASCII tags from the file as keys.
    data_dict holds a data dictionary with the variable names (column
    labels) as keys.
    A sub-dictionary holds the name of the variable (same as the key),
    the data units, the number of binary bytes used to store each
    variable type, the name of the variable, and the data using the
    keys:
    'Name'
    'Units'
    'Number_of_Bytes'
    'Data'

    For example, to retrieve the data for 'variable_name':
        vn_data = glider_data.data_dict['variable_name]['Data']
    """

    def __init__(self, filename):
        self._fid = open(filename, 'r')
        self.hdr_dict = {}
        self.data_dict = {}
        self._read_header()
        self._read_data()
        self._fid.close()

    def _read_header(self):
        """
        Read in the self describing header lines of an ASCII glider data
        file.
        """
        # There are usually 14 header lines, start with 14,
        # and check the 'num_ascii_tags' line.
        num_hdr_lines = 14
        hdr_line = 1
        while hdr_line <= num_hdr_lines:
            line = self._fid.readline()
            split_line = line.split()
            if 'num_ascii_tags' in split_line:
                num_hdr_lines = int(split_line[1])
            self.hdr_dict[split_line[0][:-1]] = split_line[1]
            hdr_line += 1

    def _read_data(self):
        """
        Read in the column labels, data type, number of bytes of each
        data type, and the data from an ASCII glider data file.
        """
        column_labels = self._fid.readline().split()
        column_type = self._fid.readline().split()
        column_num_bytes = self._fid.readline().split()

        # read each row of data & use np.array's ability to grab a
        # column of an array
        data = []
        for line in self._fid.readlines():
            data.append(line.split())
        data_array = np.array(data)  # NOTE: this is an array of strings

        # warn if # of described data rows != to amount read in.
        num_columns = int(self.hdr_dict['sensors_per_cycle'])
        if num_columns != data_array.shape[1]:
            warnings.warn('Glider data file does not have the same' +
                          'number of columns as described in header.\n' +
                          'described %d, actual %d' % (num_columns,
                                                       data_array.shape[1])
                          )

        # extract data to dictionary
        for ii in range(num_columns):
            self.data_dict[column_labels[ii]] = {
                'Name': column_labels[ii],
                'Units': column_type[ii],
                'Number_of_Bytes': int(column_num_bytes[ii]),
                'Data': data_array[:, ii]
            }
        self.data_keys = column_labels


########################################################################
# Example code for a possible way to create the data particles from a
# GliderParsedData instance
########################################################################

class CtdDataParticleKey(BaseEnum):
    IS_INSTALLED = 'sci_ctd41cp_is_installed'
    CTD_TIMESTAMP = 'sci_ctd41cp_timestamp'
    COND = 'sci_water_cond'
    PRESS = 'sci_water_pressure'
    TEMP = 'sci_water_temp'
    SECS_INTO_MISSION = 'sci_m_present_secs_into_mission'
    PRESENT_TIME = 'sci_m_present_time'


class CtdDataParticle(DataParticle):
    _data_particle_type = 'GLIDER_CTD_DATA_PARTICLE'

    def build_parsed_values(self, gpd):
        """
        Takes a GliderParsedData object and extracts CTD data from the
        data dictionary and puts the data into a CTD Data Particle.

        @param gpd A GliderParsedData class instance.
        @param result A returned list with sub dictionaries of the data
        """
        if not isinstance(gpd, GliderParsedData):
            raise GliderObjectException(
                "Object Instance is not a GliderParsedData object")

        result = []
        for key in CtdDataParticleKey.list():
            result.append({
                DataParticleKey.VALUE_ID: key,
                DataParticleKey.VALUE: gpd.data_dict[key]['Data']})


# this needs to change to the Data set base exception when there is one.
class GliderObjectException(InstrumentException):
    """ Expects a GliderParsedData instance."""
