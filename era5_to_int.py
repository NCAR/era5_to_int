#!/usr/bin/env python3

class SnowDiags:
    """ Implements the computation of SNOW (water equivalent snow depth) and
    SNOWH (physical snow depth) from ERA5 RSN (water equivalent snow depth)
    and SD (snow density) fields.
    """

    def __init__(self):
        self.snow_den = None
        self.snow_ec = None

    def consider(self, field, xlvl, proj, hdate, slab, intfile):
        """ Considers whether a given field may be used in the computation
        of SNOW or SNOWH. When all available information has been acquired, this
        method computes these two fields and writes them to the output
        intermediate file.
        """

        if field == 'SNOW_DEN' and xlvl == 200100.0:
            self.snow_den = slab
        elif field == 'SNOW_EC' and xlvl == 200100.0:
            self.snow_ec = slab
        else:
            return

        if self.snow_den is not None and self.snow_ec is not None:
            print('Computing SNOWH and SNOW')
            snow = self.snow_ec * 1000.0
            snowh = snow / self.snow_den

            write_slab(intfile, snow, 200100.0, proj, 'SNOW', hdate, 'kg m**-2',
                'ERA5 reanalysis grid', 'Water equivalent snow depth')
            write_slab(intfile, snowh, 200100.0, proj, 'SNOWH', hdate, 'm',
                'ERA5 reanalysis grid', 'Physical snow depth')

            self.snow_den = None
            self.snow_ec = None


class RH2mDiags:
    """ Implements the computation of RH (relative humidity in % at the surface)
    from ERA5 VAR_2T (2m temperature) and VAR_2D (2m dewpoint) fields.
    """

    def __init__(self):
        self.t = None
        self.td = None

    def consider(self, field, xlvl, proj, hdate, slab, intfile):
        """ Considers whether a given field may be used in the computation
        of RH at the surface. When all available information has been acquired,
        this method computes the RH field and writes it to the output
        intermediate file.
        """

        if field == 'TT' and xlvl == 200100.0:
            self.t = slab
        elif field == 'DEWPT' and xlvl == 200100.0:
            self.td = slab
        else:
            return

        if self.t is not None and self.td is not None:
            print('Computing RH at 200100.0')

            Xlv = 2.5e6
            Rv = 461.5
            rh2 = np.exp(Xlv/Rv*(1.0/self.t - 1.0/self.td)) * 1.0e2

            write_slab(intfile, rh2, 200100.0, proj, 'RH', hdate, '%',
                'ERA5 reanalysis grid', 'Relative humidity')

            self.t = None
            self.td = None


class RHDiags:
    """ Implements the computation of RH (relative humidity in % at pressure level)
    from ERA5 T (temperature) and Q (specific humidity) fields at a corresponding
    pressure level.
    """

    def __init__(self):
        self.savefields = {}

    def liquidSaturationVaporMixRatio(self, t, p):
        """ Based on the RSLF function from the Thompson microphysics scheme in WRF
        Compute the saturation vapor mixing ratio with respect to liquid water.
        """

        t0 = 273.16
        C0= .611583699E03
        C1= .444606896E02
        C2= .143177157E01
        C3= .264224321E-1
        C4= .299291081E-3
        C5= .203154182E-5
        C6= .702620698E-8
        C7= .379534310E-11
        C8=-.321582393E-13

        t_bounded =np.maximum(-80.0, t - t0)
        # Simplified calc of saturation vapor pressure
        # esL = 612.2 * np.exp(17.67 * t_bounded / (self.t-29.65))
        # esL with coefficients used instead
        esL = (C0 + t_bounded
                * (C1 + t_bounded
                  * (C2 + t_bounded
                    * (C3 + t_bounded
                      * (C4 + t_bounded
                        * (C5 + t_bounded
                          * (C6 + t_bounded
                            * (C7 + t_bounded * C8)
                            )
                          )
                        )
                      )
                    )
                  )
                )

        # Even with P=1050mb and T=55C, the sat. vap. pres only contributes to
        # ~15% of total pres.
        esL = np.minimum(esL, p * 0.15)
        mixRatioESL = .622 * esL / (p - esL)
        return mixRatioESL

    def consider(self, field, xlvl, proj, hdate, slab, intfile):
        """ Considers whether a given field may be used in the computation
        of RH at the given pressure level. When all available information has
        been acquired, this method computes the RH field and writes it to the
        output intermediate file.
        """

        if field == 'SPECHUMD':
            self.savefields[('q', xlvl )] = slab
        # Differentiate from surface pressure TT denoted by 200100.0
        elif field == 'TT' and xlvl != 200100.0:
            self.savefields[('tt', xlvl)] = slab
        else:
            return

        if ('tt', xlvl) in self.savefields and ('q', xlvl) in self.savefields:
          print('Computing RH at ' + str(xlvl))
          mixRatioESL = self.liquidSaturationVaporMixRatio( self.savefields[('tt', xlvl)], xlvl)
          mixRatioWaterVapor = self.savefields[('q', xlvl)] / (1.0 - self.savefields[('q', xlvl)])
          rh = 100.0 * mixRatioWaterVapor / mixRatioESL

          write_slab(intfile, rh, xlvl, proj, 'RH', hdate, '%',
              'ERA5 reanalysis grid', 'Relative humidity')

          del self.savefields[('tt', xlvl)]
          del self.savefields[('q', xlvl)]


class GeopotentialHeightDiags:
    """ Implements the computation of SOILHGT and GHT (geopotential height at
    the surface and at upper-air levels, respectively) from ERA5 Z
    (geopotential), whose WPS name is either GEOPT at upper-air levels or
    SOILGEO at the surface.
    """

    def consider(self, field, xlvl, proj, hdate, slab, intfile):
        """ Considers whether the given field represents geopotential, and if
        so, computes geopotential height, writing the result to the output
        intermediate file.
        """

        if field == 'GEOPT':
            print('Computing GHT at ', xlvl)

            write_slab(intfile, slab / 9.81, xlvl, proj, 'GHT', hdate, 'm',
                'ERA5 reanalysis grid', 'Geopotential height')

        elif field == 'SOILGEO':
            print('Computing SOILHGT')

            write_slab(intfile, slab / 9.81, 200100.0, proj, 'SOILHGT', hdate, 'm',
                'ERA5 reanalysis grid', 'Geopotential height')

        else:
            return


def days_in_month(year, month):
    """ Returns the number of days in a month, depending on the year.
    A Gregorian calendar is assumed for the purposes of determining leap
    years.
    """
    non_leap_year = [ 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 ]
    leap_year     = [ 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 ]

    if (year % 4 == 0) and ((year % 100 != 0) or (year % 400 == 0)):
        return leap_year[month - 1]
    else:
        return non_leap_year[month - 1]


def intdate_to_string(utc_int):
    """ Converts an integer date representation into a string.
    The digits of utc_int represent yyyymmddhh, and the returned string
    is of the form 'yyyy-mm-dd_hh:00:00'.
    """
    year = utc_int // 1000000
    month = (utc_int // 10000) % 100
    day = (utc_int // 100) % 100
    hour = utc_int % 100
    return '{:04d}-{:02d}-{:02d}_{:02d}:00:00'.format(year, month, day, hour)


def datetime_to_string(dt):
    """ Converts a Python datetime instance into a string of the form
    'yyyy-mm-dd_hh'.
    """
    return '{:04d}-{:02d}-{:02d}_{:02d}'.format(dt.year, dt.month, dt.day, dt.hour)


def string_to_yyyymmddhh(str):
    """ Given a string of the form yyyy-mm-dd_hh, returns the component year,
    month, day, and hour as a tuple of integers.
    """
    tmp = str.split('-')
    yyyy = int(tmp[0])
    mm = int(tmp[1])
    ddhh = tmp[2]
    dd = int(ddhh.split('_')[0])
    hh = int(ddhh.split('_')[1])

    return yyyy, mm, dd, hh


def begin_6hourly(yyyy, mm, dd, hh):
    """ Returns a date-time string of the form yyyymmddhh for the year, month,
    day, and hour with the hours rounded down the the beginning of a six-hour
    interval, i.e., 0, 6, 12, and 18.
    """
    return f'{yyyy:04d}{mm:02d}{dd:02d}{((hh // 6) * 6):02d}'


def end_6hourly(yyyy, mm, dd, hh):
    """ Returns a date-time string of the form yyyymmddhh for the year, month,
    day, and hour with the hours rounded up the the last hour of a six-hour
    interval, i.e., 5, 11, 17, and 23.
    """
    return f'{yyyy:04d}{mm:02d}{dd:02d}{((hh // 6) * 6 + 5):02d}'


def begin_daily(yyyy, mm, dd, hh):
    """ Returns a date-time string of the form yyyymmddhh for the year, month,
    day, and hour with the hours rounded down the beginning of a day (i.e., to 00).
    """
    return f'{yyyy:04d}{mm:02d}{dd:02d}{0:02d}'


def end_daily(yyyy, mm, dd, hh):
    """ Returns a date-time string of the form yyyymmddhh for the year, month,
    day, and hour with the hours rounded up the end of a day (i.e., to 23).
    """
    return f'{yyyy:04d}{mm:02d}{dd:02d}{23:02d}'


def begin_monthly(yyyy, mm, dd, hh):
    """ Returns a date-time string of the form yyyymmddhh for the year, month,
    day, and hour with the day and hour rounded down the the beginning of a
    monthly interval.
    """
    return f'{yyyy:04d}{mm:02d}{1:02d}{0:02d}'


def end_monthly(yyyy, mm, dd, hh):
    """ Returns a date-time string of the form yyyymmddhh for the year, month,
    day, and hour with the day and hour rounded up the the last day and hour
    of the month.
    """
    return f'{yyyy:04d}{mm:02d}{days_in_month(yyyy,mm):02d}{23:02d}'


class MapProjection:
    """ Stores parameters of map projections as used in the WPS intermediate
    file format.
    """

    def __init__(self, projType, startLat, startLon, startI, startJ,
                 deltaLat, deltaLon,
                 dx=0.0, dy=0.0, truelat1=0.0, truelat2=0.0, xlonc=0.0):
        self.projType = projType
        self.startLat = startLat
        self.startLon = startLon
        self.startI = startI
        self.startJ = startJ
        self.deltaLat = deltaLat
        self.deltaLon = deltaLon
        self.dx = dx
        self.dy = dy
        self.truelat1 = truelat1
        self.truelat2 = truelat2
        self.xlonc = xlonc


class MetVar:
    """ Describes a variable to be converted from netCDF to intermediate file
    format.
    """

    def __init__(self, WPSname, ERA5name, ERA5file, beginDateFn, endDateFn,
                 mapProj, isInvariant=False):
        self.WPSname = WPSname
        self.ERA5name = ERA5name
        self.ERA5file = ERA5file
        self.beginDateFn = beginDateFn
        self.endDateFn = endDateFn
        self.mapProj = mapProj
        self.isInvariant = isInvariant


def find_era5_file(var, validtime, localpaths=None):
    """ Returns a filename with path information of an ERA5 netCDF file given
    the ERA5 netCDF variable name and the valid time of the variable.
    The localpaths argument may be used to specify an array of local
    directories to search for ERA5 netCDF files. If localpaths is not provided
    or is None, known paths on the NWSC Glade filesystem are searched.
    If no file can be found containing the specified variable at the specified
    time, a RuntimeError exception is raised.
    """
    import os.path

    glade_paths = [
        # New Glade paths as of March 2025
        '/glade/campaign/collections/rda/data/d633006/e5.oper.an.ml/',
        '/glade/campaign/collections/rda/data/d633000/e5.oper.an.pl/',
        '/glade/campaign/collections/rda/data/d633000/e5.oper.an.sfc/',
        '/glade/campaign/collections/rda/data/d633000/e5.oper.invariant/197901/',
        '/glade/campaign/collections/rda/data/d633006/e5.oper.invariant/',

        # Old Glade paths prior to March 2025
        '/glade/campaign/collections/rda/data/ds633.6/e5.oper.an.ml/',
        '/glade/campaign/collections/rda/data/ds633.0/e5.oper.an.pl/',
        '/glade/campaign/collections/rda/data/ds633.0/e5.oper.an.sfc/',
        '/glade/campaign/collections/rda/data/ds633.0/e5.oper.invariant/197901/',
        '/gpfs/csfs1/collections/rda/decsdata/ds630.0/P/e5.oper.invariant/201601/'
        ]

    if localpaths != None:
        file_paths = localpaths
    else:
        file_paths = glade_paths

    yyyy, mm, dd, hh = string_to_yyyymmddhh(validtime)

    begin_date = var.beginDateFn(yyyy, mm, dd, hh)
    end_date = var.endDateFn(yyyy, mm, dd, hh)

    for p in file_paths:
        if var.isInvariant or localpaths != None:
            # For time-invariant fields, or if we are searching local paths,
            # assume that there is no need to append yyyymm to the end of
            # directories.
            base_path = p
        else:
            base_path = p + f'{yyyy:04d}{mm:02d}/'

        filename = base_path + var.ERA5file.format(begin_date, end_date)
        if os.path.isfile(filename):
            return filename

    raise RuntimeError('Error: Could not find file ' +
        var.ERA5file.format(begin_date, end_date) +
        ' needed for ERA5 variable ' + var.ERA5name)


def find_time_index(ncfilename, validtime):
    """ Returns a 0-based offset into the unlimited dimension of the specified
    valid time within the specified etCDF file.
    If the specified time is not found in the file, an offset of -1 is
    returned.
    The 'utc_date' variable is assumed to exist in the netCDF file, and it is
    through this variable that the search for the valid time takes place.
    """
    from netCDF4 import Dataset
    import numpy as np

    yyyy, mm, dd, hh = string_to_yyyymmddhh(validtime)

    needed_date = yyyy * 1000000 + mm * 10000 + dd * 100 + hh

    with Dataset(ncfilename) as f:
        utc_date = f.variables['utc_date'][:]

        idx = np.where(needed_date == utc_date)
        if idx[0].size == 0:
            return -1
        else:
            return idx[0][0]


def write_slab( intfile, slab, xlvl, proj, WPSname, hdate, units, map_source, desc):
    """ Writes a 2-d array (a 'slab' of data) to an opened intermediate file
    using the provided level, projection, and other metadata.
    This routine assumes that the intermediate file has already been created
    through a previous call to the WPSUtils.intermediate.write_met_init
    routine.
    """
    stat = intfile.write_next_met_field(
        5, slab.shape[1], slab.shape[0], proj.projType, 0.0, xlvl,
        proj.startLat, proj.startLon, proj.startI, proj.startJ,
        proj.deltaLat, proj.deltaLon, proj.dx, proj.dy, proj.xlonc,
        proj.truelat1, proj.truelat2, 6371229.0, 0, WPSname,
        hdate, units, map_source, desc, slab)


def add_trailing_slash(str):
    """ Returns str with a forward slash appended to it if the str argument does
    not end with a forward slash character. Otherwise, return str unmodified if
    it already ends with a slash.
    """
    if str[-1] == '/':
        return str
    else:
        return str + '/'


def handle_datetime_args(args):
    """ Returns starting and ending datetime objects along with an interval
    timedelta object given an argparse namespace with members 'datetime',
    'until_datetime', and 'interval_hours'. If 'until_datetime' is None,
    the returned ending datetime is the same as the starting datetime.
    If 'interval_hours' is 0, it defaults to a interval of six hours.
    """

    yyyy, mm, dd, hh = string_to_yyyymmddhh(args.datetime)
    startDate = datetime.datetime(yyyy, mm, dd, hh)

    if args.until_datetime != None:
        yyyy, mm, dd, hh = string_to_yyyymmddhh(args.until_datetime)
        endDate = datetime.datetime(yyyy, mm, dd, hh)
    else:
        endDate = startDate

    if endDate < startDate:
        raise ValueError('until_datetime precedes datetime')

    if args.interval_hours > 0:
        intvH = datetime.timedelta(hours=args.interval_hours)
    else:
        raise ValueError('interval_hours is not a positive integer')

    return startDate, endDate, intvH


if __name__ == '__main__':
    from netCDF4 import Dataset
    import numpy as np
    import WPSUtils
    import argparse
    import datetime
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument('datetime', help='the date-time to convert in YYYY-MM-DD_HH format')
    parser.add_argument('until_datetime', nargs='?', default=None, help='the date-time in YYYY-MM-DD_HH format until which records are converted (Default: datetime)')
    parser.add_argument('interval_hours', type=int, nargs='?', default=6, help='the interval in hours between records to be converted (Default: %(default)s)')
    parser.add_argument('-p', '--path', help='the local path to search for ERA5 netCDF files')
    parser.add_argument('-i', '--isobaric', action='store_true', help='use ERA5 pressure-level data rather than model-level data')
    parser.add_argument('-v', '--variables', help='a comma-separated list, without spaces, of WPS variable names to process')
    args = parser.parse_args()

    try:
        startDate, endDate, intvH = handle_datetime_args(args)
    except ValueError as e:
        print('Error in argument list: ' + e.args[0])
        sys.exit(1)

    print('datetime = ', startDate)
    print('until_datetime = ', endDate)
    print('interval_hours = ', intvH)

    # Set up the two map projections used in the ERA5 fields to be converted
    Gaussian = MapProjection(WPSUtils.Projections.GAUSS,
         89.7848769072, 0.0, 1.0, 1.0, 640.0 / 2.0, 360.0 / 1280.0)
    LatLon = MapProjection(WPSUtils.Projections.LATLON,
         90.0, 0.0, 1.0, 1.0, -0.25, 0.25)

    diagnostics = []
    diagnostics.append(SnowDiags())
    diagnostics.append(RH2mDiags())
    diagnostics.append(GeopotentialHeightDiags())

    if args.isobaric:
        diagnostics.append(RHDiags())

    int_vars = []
    if args.isobaric:
        int_vars.append(MetVar('GEOPT', 'Z', 'e5.oper.an.pl.128_129_z.ll025sc.{}_{}.nc', begin_daily, end_daily, LatLon))
        int_vars.append(MetVar('SPECHUMD', 'Q', 'e5.oper.an.pl.128_133_q.ll025sc.{}_{}.nc', begin_daily, end_daily, LatLon))
        int_vars.append(MetVar('TT', 'T', 'e5.oper.an.pl.128_130_t.ll025sc.{}_{}.nc', begin_daily, end_daily, LatLon))
        int_vars.append(MetVar('UU', 'U', 'e5.oper.an.pl.128_131_u.ll025uv.{}_{}.nc', begin_daily, end_daily, LatLon))
        int_vars.append(MetVar('VV', 'V', 'e5.oper.an.pl.128_132_v.ll025uv.{}_{}.nc', begin_daily, end_daily, LatLon))
    else:
        int_vars.append(MetVar('SPECHUMD', 'Q', 'e5.oper.an.ml.0_5_0_1_0_q.regn320sc.{}_{}.nc', begin_6hourly, end_6hourly, Gaussian))
        int_vars.append(MetVar('TT', 'T', 'e5.oper.an.ml.0_5_0_0_0_t.regn320sc.{}_{}.nc', begin_6hourly, end_6hourly, Gaussian))
        int_vars.append(MetVar('UU', 'U', 'e5.oper.an.ml.0_5_0_2_2_u.regn320uv.{}_{}.nc', begin_6hourly, end_6hourly, Gaussian))
        int_vars.append(MetVar('VV', 'V', 'e5.oper.an.ml.0_5_0_2_3_v.regn320uv.{}_{}.nc', begin_6hourly, end_6hourly, Gaussian))
    int_vars.append(MetVar('LANDSEA', 'LSM', 'e5.oper.invariant.128_172_lsm.ll025sc.1979010100_1979010100.nc', begin_monthly, end_monthly, LatLon, isInvariant=True))
    int_vars.append(MetVar('SST', 'SSTK', 'e5.oper.an.sfc.128_034_sstk.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('SKINTEMP', 'SKT', 'e5.oper.an.sfc.128_235_skt.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('SM000007', 'SWVL1', 'e5.oper.an.sfc.128_039_swvl1.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('SM007028', 'SWVL2', 'e5.oper.an.sfc.128_040_swvl2.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('SM028100', 'SWVL3', 'e5.oper.an.sfc.128_041_swvl3.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('SM100289', 'SWVL4', 'e5.oper.an.sfc.128_042_swvl4.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('ST000007', 'STL1', 'e5.oper.an.sfc.128_139_stl1.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('ST007028', 'STL2', 'e5.oper.an.sfc.128_170_stl2.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('ST028100', 'STL3', 'e5.oper.an.sfc.128_183_stl3.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('ST100289', 'STL4', 'e5.oper.an.sfc.128_236_stl4.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('SEAICE', 'CI', 'e5.oper.an.sfc.128_031_ci.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('TT', 'VAR_2T', 'e5.oper.an.sfc.128_167_2t.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('DEWPT', 'VAR_2D', 'e5.oper.an.sfc.128_168_2d.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('UU', 'VAR_10U', 'e5.oper.an.sfc.128_165_10u.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('VV', 'VAR_10V', 'e5.oper.an.sfc.128_166_10v.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('SNOW_DEN', 'RSN', 'e5.oper.an.sfc.128_033_rsn.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('SNOW_EC', 'SD', 'e5.oper.an.sfc.128_141_sd.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('PMSL', 'MSL', 'e5.oper.an.sfc.128_151_msl.ll025sc.{}_{}.nc', begin_monthly, end_monthly, LatLon))
    int_vars.append(MetVar('PSFC', 'SP', 'e5.oper.an.ml.128_134_sp.regn320sc.{}_{}.nc', begin_6hourly, end_6hourly, Gaussian))
    int_vars.append(MetVar('SOILGEO', 'Z', 'e5.oper.invariant.128_129_z.regn320sc.2016010100_2016010100.nc', begin_monthly, end_monthly, Gaussian, isInvariant=True))

    # WPS variable names in dont_output cause the corresponding field to not be
    #   written to the output intermediate file. This is useful when fields are
    #   read from ERA5 netCDF files only to be used in diagnosing other fields.
    dont_output = []
    dont_output.append('GEOPT')    # Only used to diagnose GHT
    dont_output.append('SOILGEO')  # Only used to diagnose SOILHGT
    dont_output.append('DEWPT')    # Only used to diagnose RH
    dont_output.append('SNOW_EC')  # Only used in diagnosing SNOW and SNOWH
    dont_output.append('SNOW_DEN') # Only used in diagnosing SNOW and SNOWH

    if args.path != None:
        paths = [ add_trailing_slash(p) for p in args.path.split(',') ]
    else:
        paths = None

    # Prepare a list of variables to process. By default, this list contains
    #   all WPS variables from the int_vars list, but the user may have supplied
    #   a subset of these variables.
    var_set = [ int_var.WPSname for int_var in int_vars ]
    if args.variables != None:
        user_var_set = args.variables.split(',')

        errcount = 0
        for v in user_var_set:
            if v not in var_set:
                errcount = errcount + 1
                print('Error: ' + v + ' is not a known WPS variable')

        if errcount > 0:
            print('The following are known WPS variables:', var_set)
            sys.exit(1)

        var_set = user_var_set

    currDate = startDate
    while currDate <= endDate:
        initdate = datetime_to_string(currDate)
        print('Processing time record ' + initdate)

        intfile = WPSUtils.IntermediateFile('ERA5', initdate)

        for v in int_vars:

            if v.WPSname not in var_set:
                continue

            try:
                e5filename = find_era5_file(v, initdate, localpaths=paths)
            except RuntimeError as e:
                print(e.args[0])
                intfile.close()
                sys.exit(1)

            idx = find_time_index(e5filename, initdate)
            if idx == -1:
                idx = 0
            proj = v.mapProj

            print(e5filename)
            with Dataset(e5filename) as f:
                hdate = intdate_to_string(f.variables['utc_date'][idx])
                print('Converting ' + v.WPSname + ' at ' + hdate)
                map_source = 'ERA5 reanalysis grid          '
                units = f.variables[v.ERA5name].units
                desc = f.variables[v.ERA5name].long_name
                field_arr = f.variables[v.ERA5name][idx,:]

                if field_arr.ndim == 2:
                    slab = field_arr
                    xlvl = 200100.0

                    # There are some special cases in which 2-d fields are not
                    # surface (xlvl = 200100.0) variables
                    if v.WPSname == 'SOILGEO':
                        xlvl = 1.0
                    elif v.WPSname == 'PMSL':
                        xlvl = 201300.0

                    if v.WPSname in dont_output:
                        print(v.WPSname + ' is NOT being written to the ' +
                            'intermediate file at level', xlvl)
                    else:
                        write_slab(intfile, slab, xlvl, proj, v.WPSname, hdate,
                            units, map_source, desc)

                    for diag in diagnostics:
                        diag.consider(v.WPSname, xlvl, proj, hdate, slab, intfile)
                else:
                    for k in range(f.dimensions['level'].size):
                        slab = field_arr[k,:,:]

                        # For isobaric levels, the WPS intermediate file xlvl
                        # value should be in Pa, while the ERA5 netCDF files
                        # provide units of hPa
                        if args.isobaric:
                            xlvl = f.variables['level'][k] * 100.0    # Convert hPa to Pa
                        else:
                            xlvl = float(f.variables['level'][k])     # Level index

                        if v.WPSname in dont_output:
                            print(v.WPSname + ' is NOT being written to the ' +
                                'intermediate file at level', xlvl)
                        else:
                            write_slab(intfile, slab, xlvl, proj,
                                v.WPSname, hdate, units, map_source, desc)

                        for diag in diagnostics:
                            diag.consider(v.WPSname, xlvl, proj, hdate, slab, intfile)

        intfile.close()

        currDate += intvH
