import atexit
import logging
from threading import Thread, Lock, Event
from itertools import count
from typing import Optional, TYPE_CHECKING

from wiederverwendbar.default import Default

from kdsm_manager_task_client.log_formatter import LogFormatter

if TYPE_CHECKING:
    from kdsm_manager_task_client.subtask import Subtask

counter = count(1).__next__


class LogHandler(logging.Handler):
    def __init__(self,
                 subtask: "Subtask",
                 level=logging.NOTSET,
                 buffer_size: int | Default = Default(),
                 buffer_periodical_flush_timing: float | None | Default = Default(),
                 buffer_early_flush_level: int | Default = Default()):
        super().__init__(level=level)

        # subtask
        self._subtask: "Subtask" = subtask

        # set formatter
        self.formatter: LogFormatter = LogFormatter()

        # buffer
        self._buffer: list[logging.LogRecord] = []

        # buffer size
        if type(buffer_size) is Default:
            buffer_size = 100
        self._buffer_size: int = buffer_size

        # buffer_periodical_flush_timing
        if type(buffer_periodical_flush_timing) is Default:
            buffer_periodical_flush_timing = 5.0
        self._buffer_periodical_flush_timing: float | None = buffer_periodical_flush_timing

        # buffer_early_flush_level
        if type(buffer_early_flush_level) is Default:
            buffer_early_flush_level = logging.CRITICAL
        self._buffer_early_flush_level: int = buffer_early_flush_level

        self._buffer_timer_thread: Thread | None = None
        self._buffer_lock: Lock = Lock()
        self._stopper: Optional[callable] = None

        # setup periodical flush
        if self._buffer_periodical_flush_timing is not None:
            # set exit event
            atexit.register(self.close)

            def call_repeatedly(interval: float, func: callable, *args):
                stopped = Event()

                def loop():
                    while not stopped.wait(interval):  # the first call is in `interval` secs
                        func(*args)

                timer_thread = Thread(name=f"{self.__class__.__name__}-{counter()}", target=loop, daemon=True)
                timer_thread.start()
                return stopped.set, timer_thread

            # launch thread
            self._stopper, self._buffer_timer_thread = call_repeatedly(interval=self._buffer_periodical_flush_timing, func=self.flush)

    def emit(self, record: logging.LogRecord) -> None:
        with self._buffer_lock:
            self._buffer.append(record)

        if len(self._buffer) >= self._buffer_size or record.levelno >= self._buffer_early_flush_level:
            self.flush()

    def flush(self):
        if len(self._buffer) == 0:
            return

        with self._buffer_lock:
            formated_records = []
            for record in self._buffer:
                try:
                    formated_record = self.formatter.format(record)
                    formated_records.append(formated_record)
                except Exception:
                    self.handleError(record)
                if len(formated_records) == 0:
                    continue
            self._subtask.log(formated_records=formated_records)
            self.empty_buffer()

    def empty_buffer(self) -> None:
        """
        Empty the buffer list.

        :return: None
        """
        del self._buffer
        self._buffer = []

    def close(self) -> None:
        """
        Clean quit logging. Flush buffer. Stop the periodical thread if needed.

        :return: None
        """

        if self._stopper:
            self._stopper()
        self.flush()
        super().close()
