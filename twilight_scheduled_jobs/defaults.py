DEFAULTS = dict(
        schedule_pending_check_interval=10,
        next_t0_expression='@sun_meridian_transit',
        variable_marker='@',
        scheduled_job_logger_name_format='scheduled_camera_settings_changer.job_{datetime_expression}_{settings_hash}',
        delta_t='25h',
        t0_step='23h',
)