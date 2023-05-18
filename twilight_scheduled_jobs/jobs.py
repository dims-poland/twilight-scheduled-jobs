import datetime
import hashlib
import json
import logging
import time
from functools import partial

import pytimeparse.timeparse
import schedule

from .safe_termination import terminate_flag as safe_termination_terminate_flag
from .next_job_datetime import resolve_next_t0_datetime, resolve_operation_datetime
from .parser import slugify_datetime_expression, find_variables
from .defaults import DEFAULTS


def initialize_jobs(
        datetime_expression,
        next_t0_datetime_expression,
        start_t0,
        settings_job_func,
        create_dict_func,
        logger,
        scheduler,
        apply_settings_job_logger_name_format=DEFAULTS['scheduled_job_logger_name_format'],
        t0_step=datetime.timedelta(seconds=pytimeparse.timeparse.timeparse(DEFAULTS['t0_step'])),
):
    scheduled_camera_settings_jobs_dict = dict()
    # scheduled_job_datetimes = set()

    resolve_next_t0_datetime_partial_func = partial(
        resolve_next_t0_datetime,
        next_t0_datetime_expression=next_t0_datetime_expression,
        create_dict_func=create_dict_func,
    )

    for datetime_expression, settings_dict in datetime_expression.items():
        resolve_operation_datetime_partial_func = partial(
            resolve_operation_datetime,
            operation_datetime_expression=datetime_expression,
            create_dict_func=create_dict_func,
        )

        datetime_expression_slug = slugify_datetime_expression(datetime_expression)

        settings_dict_json_str = json.dumps(settings_dict)
        settings_dict_json_str_truncated = settings_dict_json_str[:100] + '...' if len(settings_dict_json_str) > 100 else settings_dict_json_str
        settings_hash = hashlib.md5(settings_dict_json_str.encode('utf-8')).hexdigest()[:8]

        logger.info(
            'Initializing camera settings job for. %s: %s',  #
            settings_hash,
            settings_dict_json_str_truncated,
        )

        logger_name = apply_settings_job_logger_name_format.format(
            datetime_expression=datetime_expression_slug,
            settings_hash=settings_hash
        )
        job_logger = logging.getLogger(logger_name)

        apply_settings_job_partial_func = partial(
            settings_job_func,
            logger=job_logger,
            settings_dict=settings_dict,
            run_once=len(find_variables(datetime_expression)) == 0
        )
        change_camera_settings_job = scheduler.every(
            interval=int(t0_step.total_seconds()),
            t0_datetime=start_t0,
            resolve_next_t0_datetime_func=resolve_next_t0_datetime_partial_func,
            resolve_operation_datetime_func=resolve_operation_datetime_partial_func,
            logger=job_logger,
        ).seconds.do(apply_settings_job_partial_func)

        scheduled_camera_settings_jobs_dict[datetime_expression] = change_camera_settings_job

    return scheduled_camera_settings_jobs_dict


def run_pending_loop(
        scheduler,
        logger,
        schedule_pending_check_interval=DEFAULTS['schedule_pending_check_interval'],
):
    logger.debug('Starting scheduled camera settings loop')
    while not safe_termination_terminate_flag:
        try:
            scheduler.run_pending()
        except KeyboardInterrupt:
            logger.info('Keyboard interrupt received. Exiting.')
            break
        except Exception as e:
            logger.error('Error in scheduled camera settings loop [%s]: %s'.format(str(e)))

        time.sleep(schedule_pending_check_interval)


def run_job_wrapper(
        settings_dict,
        logger,
        apply_settings_job_func,
        datetime_variable_values_dict_factory,
        run_once=False,
        **kwargs
):
    apply_settings_job_func(**{
        **kwargs,
        **dict(
            settings_dict=settings_dict,
            logger=logger,
        )
    })
    datetime_variable_values_dict_factory.auto_prune_cache()
    if run_once:
        return schedule.CancelJob
    return None
