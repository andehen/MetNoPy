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
#       weather_df[element_code] = weather_df[elemen_code].apply(<type>)  where type can f. ex. be float

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


class FailedToParseXML(Exception):
    pass


def get_xml_obs(timeserietypeid, stations, elements, from_date, to_date, hours, months):
    """ Get met data in XML format for the given parameters

    This function builds the query url, performs a GET request
    to the met API and returns the XML as a string


    Returns:
        str : The resulting XML schema as a string
    """

    # Base url of MET api
    baseurl = "http://eklima.met.no/metdata/MetDataService?invoke=getMetData&"

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
        raise FailedToParseXML("Failed to parse response content as XML")

    try:
        observations = xml_tree[0][0][0][1].findall("item")
    except IndexError:
        raise FailedToParseXML("Could not extract observations from XML.")

    if len(observations) is 0:
        text = xml_tree[0][0][0][2].text
        if text.find("Error") != -1:
            raise InvalidQueryException("Met API returned: {0}".format(text))

    return observations


def xml_obs_to_dict(xml_observation, tz):
    """ Transform xml object to dict

    Args:
        xml_object (xml.etree.ElementTree.Element): Weather observation represented as an XML Element
        tz (pytz.timezone): A pytz timezone object defining which timezone to use

    Returns:
        dict : Weather observation represented as a python dict
    """
    date_str = xml_observation[0].text
    date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")

    # Met API return observations in UTC time. To convert to other timezones we need to
    # make the datetime object aware of the timezone and return the date in the new timezone.
    # The timezone information is removed from the date object afterwards since in most cases
    # the information is not needed and the user should be aware of which timezone he uses.

    if tz is not pytz.UTC:
        date = date.replace(tzinfo=pytz.UTC)
        date = date.astimezone(tz)
        date = date.replace(tzinfo=None)

    observation_dict = {
        "Date": date,
        "St.no": xml_observation[1][0][0].text
    }

    weather_elements = xml_observation[1][0][2].findall("item")

    for el in weather_elements:

        # Met API uses -99999 as default for NaN values
        if el[2].text == "-99999":
            observation_dict[el[0].text] = np.nan
        else:
            observation_dict[el[0].text] = el[2].text

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
