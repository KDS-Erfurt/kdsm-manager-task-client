import logging
from typing import Any

from kdsm_manager_task_client.subtask_log import SubtaskLogModel


class LogFormatter(logging.Formatter):
    DEFAULT_PROPERTIES = set(logging.LogRecord('', 0, '', 0, '', (), (None, None, None), '').__dict__.keys())
    DEFAULT_PROPERTIES.add("message")

    def format(self, record) -> SubtaskLogModel:
        """
        Formats LogRecord into python dictionary.

        :param record: LogRecord instance.
        :return: dict
        """

        # standard entry
        entry: dict[str, Any] = {
            "timestamp": record.created,
            "log_level": record.levelname,
            "thread": record.thread,
            "thread_name": record.threadName,
            "message": record.getMessage(),
            "logger_name": record.name,
            "file_name": record.pathname,
            "module": record.module,
            "method": record.funcName,
            "line_number": record.lineno
        }

        # add exception information if present
        if record.exc_info is not None:
            # noinspection PyTypeChecker
            exception = {
                "message": str(record.exc_info[1]),
                "code": 0,
                "stack_trace": self.formatException(record.exc_info)
            }
            entry["exception"] = exception

        # add extra information
        if len(self.DEFAULT_PROPERTIES) != len(record.__dict__):
            contextual_extra = set(record.__dict__).difference(self.DEFAULT_PROPERTIES)
            if contextual_extra:
                extra = {}
                for key in contextual_extra:
                    extra[key] = record.__dict__[key]
                entry["extra"] = extra

        entry_model = SubtaskLogModel(**entry)

        return entry_model
