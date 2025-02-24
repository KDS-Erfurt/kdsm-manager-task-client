import json
from typing import Literal, Any
import threading

from pydantic import BaseModel
from requests import request
from requests.exceptions import HTTPError, JSONDecodeError
from wiederverwendbar.default import Default
from wiederverwendbar.logger import Logger

from kdsm_manager_task_client.bearer_auth import BearerAuth
from kdsm_manager_task_client.group import Group
from kdsm_manager_task_client.task_status import TaskStatus
from kdsm_manager_task_client.settings import Settings
from kdsm_manager_task_client.subtask import Subtask


class Task:
    def __init__(self,
                 settings: Settings | Default = Default(),
                 id: int | Default = Default(),
                 api_token: str | Default = Default(),
                 api_url: str | Default = Default(),
                 ssl: bool | Default = Default(),
                 ssl_verify: bool | Default = Default()):
        # settings
        if type(settings) is Default:
            settings = Settings()
        self._settings = settings

        # id
        if type(id) is not Default:
            self._settings.id = id
        if self._settings.id is None:
            raise ValueError(f"Task id is not set!")

        # api_token
        if type(api_token) is not Default:
            self._settings.api_token = api_token
        if self._settings.api_token is None:
            raise ValueError(f"Task api_token is not set!")

        # api_url
        if type(api_url) is not Default:
            self._settings.api_url = api_url
        if self._settings.api_url is None:
            raise ValueError(f"Task api_url is not set!")

        # ssl
        if type(ssl) is not Default:
            self._settings.ssl = ssl
        if self._settings.ssl is None:
            raise ValueError(f"Task ssl is not set!")

        # ssl_verify
        if type(ssl_verify) is not Default:
            self._settings.ssl_verify = ssl_verify
        if self._settings.ssl_verify is None:
            raise ValueError(f"Task ssl_verify is not set!")

        # lock
        self._lock: threading.Lock = threading.Lock()

        # bearer_auth
        self._bearer_auth: BearerAuth = BearerAuth(task=self)

        # logger
        self._logger: Logger = Logger(name=f"task.{self.name}", settings=self.settings)

        # groups
        self._groups: list[Group] = []

        # local_abort
        self._local_abort: bool = False

    def __str__(self):
        return (f"{self.__class__.__name__}("
                f"id={self.id}, "
                f"name='{self.name}', "
                f"{'' if self.title is None else f'title={chr(39)}{self.title}{chr(39)}'}, "
                f"status='{self.status.value}', "
                f"percent={self.percent}%"
                f")")

    def __call__(self) -> None:
        return self.run()

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def id(self) -> int:
        return self.settings.id

    @property
    def api_token(self) -> str:
        return self.settings.api_token

    @property
    def api_url(self) -> str:
        if not self.ssl:
            # noinspection HttpUrlsUsage
            api_url = "http://" + self.settings.api_url
        else:
            api_url = "https://" + self.settings.api_url
        return api_url

    @property
    def ssl(self) -> bool:
        return self.settings.ssl

    @property
    def ssl_verify(self) -> bool:
        return self.settings.ssl_verify

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def groups(self) -> tuple[Group, ...]:
        return tuple(self._groups)

    @property
    def subtasks(self) -> tuple[Subtask, ...]:
        subtasks = []
        for group in self.groups:
            subtasks.extend(group.subtasks)
        return tuple(subtasks)

    @property
    def name(self) -> str:
        return self.request(method="GET",
                            url=self.api_url + "/task/name",
                            response_model=str)

    @property
    def title(self) -> str | None:
        return self.request(method="GET",
                            url=self.api_url + "/task/title")

    @property
    def data(self) -> dict[str, Any]:
        return self.request(method="GET",
                            url=self.api_url + "/task/data",
                            response_model=dict)

    @property
    def percent(self) -> float:
        return self.request(method="GET",
                            url=self.api_url + "/task/percent",
                            response_model=float)

    @property
    def status(self) -> TaskStatus:
        return self.request(method="GET",
                            url=self.api_url + "/task/status",
                            response_model=TaskStatus)

    @property
    def abort(self) -> bool:
        with self._lock:
            return self._local_abort

    @abort.setter
    def abort(self, value: bool) -> None:
        with self._lock:
            self._local_abort = value

    def request(self,
                method: Literal["GET", "POST", "PUT"],
                url: str,
                response_model: type | None = None,
                **kwargs) -> Any:
        # prepare kwargs for request
        if self.ssl:
            if "verify" not in kwargs:
                kwargs["verify"] = self.ssl_verify
        if "auth" not in kwargs:
            kwargs["auth"] = self._bearer_auth

        # do request
        response = request(method, url, **kwargs)

        # parse response to json
        try:
            response_data = response.json()
        except JSONDecodeError:
            response_data = response.text

        # handle non-ok status coder
        if not response.ok:
            detail = response.reason
            if type(response_data) is str:
                detail += " - " + response_data
            elif type(response_data) is dict:
                if "detail" in response_data:
                    response_data_pretty = json.dumps(response_data["detail"], indent=4)
                else:
                    response_data_pretty = json.dumps(response_data, indent=4)
                detail += " - " + response_data_pretty
            raise HTTPError(detail, response=response)

        # parse to response_model
        if response_model is not None:
            if issubclass(response_model, BaseModel):
                result = response_model(**response.json())
            else:
                result = response_model(response.json())
        else:
            result = response.json()

        return result

    def subtask(self, *subtasks_or_groups: Subtask | Group, delete_subtasks: bool = False) -> None:
        current_subtasks = []

        def create_dynamic_group():
            if len(current_subtasks) == 0:
                return
            self._groups.append(Group(*current_subtasks))
            current_subtasks.clear()

        for subtask_or_group in subtasks_or_groups:
            if isinstance(subtask_or_group, Subtask):
                current_subtasks.append(subtask_or_group)
            elif isinstance(subtask_or_group, Group):
                create_dynamic_group()
                self._groups.append(subtask_or_group)
        create_dynamic_group()

        # submit subtasks
        self.request(method="POST",
                     url=self.api_url + "/task/subtasks",
                     params={"delete_subtasks": delete_subtasks},
                     json=[{
                         "name": subtask.name,
                         "title": subtask.title
                     } for subtask in self.subtasks])

        # set task to groups
        for group in self.groups:
            group.task = self

    def run(self) -> None:
        self.logger.debug("Task started.")

        # start groups
        for group in self.groups:
            if group.started_at is not None:
                continue
            group.start()

        # wait for groups
        while True:
            all_groups_finished = True
            for group in self.groups:
                if group.ended_at is None:
                    all_groups_finished = False
                    break
            if all_groups_finished:
                break

        self.logger.debug("Task ended.")
