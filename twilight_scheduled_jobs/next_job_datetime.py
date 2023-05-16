import datetime

from twilight_scheduled_jobs.parser import find_variables, evaluate_datetime_expression


def resolve_next_t0_datetime(
        t0_datetime,
        operation_datetime,
        interval_timedelta,
        next_t0_datetime_expression,
        create_dict_func,
        datetime_variable_values=None,
):
    required_variable_names = find_variables(next_t0_datetime_expression)
    if datetime_variable_values is None:
        datetime_variable_values = create_dict_func(
            t0_datetime=t0_datetime,
            required_variable_names=required_variable_names
        )
    next_t0_datetime = evaluate_datetime_expression(
        next_t0_datetime_expression,
        datetime_variable_values
    )
    if operation_datetime > next_t0_datetime:
        datetime_variable_values = create_dict_func(
            t0_datetime=next_t0_datetime + interval_timedelta,
            required_variable_names=required_variable_names
        )
        next_t0_datetime = evaluate_datetime_expression(
            next_t0_datetime_expression,
            datetime_variable_values
        )
        if next_t0_datetime < operation_datetime:
            # Unexpected state, should not happen
            raise RuntimeError('Cannot continue. next_t0_datetime < operation_datetime.')

    return next_t0_datetime


def resolve_operation_datetime(
        t0_datetime,
        operation_datetime_expression,
        create_dict_func,
):
    required_variable_names = find_variables(operation_datetime_expression)

    datetime_variable_values = create_dict_func(
        t0_datetime=t0_datetime,
        required_variable_names=required_variable_names
    )

    operation_datetime = evaluate_datetime_expression(operation_datetime_expression, datetime_variable_values)

    return operation_datetime
