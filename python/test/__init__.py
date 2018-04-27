import unittest

from interpolater import Interpolater

class TestInterpolater(unittest.TestCase):
    SCHEDULE = [
        {
            'time': '00:00',
            'color_temperature': 1000,
            'brightness': 100
        },
        {
            'time': '12:00',
            'color_temperature': 3000,
            'brightness': 50
        },
        {
            'time': '18:00',
            'color_temperature': 3000,
            'brightness': 150
        }
    ]

    def test_nterpolate_values(self):
        self.assertEqual(50, Interpolater.interpolate_values(0, 100, 0.5))
        self.assertEqual(50, Interpolater.interpolate_values(100, 0, 0.5))
        self.assertEqual(25, Interpolater.interpolate_values(0, 100, 0.25))
        self.assertEqual(75, Interpolater.interpolate_values(0, 100, 0.75))
        self.assertEqual(0, Interpolater.interpolate_values(0, 100, 0))
        self.assertEqual(100, Interpolater.interpolate_values(0, 100, 1))

        self.assertEqual(150, Interpolater.interpolate_values(100, 200, 0.5))
        self.assertEqual(150, Interpolater.interpolate_values(200, 100, 0.5))
        self.assertEqual(0, Interpolater.interpolate_values(-50, 50, 0.5))
        self.assertEqual(0, Interpolater.interpolate_values(0, 100, 0))

    def test_time_percent(self):
        self.assertEqual(0.5, Interpolater.time_percent('00:00', '12:00', '06:00'))
        self.assertEqual(0.5, Interpolater.time_percent('06:00', '18:00', '12:00'))
        self.assertEqual(1.0/12, Interpolater.time_percent('00:00', '12:00', '01:00'))
        self.assertEqual(0.5, Interpolater.time_percent('12:00', '00:00', '18:00'))
        self.assertEqual(0.5, Interpolater.time_percent('18:00', '00:00', '21:00'))

    def test_interpolate_entries(self):
        entry1 = {
            'time': '00:00',
            'color_temperature': 1000,
            'brightness': 100
        }
        entry2 = {
            'time': '12:00',
            'color_temperature': 3000,
            'brightness': 50
        }
        expected_entry = {
            'color_temperature': 2000,
            'brightness': 75
        }
        entry3 = Interpolater.interpolate_entries(entry1, entry2, '06:00')
        self.assertEqual(expected_entry, entry3)

    def test_schedule_0(self):
        i = Interpolater(self.SCHEDULE)
        entry = i.interpolate('00:00')
        expected_entry = {
            'color_temperature': 1000,
            'brightness': 100
            }
        self.assertEqual(expected_entry, entry)

    def test_schedule_1(self):
        i = Interpolater(self.SCHEDULE)
        entry = i.interpolate('12:00')
        expected_entry = {
            'color_temperature': 3000,
            'brightness': 50
            }
        self.assertEqual(expected_entry, entry)


    def test_schedule_2(self):
        i = Interpolater(self.SCHEDULE)
        entry = i.interpolate('06:00')
        expected_entry = {
            'color_temperature': 2000,
            'brightness': 75
            }
        self.assertEqual(expected_entry, entry)

    def test_schedule_3(self):
        i = Interpolater(self.SCHEDULE)
        entry = i.interpolate('21:00')
        expected_entry = {
            'color_temperature': 2000,
            'brightness': 125
            }
        self.assertEqual(expected_entry, entry)
