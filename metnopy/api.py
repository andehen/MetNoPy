import pandas as pd
import pytz

from .core import get_xml_obs, xml_observations_to_df
from .core import InvalidQueryException


def get_met_data(timeserietypeid, stations, elements, from_date, to_date, hours, months, tz=pytz.timezone("UTC")):
    """ Returns a pandas data frame with met data found for the given parameters

    Please note that the dates and hours given in the query are in UTC, so if specify another timezone
    to return the data in, the hours you give in the query will differ from the results.

    Ex: If you would like to get the temperature at 19 every day for June in Trondheim (station 68860) 2015,
        returned in Norwegian time zone, the function call would be

        get_met_data("2", "68860", "TA", "2015-06-01", "2015-06-30", "17", "", pytz.timezone("Europe/Oslo"))

    Args:
        timeserietypeid (str) : See documentation on WSKlima. Use "2" for all available observations
        stations (str) : List of stations to get observations from. Ex. "88690,88660".
                         NB: Even though it does support mulitple stations, it is better to use this
                         function with one station at a time, and then merge the data frames later in the
                         preferred way
        elements (str) : List of elements to get. Ex. "TA,FF,DD,SA". See this url
                         http://eklima.met.no/Help/Stations/toDay/all/en_e88660.html
                         for more information.
        from_date (str) : Start date. Ex. "2010-01-01"
        to_date (str) : End date. Ex. "2012-01-01"
        hours (str) : String with hours from 0 - 23. Ex. "0,6,12,18". Use "" for all hours
        months (str) : String with months. Ex. "1,2,3,4,11,12". Use "" for all months
        tx (pytz.timezone) : A python timezone object. Default is UTC.

    Returns:
        pandas.DataFrame : Data frame with weather observations
    """

    if timeserietypeid != "2":
        raise InvalidQueryException("Only timeserietype 2 is supported in this version.")

    if hours is "":
        hours = ",".join(map(str, range(0, 24)))

    from_date_year = from_date.split("-")[0]
    to_date_year = to_date.split("-")[0]

    # To avoid making too big queries, we spilt requests by station and year
    weather_df = pd.DataFrame()

    for station in stations.split(","):

        if from_date_year == to_date_year:
            tmp_xml_obs = get_xml_obs(timeserietypeid, station, elements, from_date,
                                      to_date, hours, months)
            tmp_df = xml_observations_to_df(tmp_xml_obs, tz)
            if weather_df.empty:
                weather_df = tmp_df
            else:
                weather_df = weather_df.append(tmp_df)

        else:
            # Get data for first year
            tmp_xml_obs = get_xml_obs(timeserietypeid, station, elements, from_date,
                                      from_date_year+"-12-31", hours, months)
            tmp_df = xml_observations_to_df(tmp_xml_obs, tz)

            if weather_df.empty:
                weather_df = tmp_df
            else:
                weather_df = weather_df.append(tmp_df)

            # Get data for years whole years in period given
            for year in range(int(from_date_year)+1, int(to_date_year)):

                tmp_from_date = str(year)+"-01-01"
                tmp_end_date = str(year)+"-12-31"

                tmp_xml_obs = get_xml_obs(timeserietypeid, stations, elements,
                                          tmp_from_date, tmp_end_date, hours, months)

                tmp_df = xml_observations_to_df(tmp_xml_obs, tz)

                weather_df = weather_df.append(tmp_df)

            # Get data for last year in query
            tmp_xml_obs = get_xml_obs(timeserietypeid, station, elements, to_date_year+"-01-01",
                                      to_date, hours, months)
            tmp_df = xml_observations_to_df(tmp_xml_obs, tz)
            weather_df = weather_df.append(tmp_df)

    weather_df.sort_index(inplace=True)
    columns = weather_df.columns.tolist()
    columns.remove("St.no")
    columns = ["St.no"]+columns
    weather_df = weather_df[columns]

    return weather_df
