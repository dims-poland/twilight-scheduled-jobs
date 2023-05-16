import datetime
import logging
import typing

import schedule
import tzlocal


class FloatingNextRunJob(schedule.Job):

    def __init__(
            self, interval, scheduler,
            t0_datetime: datetime.datetime,
            resolve_next_t0_datetime_func: typing.Callable,
            resolve_operation_datetime_func: typing.Callable,
            logger: logging.Logger = None,
            **kwargs
    ):
        super().__init__(interval, scheduler)

        self.logger = logger if logger else logging.getLogger('FloatingNextRunJob')

        self.next_t0_datetime = t0_datetime
        self.resolve_next_t0_func = resolve_next_t0_datetime_func
        self.resolve_operation_datetime_func = resolve_operation_datetime_func

    def _schedule_next_run(self) -> None:

        t0_datetime = self.next_t0_datetime
        operation_datetime = self.resolve_operation_datetime_func(t0_datetime=t0_datetime)

        local_tz = tzlocal.get_localzone()
        operation_datetime_local = operation_datetime.astimezone(local_tz).replace(tzinfo=None)

        self.next_run = operation_datetime_local

        self.next_t0_datetime = self.resolve_next_t0_func(
            t0_datetime=t0_datetime,
            operation_datetime=operation_datetime,
            interval_timedelta=datetime.timedelta(seconds=self.interval),
        )

        self.logger.info(
            'Scheduled job for %s (system timezone)',
            self.next_run.strftime('%Y-%m-%d %H:%M'),
        )
    def run(self):
        """
        Run the job and immediately reschedule it.
        If the job's deadline is reached (configured using .until()), the job is not
        run and CancelJob is returned immediately. If the next scheduled run exceeds
        the job's deadline, CancelJob is returned after the execution. In this latter
        case CancelJob takes priority over any other returned value.

        :return: The return value returned by the `job_func`, or CancelJob if the job's
                 deadline is reached.

        """
        if self._is_overdue(datetime.datetime.now()):
            self.logger.debug("Cancelling job %s", self)
            return schedule.CancelJob

        self.logger.debug("Running job %s", self)
        ret = self.job_func()
        self.last_run = datetime.datetime.now()

        if not (isinstance(ret, schedule.CancelJob) or ret is schedule.CancelJob):
            # this condition is a change from the original implementation
            self._schedule_next_run()

            if self._is_overdue(self.next_run):
                self.logger.debug("Cancelling job %s", self)
                return schedule.CancelJob

        return ret


class CustomizableScheduler(schedule.Scheduler):
    def __init__(self, job_class=FloatingNextRunJob):
        super().__init__()
        self.job_class = job_class

    def every(self, interval=1, **kwargs):
        job = self.job_class(interval, self, **kwargs)
        return job

