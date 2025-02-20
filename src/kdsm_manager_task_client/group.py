from typing import TYPE_CHECKING, Optional
from itertools import count

from wiederverwendbar.default import Default
from wiederverwendbar.logger import Logger, remove_logger
from wiederverwendbar.threading import ExtendedThread

from kdsm_manager_task_client.task_status import TaskStatus
from kdsm_manager_task_client.subtask import Subtask

if TYPE_CHECKING:
    from kdsm_manager_task_client.task import Task

counter = count(1).__next__


class Group(ExtendedThread):
    def __init__(self, *subtasks: Subtask):
        # task
        self._task: Optional["Task"] = None

        # subtasks
        self._subtasks: tuple[Subtask, ...] = subtasks
        for subtask in self.subtasks:
            subtask.group = self

        super().__init__(group=None,
                         target=Default(),
                         name=f"{self.__class__.__name__}-{counter()}",
                         args=Default(),
                         kwargs=Default(),
                         daemon=Default(),
                         cls_name=Default(),
                         logger=Default(),
                         ignore_stop=Default(),
                         loop_disabled=True,
                         loop_sleep_time=Default(),
                         loop_stop_on_other_exception=True,
                         continue_exceptions=Default(),
                         stop_exceptions=Default(),
                         kill_exceptions=Default(),
                         watchdog_target=Default(),
                         auto_start=False)

    @property
    def task(self) -> "Task":
        if self._task is None:
            raise AttributeError(f"Task is not set for {self}")
        return self._task

    @task.setter
    def task(self, value: "Task") -> None:
        if self._task is not None:
            raise AttributeError(f"Task is already set for {self}")
        self._task = value

        # set logger
        remove_logger(self._logger)
        self._logger: Logger = Logger(name=f"{self.task.logger.name}.{self.name.lower()}", settings=self.task.settings)

    @property
    def subtasks(self) -> tuple[Subtask, ...]:
        return self._subtasks

    def _set_subtask_status(self, subtask: Subtask, new_status: TaskStatus) -> None:
        self.logger.debug(f"Setting subtask '{subtask.name}' status to '{new_status.value}'.")
        subtask.status = new_status

    def loop(self) -> None:
        for subtask in self.subtasks:
            # set subtask to status running
            self._set_subtask_status(subtask=subtask, new_status=TaskStatus.RUNNING)

            # start subtask
            subtask.start()

            # running payload
            try:
                subtask.payload()
                subtask.stop(final_status=TaskStatus.SUCCESS)
                self._set_subtask_status(subtask=subtask, new_status=TaskStatus.SUCCESS)
            except Exception as e:
                subtask.logger.exception(f"Subtask failed with exception:")
                subtask.stop(final_status=TaskStatus.FAILED)
                self._set_subtask_status(subtask=subtask, new_status=TaskStatus.FAILED)
                raise e

    def on_end(self) -> None:
        for subtask in self.subtasks:
            if subtask.status in [TaskStatus.DEPLOYED, TaskStatus.RUNNING]:
                self._set_subtask_status(subtask=subtask, new_status=TaskStatus.ABORTED)
