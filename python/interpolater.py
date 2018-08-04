import time

class Interpolater(object):
    TIME_FORMAT = '%H:%M'

    def __init__(self, schedule):
        self._schedule = schedule

    def interpolate(self, when):
        target = self._to_minutes(when)

        prev = None
        for entry in self._schedule:
            if not prev:
                prev = entry
                continue

            elif self._to_minutes(prev['time']) <= target < self._to_minutes(entry['time']):
                return self.interpolate_entries(prev, entry, when)
            prev = entry

        return self.interpolate_entries(prev, self._schedule[0], when)

    def interpolate_now(self, now):
        return self.interpolate(now.strftime(self.TIME_FORMAT))

    @staticmethod
    def interpolate_entries(lower, higher, target):
        percent = Interpolater.time_percent(lower['time'], higher['time'], target)
        result = {}
        for key in lower.keys():
            if key == 'time':
                continue
            result[key] = Interpolater.interpolate_values(lower[key], higher[key], percent)

        return result

    @staticmethod
    def _to_minutes(when):
        when_t = time.strptime(when, Interpolater.TIME_FORMAT)
        return when_t.tm_hour * 60 + when_t.tm_min

    @staticmethod
    def interpolate_values(val1, val2, percent):
        return (val2 - val1) * percent + val1

    @staticmethod
    def time_percent(earlier, later, target):
        earlier_m = Interpolater._to_minutes(earlier)
        later_m = Interpolater._to_minutes(later)
        target_m = Interpolater._to_minutes(target)

        # assume next day
        if later_m < earlier_m:
            later_m += 24 * 60

        return float(target_m - earlier_m) / (later_m - earlier_m)
