# era5_to_int

A simple Python script for converting ERA5 netCDF files to the WPS intermediate
format

## Overview

The `era5_to_int.py` script converts ERA5 model- or pressure-level netCDF files
to the WRF Pre-processing System (WPS) intermediate file format, permitting the
use of these data with either the Weather Research and Forecasting (WRF) model
or the Model for Prediction Across Scales - Atmosphere (MPAS-A).

The only required command-line argument is the date-time, in YYYY-MM-DD_HH
format, of ERA5 files to convert. For example:
```
era5_to_int.py 2024-05-01_00
```

Conversion of a range of date-times is possible through the use of additional
command-line arguments as described in the Usage section.

The following surface fields from the d633 datasets are handled by the script:

| Field   | Dataset | Horiz. grid | Num. levels |
|---------|---------|-------------|-------------|
| SOILGEO | [d633000](https://rda.ucar.edu/datasets/d633000/) | ~0.281-deg Gaussian | 1 |
| SP      | [d633006](https://rda.ucar.edu/datasets/d633006/) | ~0.281-deg Gaussian | 1 |
| MSL     | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| VAR_2T  | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| VAR_2D  | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| VAR_10U | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| VAR_10V | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| RSN     | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| SD      | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| LSM     | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| SSTK    | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| SKT     | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| SWVL1   | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| SWVL2   | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| SWVL3   | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| SWVL4   | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| STL1    | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| STL2    | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| STL3    | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| STL4    | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |
| CI      | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 1 |

When model-level ERA5 files are being processed (the default), the following
atmospheric fields are handled:

| Field   | Dataset | Horiz. grid | Num. levels |
|---------|---------|-------------|-------------|
| Q       | [d633006](https://rda.ucar.edu/datasets/d633006/) | ~0.281-deg Gaussian | 137 |
| T       | [d633006](https://rda.ucar.edu/datasets/d633006/) | ~0.281-deg Gaussian | 137 |
| U       | [d633006](https://rda.ucar.edu/datasets/d633006/) | ~0.281-deg Gaussian | 137 |
| V       | [d633006](https://rda.ucar.edu/datasets/d633006/) | ~0.281-deg Gaussian | 137 |

Alternatively, if the processing of pressure-level (isobaric) ERA5 files is
selected with the `-i` / `--isobaric` command-line option, the following
atmospheric fields are instead handled:

| Field   | Dataset | Horiz. grid | Num. levels |
|---------|---------|-------------|-------------|
| Z       | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 37 |
| Q       | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 37 |
| T       | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 37 |
| U       | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 37 |
| V       | [d633000](https://rda.ucar.edu/datasets/d633000/) | 0.25-deg Lat-Lon | 37 |

As fields are converted from netCDF to intermediate format, their names are also
converted to match WPS and MPAS-A expectations.

## Requirements
The `era5_to_int.py` script requires:
- Python 3.11+
- netCDF4
- NumPy

## Usage

The only required command-line argument is the date-time, in YYYY-MM-DD_HH
format, of ERA5 model-level files to convert. For example:
```
era5_to_int.py 2024-05-01_00
```

Upon successful completion, an intermediate file with the prefix `ERA5` is
created in the current working directory; for example, `ERA5:2024-05-01_00`.

With no optional arguments, the script will search known paths on the NWSC Glade
filesystem for ERA5 model-level netCDF files. If the `-p`/`--path` option is
provided with a local path, the script will instead search that local path for
ERA5 files that have been downloaded from the NSF NCAR Research Data Archive
(RDA) d633 datasets. For example:
```
era5_to_int.py --path /some/data/directory/era5 2024-05-01_00
```

Processing a range of times is possible by providing as a second positional
argument the date-time until which time records should be converted. For
example, to converted the entire month of May 2024:
```
era5_to_int.py 2024-05-01_00 2024-05-31_18
```

By default, fields are converted at a six-hourly interval, and a different
interval may be specified with a third positional argument. For example, to
convert data at a three-hourly interval for the month of May 2024:
```
era5_to_int.py 2024-05-01_00 2024-05-31_21 3
```

If only a subset of the standard set of fields is needed, the `-v`/`--variables`
command-line option may be used to specify this subset as a comma-separated
list, without spaces, of the WPS field names. For example:
```
era5_to_int.py -v LANDSEA,SEAICE,SKINTEMP 2024-01-01_00 2024-01-31_00 24
```
In this example, intermediate files would be created with only the three fields
provided to the `-v` option, i.e., LANDSEA, SEAICE, and SKINTEMP. None of the
other fields that are usually processed by the `era5_to_int.py` script will be
processed.

Note that if a diagnostic variable (e.g, GHT) is needed in the output
intermediate files, all of the fields required to compute that diagnostic field
(e.g., GEOPT) must be specified in the list supplied to the `-v`/`--variable`
option.

Usage is provided by running the `era5_to_int.py` script with the `-h`/`--help`
argument, which prints the following:
```
usage: era5_to_int.py [-h] [-p PATH] [-i] [-v VARIABLES] datetime [until_datetime] [interval_hours]

positional arguments:
  datetime              the date-time to convert in YYYY-MM-DD_HH format
  until_datetime        the date-time in YYYY-MM-DD_HH format until which records are converted (Default:
                        datetime)
  interval_hours        the interval in hours between records to be converted (Default: 6)

options:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  the local path to search for ERA5 netCDF files
  -i, --isobaric        use ERA5 pressure-level data rather than model-level data
  -v VARIABLES, --variables VARIABLES
                        a comma-separated list, without spaces, of WPS variable names to process
```

## Supplementary files

Included in this repository is a list of ECMWF vertical level coefficients in
the `ecmwf_coeffs` file. The `ecmwf_coeffs` file may be used with the WPS
`calc_ecmwf_p.exe` utility program to generate an intermediate file with 3-d
pressure, geopotential height, and R.H. fields from ERA5 model-level data.
