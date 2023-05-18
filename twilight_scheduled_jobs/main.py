import datetime
import logging
from functools import partial

import dateutil.parser
import pytimeparse.timeparse
import pytz as pytz

from .floating_next_run_job import CustomizableScheduler, FloatingNextRunJob
from .datetime_variables import DatetimeVariableValuesDictFactory
from .parser import load_job_settings_dict_yaml, parse_timestamp_syntax

from .jobs import run_job_wrapper, initialize_jobs, run_pending_loop
from .defaults import DEFAULTS

DEFAULT_LOGGER_NAME = 'scheduled_twilight_operation'


def twilight_scheduled_jobs_main(
        schedule_file,
        station_geographic_position,
        settings_job_func,
        current_datetime=None,
        timezone=DEFAULTS['timezone'],
        variable_marker=DEFAULTS['variable_marker'],
        next_t0_expression=DEFAULTS['next_t0_expression'],
        delta_t=DEFAULTS['delta_t'],
        t0_step=DEFAULTS['t0_step'],
        schedule_pending_check_interval=DEFAULTS['schedule_pending_check_interval'],
        job_logger_name_format=DEFAULTS['scheduled_job_logger_name_format'],
        logger=None,
):
    current_datetime = dateutil.parser.parse(current_datetime) \
        if isinstance(current_datetime, str) \
        else current_datetime

    if logger is None:
        logger = logging.getLogger(DEFAULT_LOGGER_NAME)

    current_datetime = datetime.datetime.now(pytz.timezone(timezone)) \
        if current_datetime is None \
        else current_datetime

    timezone = pytz.timezone(timezone)
    job_settings_by_datetime_expression = load_job_settings_dict_yaml(
        pathname=schedule_file,
        fallback_timezone=timezone,
        timestamp_variables=dict(
            parse_time=datetime.datetime.now(timezone)
        ),
        replace_variables=True,
        skip_missing_variables=True,
        variable_marker=variable_marker,
    )

    next_t0_datetime_expression = parse_timestamp_syntax(next_t0_expression)
    delta_t = datetime.timedelta(seconds=pytimeparse.timeparse.timeparse(delta_t))
    t0_step = datetime.timedelta(seconds=pytimeparse.timeparse.timeparse(t0_step))

    datetime_variable_values_dict_factory = DatetimeVariableValuesDictFactory(
        station_geographic_position=station_geographic_position,
        timezone=timezone,
        delta_t=delta_t
    )

    run_job_wrapper_partial_func = partial(
        run_job_wrapper,
        settings_job_func=settings_job_func,
        datetime_variable_values_dict_factory=datetime_variable_values_dict_factory,
    )

    create_dict_partial_func = partial(
        datetime_variable_values_dict_factory.create_dict,
        use_cache=True,
    )

    scheduler = CustomizableScheduler(job_class=FloatingNextRunJob)

    scheduled_camera_settings_jobs_dict = \
        initialize_jobs(
            scheduler=scheduler,
            start_t0=current_datetime,
            datetime_expression=job_settings_by_datetime_expression,
            next_t0_datetime_expression=next_t0_datetime_expression,
            settings_job_func=run_job_wrapper_partial_func,
            t0_step=t0_step,
            create_dict_func=create_dict_partial_func,
            logger=logger,
            apply_settings_job_logger_name_format=job_logger_name_format,
        )

    run_pending_loop(
        scheduler=scheduler,
        logger=logger,
        schedule_pending_check_interval=schedule_pending_check_interval,
    )

    # returns when safe termination flag is set or KeyboardInterrupt caught in run_pending_loop
    return scheduled_camera_settings_jobs_dict
