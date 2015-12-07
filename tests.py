import unittest
from datetime import time

import pytz

from metnopy import get_met_data


class TestGetMetData(unittest.TestCase):

    def test_get_met_data_works(self):
        response = get_met_data("2", "18700", "TA, TAX", "2015-11-10", "2015-11-13", "0", "",
                                     pytz.timezone("Europe/Oslo"))
        self.assertEqual(response.shape, (4, 2))
        self.assertEqual(response.index.time[0], time(1, 0))

    def test_get_met_data_long_format(self):
        response = get_met_data("2", "18700, 68860", "TA, RR_12",
                                "2015-12-06", "2015-12-07", "6,18", "", long_format=True)
        self.assertEqual(response.shape, (6, 4))
