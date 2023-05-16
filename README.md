# Twilight-scheduled Jobs

The aim of this project is to provide a simple way to run jobs (single-threaded) to run at local twilight times.
The twilight times are calculated using Skyfiled package.
The scheduling is based on scheduler package.
The main aim is to schedule camera settings change.

## Example schedule file

```yaml
# Timestamps (UTC) are calculated/observed for 2023-05-10 and 2023-05-11.
# 02:32 Civil twilight starts
'@civil_twilight_start':
  iris: 1.4
  gain: 0
  nd_filter: "off"
  ir_filter: "on"
# 03:02: Civil twilight ends, Nautical twilight starts
# 03:03: UFOCapture starts detection
'@nautical_twilight_start':
  gain: 9
'@nautical_twilight_start + 10m':
  gain: 21
'@nautical_twilight_start + 20m':
  gain: 51
# 03:20 Gain=51 (NO IR) is OK
# 03:33 Too bright for Gain=66
# 03:39 Nautical twilight ends, Astronomical twilight starts
'@astronomical_twilight_start':
  gain: 66
# 03:31 Borderline bright for Gain=66
# 03:40 Gain=66 is OK
#'@night_start':
#  gain: 69
# 10:34 Night ends, Astronomical twilight starts
# 11:14 Nautical twilight starts
'@next_day_nautical_twilight_start + 2m':
  gain: 51
'@next_day_nautical_twilight_start + 20m':
  gain: 45
# 11:37 Too bright for Gain=69, Gain=45 is OK
'@next_day_nautical_twilight_start + 25m':
  gain: 39
# 11:38 Too bright for Gain=45, Gain=39 is OK
# 11:44 Too bright for Gain=39, Gain=30 is OK
'@next_day_nautical_twilight_start + 30m':
  gain: 30
# 11:51 Civil twilight starts
# 11:52 UFOCapture stops detection
'@next_day_civil_twilight_start':
  gain: 0
  iris: 22
  ir_filter: "off"
  nd_filter: "1/64"
```