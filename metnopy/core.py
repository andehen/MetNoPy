from datetime import datetime
import numpy as np
import pandas as pd
import pytz
import requests
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError


# See http://eklima.met.no/Help/Stations/toDay/all/en_e18700.html for information about weather elements
# Values in these lists will automatically be cast to the type in the list name.

# For values not listed here, you can convert them to your preferred type with
#       weather_df[element_code] = weather_df[element_code].apply(<type>)  where type can f. ex. be float

# Feel free to include more in these lists

WEATHER_ELEMENT_TYPES = [(float,
                          ["TA", "TAX", "TAX_12", "TAN", "TAN_12", "TD",
                           "SA", "RA", "RR_12", "RR_24",
                           "FF", "DD"]),
                         (int,
                          ["St.no", "SD"])]


class InvalidQueryException(Exception):
    pass


class MetAPIStatusCodeException(Exception):
    pass


class XMLParsingError(Exception):
    pass


class UnknownXMLTagException(Exception):
    pass


def get_xml_obs(timeserietypeid, stations, elements, from_date, to_date, hours, months):
    """ Get met data in XML format for the given parameters

    This function builds the query url, performs a GET request
    to the met API and parses the returned content as XML.
    If the query is valid but no data is found, it will return an empty list.


    Args:
        timeserietypeid (str): Timeserie type id
        stations (str): Stations Ex. "18700"
        elements (str): Weather element codes Ex. "TA,RR_24"
        from_date (str): Ex. "2015-11-10"
        to_date (str): Ex. "2015-11-12"
        hours (str): Ex. "1,13"
        months (str): Use "" (empty string) for all. Works as a filter. Ex. "1,7"

    Returns:
        list : List of XML elements (weather observations)

    Raises:
        MetAPIStatusCodeException : If the server returns other status code than 200
        XMLParsingError : If the content returned from Met API can not be parsed as XML
        InvalidQueryException : If Met API returns 200, but with error message
    """

    # Base url of MET api
    baseurl = "http://eklima.met.no/met/MetService?invoke=getMetDataValues&"

    query_string = ("timeserietypeid={0}&"
                    "format=&"
                    "from={1}&"
                    "to={2}&"
                    "stations={3}&"
                    "elements={4}&"
                    "hours={5}&"
                    "months={6}&"
                    "username=").format(timeserietypeid, from_date, to_date, stations,
                                        elements, hours, months)

    response = requests.get(baseurl+query_string)

    if response.status_code is not 200:
        raise MetAPIStatusCodeException("Met API responded with status code {0}".format(response.status_code))

    try:
        xml_tree = ElementTree.fromstring(response.content)
    except ParseError:
        raise XMLParsingError("Failed to parse response content as XML")

    try:
        xml_data = xml_tree[0][0][0][0]
    except IndexError:
        raise XMLParsingError("Unknown structure on XML response.")

    if xml_data.tag != 'Metdata':
        text = xml_data[0].text

        if xml_data.tag == 'Error':
            if text == 'No data found':
                return []

            else:
                raise InvalidQueryException("Met API returned: {0}".format(text))
        else:
            raise UnknownXMLTagException("XML tag {0} is not known".format(xml_data.tag))

    observations = list(xml_data)

    return observations


def xml_obs_to_dict(xml_observation, tz):
    """ Transform xml object to dict

    Args:
        xml_observation (xml.etree.ElementTree.Element): Weather observation represented as an XML Element
        tz (pytz.timezone): A pytz timezone object defining which timezone to use

    Returns:
        dict : Weather observation represented as a python dict
    """
    date_str = xml_observation.get('from')
    date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")

    # Met API return observations in UTC time. To convert to other timezones we need to
    # make the datetime object aware of the timezone and return the date in the new timezone.
    # The timezone information is removed from the date object afterwards since in most cases
    # the information is not needed and the user should be aware of which timezone he uses.

    if tz is not pytz.UTC:
        date = date.replace(tzinfo=pytz.UTC)
        date = date.astimezone(tz)
        date = date.replace(tzinfo=None)

    locations = list(xml_observation)

    multiple_locations = (len(locations) > 1)

    observation_dict = {}

    for location in list(xml_observation):

        observation_dict["Date"] = date

        weather_elements = list(location)

        for el in weather_elements:
            el_code = el.get("id")

            if multiple_locations:
                el_code += "_" + location.get("id")
            # Met API uses -99999 as default for NaN values
            if el[0].text == "-99999":
                observation_dict[el_code] = np.nan
            else:
                observation_dict[el_code] = el[0].text

    return observation_dict


def xml_observations_to_df(observations, tz):
    """ Map weather observations from XML elements to python dicts readable by Pandas

    Args:
        observations (list(xml.etree.ElementTree.Element)) : A list with XML elements
        tz (pytz.timezone) : A pytz timezone object

    Returns:
        pandas.DataFrame : A data frame with weather observations
    """

    observation_list = map(lambda obs: xml_obs_to_dict(obs, tz), observations)

    weatherdf = pd.DataFrame(observation_list)

    if not weatherdf.empty:
        weatherdf.set_index("Date", inplace=True)

        # Convert element types to float, int or whatever
        for tp in WEATHER_ELEMENT_TYPES:
            for code in tp[1]:
                if code in weatherdf.columns:
                    weatherdf[code] = weatherdf[code].apply(tp[0])

    return weatherdf


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
        stations_as_column:
        tz (pytz.timezone) : A python timezone object. Default is UTC.

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

    if from_date_year == to_date_year:
        tmp_xml_obs = get_xml_obs(timeserietypeid, stations, elements, from_date,
                                  to_date, hours, months)
        tmp_df = xml_observations_to_df(tmp_xml_obs, tz)
        if weather_df.empty:
            weather_df = tmp_df
        else:
            weather_df = weather_df.append(tmp_df)

    else:
        # Get data for first year
        tmp_xml_obs = get_xml_obs(timeserietypeid, stations, elements, from_date,
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
        tmp_xml_obs = get_xml_obs(timeserietypeid, stations, elements, to_date_year+"-01-01",
                                  to_date, hours, months)
        tmp_df = xml_observations_to_df(tmp_xml_obs, tz)
        weather_df = weather_df.append(tmp_df)

    return weather_df
