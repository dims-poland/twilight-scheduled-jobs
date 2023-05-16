import datetime

import pytz
import skyfield.api
from skyfield import almanac


class DatetimeVariableValuesDictFactory:

    sun_meridian_transit_key = 'sun_meridian_transit'
    sun_antimeridian_transit_key = 'sun_antimeridian_transit'
    next_day_prefix = 'next_day_'
    end_suffix = '_end'
    start_suffix = '_start'

    def __init__(
            self, station_geographic_position, timezone=pytz.UTC,
            delta_t=datetime.timedelta(hours=25),
            ts=None,
            max_cache_size=5,
    ):
        eph = skyfield.api.load('de421.bsp')
        self.sun_meridian_transit_func = almanac.meridian_transits(eph, eph['Sun'], station_geographic_position)
        self.dark_twilight_day_func = almanac.dark_twilight_day(eph, station_geographic_position)
        if ts is None:
            self.ts = skyfield.api.load.timescale()
        else:
            self.ts = ts
        self.timezone = timezone
        self.variable_values_dict_cache = dict()
        self.delta_t = delta_t
        self.max_cache_size = max_cache_size

    @property
    def timezone(self):
        return self._timezone

    @timezone.setter
    def timezone(self, value):
        if isinstance(value, str):
            value = pytz.timezone(value)
        self._timezone = value

    # @property
    # def next_day_sun_meridian_transit_key(self):
    #     return self.next_day_prefix + self.sun_meridian_transit_key
    #
    # def next_day_sun_antimeridian_transit_key(self):
    #     return self.next_day_prefix + self.sun_antimeridian_transit_key

    def _has_required_variables(self, required_variable_names, variable_values_dict):
        if required_variable_names is not None:
            for variable_name in required_variable_names:
                if variable_name not in variable_values_dict:
                    return False
        return True

    def create_dict(
            self, t0_datetime, use_cache=True,
            required_variable_names=None,
            delta_t_iterations=5
    ):
        # next_day_sun_meridian_transit_key = self.next_day_sun_meridian_transit_key
        # next_day_sun_antimeridian_transit_key = self.next_day_sun_antimeridian_transit_key

        variable_values_dict = dict()

        if use_cache and t0_datetime in self.variable_values_dict_cache:
            if self._has_required_variables(required_variable_names, self.variable_values_dict_cache[t0_datetime]):
                return self.variable_values_dict_cache[t0_datetime]
            else:
                variable_values_dict = self.variable_values_dict_cache[t0_datetime]

        # delta_t=datetime.timedelta(days=1)
        # delta_t=datetime.timedelta(hours=12)
        # t0_datetime = self.timezone.localize(
        #     datetime.datetime.combine(t0_datetime, datetime.datetime.min.time())
        # )

        # searched_base_variable_names = set()
        #
        # for variable_name in variable_names:
        #     base_variable_name, variable_type = variable_name.rsplit('_')[-1]
        #     searched_base_variable_names.add(base_variable_name)
        #     if variable_type == 'start' and delta_t.days == 0:
        #         delta_t = datetime.timedelta(days=1)

        t_t0_datetime = t0_datetime

        for delta_t_iteration in range(delta_t_iterations):
            t1_datetime = t_t0_datetime + self.delta_t
            t1 = self.ts.from_datetime(t1_datetime)
            t0 = self.ts.from_datetime(t_t0_datetime)

            meridian_times, meridian_events = almanac.find_discrete(t0, t1, self.sun_meridian_transit_func)

            meridian_transit_index = almanac.MERIDIAN_TRANSITS.index('Meridian transit')
            antimeridian_transit_index = almanac.MERIDIAN_TRANSITS.index('Antimeridian transit')

            sun_antimeridian_transit_time = None
            for sun_transit_time, sun_transit_event in zip(meridian_times, meridian_events):
                if sun_transit_event == antimeridian_transit_index:
                    if sun_antimeridian_transit_time is None:
                        sun_antimeridian_transit_time = sun_transit_time
                    if self.sun_antimeridian_transit_key not in variable_values_dict:
                        variable_values_dict[self.sun_antimeridian_transit_key] = sun_transit_time.astimezone(self.timezone)
                    # elif next_day_sun_antimeridian_transit_key not in variable_values_dict:
                    #     variable_values_dict[next_day_sun_antimeridian_transit_key] = sun_transit_time.astimezone(self.timezone)
                elif sun_transit_event == meridian_transit_index:
                    if self.sun_meridian_transit_key not in variable_values_dict:
                        variable_values_dict[self.sun_meridian_transit_key] = sun_transit_time.astimezone(self.timezone)
                    # elif next_day_sun_meridian_transit_key not in variable_values_dict:
                    #     variable_values_dict[next_day_sun_meridian_transit_key] = sun_transit_time.astimezone(self.timezone)

            if sun_antimeridian_transit_time is None:
                raise ValueError('No meridian transit of the Sun found')

            twilight_times, twilight_events = almanac.find_discrete(t0, t1, self.dark_twilight_day_func)
            previous_twilight_event = self.dark_twilight_day_func(t0).item()
            for twilight_time, twilight_event in zip(twilight_times, twilight_events):
                previous_base_variable_name = almanac.TWILIGHTS[previous_twilight_event]  # day
                previous_variable_suffix = '_end'  # day_end
                this_base_variable_name = almanac.TWILIGHTS[twilight_event]  # civil twilight
                this_variable_suffix = '_start'  # civil_twilight_start

                variable_prefix = self.next_day_prefix if previous_twilight_event < twilight_event else ''

                previous_variable_name = (
                        variable_prefix + previous_base_variable_name.lower().replace(' ', '_') +
                        previous_variable_suffix)
                this_variable_name = (
                        variable_prefix + this_base_variable_name.lower().replace(' ', '_') +
                        this_variable_suffix)

                twilight_time_as_datetime = twilight_time.astimezone(self.timezone)

                if previous_variable_name not in variable_values_dict:
                    variable_values_dict[previous_variable_name] = twilight_time_as_datetime
                if this_variable_name not in variable_values_dict:
                    variable_values_dict[this_variable_name] = twilight_time_as_datetime

                previous_twilight_event = twilight_event

            if self._has_required_variables(required_variable_names, variable_values_dict):
                break

            t_t0_datetime = t1_datetime

        if use_cache:
            self.variable_values_dict_cache[t0_datetime] = variable_values_dict

        return variable_values_dict

    def prune_cache(self, valid_datetimes):
        for date in list(self.variable_values_dict_cache.keys()):
            if date not in valid_datetimes:
                del self.variable_values_dict_cache[date]

    def auto_prune_cache(self):
        if len(self.variable_values_dict_cache) > self.max_cache_size:
            self.prune_cache(sorted(self.variable_values_dict_cache.keys())[-self.max_cache_size:])


