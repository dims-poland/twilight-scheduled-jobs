import datetime

import skyfield.api
from pytz import timezone
from skyfield import almanac


station_locations = dict(
    tara=skyfield.api.wgs84.latlon(39.3384, -112.70082, elevation_m=1400),
    brm=skyfield.api.wgs84.latlon(39.1885, -112.71195, elevation_m=1415),
)

def demo_calculation():
    geographic = station_locations['tara']

    # Figure out local midnight.
    # zone = timezone('US/Eastern')
    zone = timezone('UTC')
    now = zone.localize(datetime.datetime.now())
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    next_midnight = midnight + datetime.timedelta(days=1)

    ts = skyfield.api.load.timescale()
    t0 = ts.from_datetime(midnight)
    t1 = ts.from_datetime(next_midnight)
    eph = skyfield.api.load('de421.bsp')
    f = almanac.dark_twilight_day(eph, geographic)
    times, events = almanac.find_discrete(t0, t1, f)

    # print(f)

    previous_e = f(t0).item()
    for t, e in zip(times, events):
        tstr = str(t.astimezone(zone))[:16]
        if previous_e < e:
            print(tstr, ' ', almanac.TWILIGHTS[e], 'starts')
        else:
            print(tstr, ' ', almanac.TWILIGHTS[previous_e], 'ends')
        previous_e = e

        topos = eph['earth'] + geographic
        sun_astrometric = topos.at(t).observe(eph['sun'])
        moon_astrometric = topos.at(t).observe(eph['moon'])

        print('     sun alt, az: ', sun_astrometric.apparent().altaz())
        print('     moon alt, az: ', moon_astrometric.apparent().altaz())
