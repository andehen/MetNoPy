# MetNoPy

**Disclaimer**: This package is still under development, so it may contain bugs or weird behaviour. 

MetNoNpy is python package that can retrieve data from the Norwegian Meteorological Institute.
More specifically it uses the API which you can use manually [here](http://eklima.met.no/met/MetService?operation=getMetDataValues).
Also see [eklima.no](eklima.no) for more information about the data source.
The data is returned as a [Pandas](http://pandas.pydata.org/) data frame.
If you are not familiar with Pandas, I recommend you to take a look at some tutorials to get started.
It is super easy to work with!

## Installation

Package is not ready for PyPi yet, but will be once it is stable.

To install, run 
```
pip install https://github.com/hennumjr/MetNoPy/archive/master.zip
```

or clone the project. 

If you don't have pip, see [here](https://pip.pypa.io/en/stable/installing/)

## Usage

The usage is

```python
get_met_data(timeserietypeid, stations, elements, from_date, to_date, 
             hours, months, tz=pytz.UTC)

```

where
 * **timeserietypeid** (*str*): "2" (only 2 is supported for now)
 * **stations** (*str*): A comma seperated string with station id's
 * **elements** (*str*): A comma seperated string with weather element codes. For an almost complete list of codes, see 
 [here](http://eklima.met.no/Help/Stations/toDay/all/en_e18700.html).
 * **from_date** (*str*): Date as string in the format "2015-12-31"
 * **to_date** (*str*): Date as string in the format "2015-12-31"
 * **hours** (*str*): A comma separated string with hours (in UTC time!). Use empty string for all hours.
 * **months** (*str*): A comma separated string with months. Use empty string for all months
 * **tz** (*pytz.timezone*): Optional. Default is UTC, same as Met API. 
 * **long_format** (*boolean*): Optional. Specifies format of returned dataframe. Default is False (wide format),
   and for most cases this is the preferable format.
 
 The parameters are more or less passed directly to the [API](http://eklima.met.no/met/MetService?operation=getMetDataValues),
 except for **tz** which is only used internally to convert dates to the provided timezone. 

Example of usage:

To get the temperature in Oslo, Blindern (18700) and Trondheim, Voll (68860) at 11am UTC from the 10th to 15th of June 2015,
you can run

```python
In [1]: from metnopy import get_met_data

In [2]: get_met_data("2", "18700,68860", "TA", "2015-06-10", "2015-06-15", "11", "", 
   ...:              pytz.timezone("Europe/Oslo"))

Out[3]: 
                    TA_18700 TA_68860
date                                 
2015-06-10 11:00:00     18.4      9.8
2015-06-11 11:00:00     20.1      9.8
2015-06-12 11:00:00     23.1     12.2
2015-06-13 11:00:00     18.8      9.5
2015-06-14 11:00:00     17.5      7.7
2015-06-15 11:00:00     16.5      6.8

```

Note that the Met API returns the dates in UTC as default. Thus, if you want to have them returned in Norwegian time zone, 
provide the pytz.timezone object as and extra argument. For now, the query parameters are passed directly to the API so they
are still in UTC. 

```python
In [1]: import pytz

In [2]: from metnopy import get_met_data

In [3]: get_met_data("2", "18700,68860", "TA", "2015-06-10", "2015-06-15", "11", "", 
   ...:              pytz.timezone("Europe/Oslo"))

Out[4]: 
                    TA_18700 TA_68860
date                                 
2015-06-10 13:00:00     18.4      9.8
2015-06-11 13:00:00     20.1      9.8
2015-06-12 13:00:00     23.1     12.2
2015-06-13 13:00:00     18.8      9.5
2015-06-14 13:00:00     17.5      7.7
2015-06-15 13:00:00     16.5      6.8

```

#### Long format example

Long format can be handy sometimes. The following example shows how the resulting dataframe looks like.

```python
In [1]: get_met_data("2", "68860", "TA, RR_12", "2015-12-06","2015-12-07", "6,18", "", long_format=True)

Out[2]: 
                 date  st.no value variable
0 2015-12-06 06:00:00  68860   3.0       TA
1 2015-12-06 06:00:00  68860   0.0    RR_12
2 2015-12-06 18:00:00  68860   2.5       TA
3 2015-12-06 18:00:00  68860   2.3    RR_12
4 2015-12-07 06:00:00  68860   4.0       TA
5 2015-12-07 06:00:00  68860  11.3    RR_12

```
