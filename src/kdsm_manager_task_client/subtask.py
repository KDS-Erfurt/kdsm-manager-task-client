import contextlib
import warnings
from abc import ABC, abstractmethod
from threading import Lock
from typing import Literal, Optional, TYPE_CHECKING
import re

from wiederverwendbar.default import Default
from wiederverwendbar.logger import Logger, remove_logger

from kdsm_manager_task_client.log_handler import LogHandler
from kdsm_manager_task_client.subtask_log import SubtaskLogModel
from kdsm_manager_task_client.task_status import TaskStatus

if TYPE_CHECKING:
    from kdsm_manager_task_client.group import Group
    from kdsm_manager_task_client.group import Task


class StepsNotCompletedError(RuntimeError):
    """
    Exception that is triggered if not all steps for the subtask have been completed.
    """


class NoMoreStepsLeftError(RuntimeError):
    """
    Exception that is triggered if no more steps are left.
    """


class StepNotCompletedWarning(RuntimeWarning):
    """
    Warning that is triggered if not all steps for the subtask have been completed.
    """


class Subtask(ABC):
    def __init__(self,
                 name: str | Default = Default(),
                 title: str | None | Default = Default(),
                 steps: int | Default = Default(),
                 if_the_steps_have_not_been_completed: Literal["raise", "warn", "complete", "ignore"] | Default = Default()):
        # groups
        self._group: Optional["Group"] = None

        # thread lock
        self._lock: Lock = Lock()

        # name
        if type(name) is Default:
            name = self.__class__.__name__.lower()
        self._name: str = name

        # title
        if type(title) is Default:
            title: str = ' '.join(re.findall(r'[A-Z][a-z]*|\d+', self.__class__.__name__))
        self._title: str | None = title

        # step
        self._current_step: int = 0

        # steps
        if type(steps) is Default:
            steps = 1
        if steps < self.current_step:
            raise AttributeError(f"Steps must be greater than {self.current_step} for {self}")
        self._steps: int = steps

        # if_the_steps_have_not_been_completed
        if type(if_the_steps_have_not_been_completed) is Default:
            if_the_steps_have_not_been_completed = "raise"
        if_the_steps_have_not_been_completed: Literal["raise", "warn", "complete", "ignore"]
        self._if_the_steps_have_not_been_completed: Literal["raise", "warn", "complete", "ignore"] = if_the_steps_have_not_been_completed

        # log_handler
        self._log_handler: LogHandler | None = None

        # logger
        self._logger: Logger | None = None

        # ended
        self._stopped: bool = False

        # local_abort
        self._local_abort: bool = False

    def __str__(self):
        return (f"{self.__class__.__name__}("
                f"name='{self.name}', "
                f"{'' if self.title is None else f'title={chr(39)}{self.title}{chr(39)}'}, "
                f"status='{self.status.value}', "
                f"percent={self.percent}%"
                f")")

    @property
    def group(self) -> "Group":
        if self._group is None:
            raise AttributeError(f"Group is not set for {self}")
        return self._group

    @group.setter
    def group(self, value: "Group") -> None:
        if self._group is not None:
            raise AttributeError(f"Group is already set for {self}")
        self._group = value

    @property
    def task(self) -> "Task":
        return self.group.task

    @property
    def name(self) -> str:
        return self._name

    @property
    def title(self) -> str | None:
        return self._title

    @property
    def current_step(self) -> int:
        with self._lock:
            return self._current_step

    @current_step.setter
    def current_step(self, new_step: int) -> None:
        if new_step > self.steps:
            raise AttributeError(f"Step must be less than {self.steps} for {self}")

        with self._lock:
            self._current_step = new_step

        # calculate percent
        self.percent = self.current_step / self.steps * 100

    def next_step(self) -> None:
        self.current_step += 1

    @contextlib.contextmanager
    def step(self, new_status_text: str | None = None, log: bool = False):
        if self.steps_left == 0:
            raise NoMoreStepsLeftError(f"No more steps left for {self}!")
        if new_status_text is not None:
            self.status_text(new_status_text=new_status_text, log=log)
        yield
        self.next_step()

    @property
    def steps(self) -> int:
        with self._lock:
            return self._steps

    @steps.setter
    def steps(self, new_steps: int) -> None:
        if self.current_step > new_steps:
            raise AttributeError(f"Steps must be more than {self.current_step} for {self}")

        with self._lock:
            self._steps = new_steps

        # calculate percent
        self.percent = self.current_step / self.steps * 100

    @property
    def steps_left(self) -> int:
        steps_left = self.steps - self.current_step
        if steps_left < 0:
            return 0
        return steps_left

    @property
    def if_the_steps_have_not_been_completed(self) -> Literal["raise", "warn", "complete", "ignore"]:
        with self._lock:
            return self._if_the_steps_have_not_been_completed

    @if_the_steps_have_not_been_completed.setter
    def if_the_steps_have_not_been_completed(self, new_value: Literal["raise", "warn", "complete", "ignore"]) -> None:
        with self._lock:
            self._if_the_steps_have_not_been_completed = new_value

    @property
    def percent(self) -> float:
        return self.task.request(method="GET",
                                 url=self.task.api_url + f"/task/subtask/{self.name}/percent",
                                 response_model=float)

    @percent.setter
    def percent(self, new_percent: float) -> None:
        self.task.request(method="PUT",
                          url=self.task.api_url + f"/task/subtask/{self.name}/percent",
                          params={"new_percent": new_percent})

    @property
    def status(self) -> TaskStatus:
        return self.task.request(method="GET",
                                 url=self.task.api_url + f"/task/subtask/{self.name}/status",
                                 response_model=TaskStatus)

    @status.setter
    def status(self, new_status: TaskStatus) -> None:
        self.task.request(method="PUT",
                          url=self.task.api_url + f"/task/subtask/{self.name}/status",
                          params={"new_status": new_status.value})

    def status_text(self, new_status_text: str = "", log: bool = False) -> None:
        self.task.request(method="PUT",
                          url=self.task.api_url + f"/task/subtask/{self.name}/status-text",
                          params={"new_status_text": new_status_text})
        if log:
            self.logger.info(new_status_text)

    @property
    def abort(self) -> bool:
        if self.task.abort:
            return self.task.abort
        with self._lock:
            if self._local_abort:
                return self._local_abort
        return self.task.request(method="GET",
                                 url=self.task.api_url + f"/task/subtask/{self.name}/abort",
                                 response_model=bool)

    @abort.setter
    def abort(self, value: bool) -> None:
        with self._lock:
            self._local_abort = value

    @property
    def logger(self) -> Logger:
        if self._logger is not None:
            return self._logger

        if self.status in [TaskStatus.ABORTED, TaskStatus.FAILED, TaskStatus.SUCCESS]:
            raise RuntimeError(f"Can't create logger for {self}, because subtask is in state '{self.status.value}'!")

        # create LogHandler
        self._log_handler = LogHandler(subtask=self)

        # create logger
        self._logger: Logger = Logger(name=f"{self.group.logger.name}.{self.name}", settings=self.task.settings)

        # set log handler
        self._logger.addHandler(self._log_handler)

        return self._logger

    def log(self, formated_records: list[SubtaskLogModel]) -> None:
        if len(formated_records) == 0:
            return
        self.task.request(method="POST",
                          url=self.task.api_url + f"/task/subtask/{self.name}/log",
                          json=[formated_record.model_dump() for formated_record in formated_records])

    def start(self) -> None:
        if self._stopped:
            raise RuntimeError(f"Subtask {self} is stopped!")

        # log fist message
        self.logger.debug("Subtask started.")

    def stop(self, final_status: TaskStatus) -> None:
        if self._stopped:
            raise RuntimeError(f"Subtask {self} is already stopped!")

        # check if steps left
        if self.steps_left > 0 and final_status == TaskStatus.SUCCESS:
            msg = f"Not all steps for {self} have been completed! -> {self.steps_left} left."
            if self.if_the_steps_have_not_been_completed == "raise":
                try:
                    raise StepsNotCompletedError(msg)
                except StepsNotCompletedError as e:
                    raise e
            elif self.if_the_steps_have_not_been_completed == "warn":
                self.logger.warning(msg)
                warnings.warn(StepNotCompletedWarning(msg))
            elif self.if_the_steps_have_not_been_completed == "complete":
                self.current_step = self.steps

        # log last message
        self.logger.debug(f"Subtask ended with status '{final_status.value}'.")

        # close log handler
        self._log_handler.close()
        self._log_handler = None

        # delete logger
        remove_logger(self._logger)
        self._logger = None

    @abstractmethod
    def payload(self):
        ...
