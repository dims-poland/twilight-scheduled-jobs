import datetime
import operator

import dateutil.parser
import pytimeparse.timeparse
import pytz
import yaml

def parse_timestamp_syntax(
        settings_operation_key,
        timestamp_variables=None,
        replace_variables=False,
        skip_missing_variables=True,
        variable_marker='@',
        fallback_timezone='UTC'
):
    if isinstance(fallback_timezone, str):
        fallback_timezone = pytz.timezone(fallback_timezone)
    parsed_timestamp_expression = []
    base_time_present = False
    parts = settings_operation_key.split(' + ')
    for part_i, part in enumerate(parts):
        if part_i > 0:
            parsed_timestamp_expression.append(operator.add)
        subparts = part.strip().split(' - ')
        for subpart_j, subpart in enumerate(subparts):
            if subpart_j > 0:
                parsed_timestamp_expression.append(operator.sub)
            subpart_stripped = subpart.strip()
            if subpart_stripped.startswith(variable_marker):
                if base_time_present:
                    raise ValueError(f'Variable {subpart_stripped} found after base time was already recognized.')
                variable_name = subpart_stripped[1:]
                if replace_variables:
                    if timestamp_variables is None:
                        raise ValueError('Timestamp variables must be specified if replace_variables is True.')
                    if variable_name in timestamp_variables:
                        parsed_timestamp_expression.append(timestamp_variables[variable_name])
                    elif skip_missing_variables:
                        parsed_timestamp_expression.append(variable_name)
                    else:
                        raise ValueError(f'Variable {variable_name} not found in timestamp variables.')
                else:
                    parsed_timestamp_expression.append(variable_name)
                base_time_present = True
            else:
                maybe_seconds = pytimeparse.timeparse.timeparse(subpart_stripped)
                if maybe_seconds is not None:
                    parsed_timestamp_expression.append(datetime.timedelta(seconds=maybe_seconds))
                else:
                    try:
                        base_time = dateutil.parser.parse(subpart_stripped)
                        if base_time.tzinfo is None:
                            base_time = fallback_timezone.localize(base_time)
                    except Exception as e:
                        raise ValueError(f'Could not parse {subpart_stripped} as a datetime.') from e
                    parsed_timestamp_expression.append(base_time)
    return tuple(parsed_timestamp_expression)


def find_variables(datetime_expression):
    variables = set()
    if isinstance(datetime_expression, str):
        datetime_expression = (datetime_expression,)
    for part in datetime_expression:
        if isinstance(part, str):
            variables.add(part)
    return variables


def resolve_variables(datetime_expression, variable_values_dict):
    if isinstance(datetime_expression, str):
        datetime_expression = (datetime_expression,)
    complete_timestamp_expression = list(datetime_expression)
    for i, part in enumerate(datetime_expression):
        if isinstance(part, str):
            if part in variable_values_dict:
                complete_timestamp_expression[i] = variable_values_dict[part]
            else:
                raise ValueError(f'Variable {part} not found in timestamp variables.')
    return tuple(complete_timestamp_expression)


def evaluate_resolved_expression(datetime_expression):
    if isinstance(datetime_expression, str):
        datetime_expression = (datetime_expression,)
    result = datetime_expression[0]
    for i in range(1, len(datetime_expression), 2):
        operator = datetime_expression[i]
        operand = datetime_expression[i + 1]
        result = operator(result, operand)
    return result


def evaluate_datetime_expression(
        datetime_expression,
        variable_values_dict
):
    datetime_expression = resolve_variables(
        datetime_expression, variable_values_dict
    )
    return evaluate_resolved_expression(datetime_expression)


def slugify_datetime_expression(datetime_expression, separator='_'):
    import slugify

    if isinstance(datetime_expression, str):
        datetime_expression = (datetime_expression,)
    slug = []
    for part in datetime_expression:
        if isinstance(part, str):
            part_stripped = part.strip()
            if part_stripped == '+':
                slug.append('plus')
            elif part_stripped == '-':
                slug.append('minus')
            else:
                slug.append(part)
        elif isinstance(part, datetime.datetime):
            slug.append(part.strftime('%Y%m%d_%H%M%S'))
        elif isinstance(part, datetime.timedelta):
            slug.append(f'{part.total_seconds()}s')
        elif part is operator.add:
            slug.append('plus')
        elif part is operator.sub:
            slug.append('minus')
        else:
            raise ValueError(f'Unknown part {part} in datetime expression.')

    slug_str = separator.join(slug)
    slugified_str = slugify.slugify(slug_str, separator=separator)

    return slugified_str


def load_job_settings_dict_yaml(
        pathname,
        timestamp_variables=None, replace_variables=False,
        skip_missing_variables=True,
        fallback_timezone='UTC',
        variable_marker='@',
):
    with open(pathname) as f:
        yaml_data = yaml.safe_load(f)

    parsed_data = {}
    for key, value in yaml_data.items():
        parsed_key = parse_timestamp_syntax(
            settings_operation_key=key,
            timestamp_variables=timestamp_variables,
            replace_variables=replace_variables,
            variable_marker=variable_marker,
            fallback_timezone=fallback_timezone,
            skip_missing_variables=skip_missing_variables
        )
        parsed_data[parsed_key] = value

    return parsed_data
