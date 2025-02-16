from typing import Literal, Any, Self
import json

from requests import request, PreparedRequest
from requests.auth import AuthBase
from requests.exceptions import HTTPError, JSONDecodeError
from wiederverwendbar.default import Default

from kdsm_manager_task_client.task_status import TaskStatus


class TaskClient:
    class BearerAuth(AuthBase):
        def __init__(self,
                     task_client: "TaskClient",
                     authorization_header_name: str = "Authorization",
                     authorization_header_prefix: str = "Bearer ",
                     authorization_header_delimiter: str = ":"):
            self.task_client = task_client
            self.authorization_header_name = authorization_header_name
            self.authorization_header_prefix = authorization_header_prefix
            self.authorization_header_delimiter = authorization_header_delimiter

        def __call__(self, r: PreparedRequest):
            if self.authorization_header_name not in r.headers:
                r.headers[self.authorization_header_name] = (f"{self.authorization_header_prefix}"
                                                             f"{self.task_client.id}"
                                                             f"{self.authorization_header_delimiter}"
                                                             f"{self.task_client.api_token}")
            return r

    def __init__(self,
                 id: int,
                 api_token: str,
                 api_url: str | Default = Default(),
                 ssl: bool | Default = Default(),
                 ssl_verify: bool | Default = Default()):
        # task_id
        self._id: int = id

        # task_api_token
        self._api_token: str = api_token

        # api_url
        if type(api_url) is Default:
            api_url = "localhost/kdsm-manager/api"
        # noinspection HttpUrlsUsage
        if api_url.startswith("http://"):
            api_url = api_url[7:]
        if api_url.startswith("https://"):
            api_url = api_url[8:]
        if api_url.endswith("/"):
            api_url = api_url[:-1]
        self._api_url: str = api_url

        # ssl
        if type(ssl) is Default:
            ssl = False
        self.ssl: bool = ssl

        # ssl_verify
        if type(ssl_verify) is Default:
            ssl_verify = True
        self.ssl_verify: bool = ssl_verify

        # requests stuff
        self._bearer_auth = TaskClient.BearerAuth(task_client=self)

        # cache
        self._cache: dict[str, Any] = {}

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id}, name={self.name}, status={self.status})"

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            self.stop(final_state=TaskStatus.SUCCESS)
        else:
            self.stop(final_state=TaskStatus.FAILED)

    def _request(self,
                 method: Literal["GET", "POST", "PUT"],
                 url: str,
                 cache_key: str | None = None,
                 response_model: Any = None,
                 **kwargs) -> Any:
        # lookup in cache
        if cache_key is not None:
            if cache_key in self._cache:
                return self._cache[cache_key]

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
            result = response_model(response.json())
        else:
            result = response.json()

        # save in cache
        if cache_key is not None:
            self._cache[cache_key] = result

        return result

    @property
    def id(self) -> int:
        return self._id

    @property
    def api_token(self) -> str:
        return self._api_token

    @property
    def api_url(self) -> str:
        if not self.ssl:
            # noinspection HttpUrlsUsage
            api_url = "http://" + self._api_url
        else:
            api_url = "https://" + self._api_url
        return api_url

    @property
    def api_task_url(self):
        return self.api_url + "/task"

    @property
    def api_task_name_url(self):
        return self.api_task_url + "/name"

    @property
    def api_task_status_url(self):
        return self.api_task_url + "/status"

    @property
    def api_task_data_url(self):
        return self.api_task_url + "/data"

    @property
    def cache(self) -> dict[str, Any]:
        return self._cache.copy()

    @property
    def name(self) -> str:
        return self._request(method="GET",
                             url=self.api_task_name_url,
                             cache_key="name",
                             response_model=str)

    @property
    def status(self) -> TaskStatus:
        return self._request(method="GET",
                             url=self.api_task_status_url,
                             response_model=TaskStatus)

    @status.setter
    def status(self, value: TaskStatus) -> None:
        self._request(method="PUT",
                      url=self.api_task_status_url,
                      params={"new_status": value.value})

    @property
    def data(self) -> dict:
        return self._request(method="GET",
                             url=self.api_task_data_url,
                             cache_key="data",
                             response_model=dict)

    def clear_cache(self) -> None:
        self._cache = {}

    def clear_cache_key(self, cache_key: str) -> None:
        if cache_key in self._cache:
            del self._cache[cache_key]

    def start(self) -> None:
        # set task state to 'running'
        self.status = TaskStatus.RUNNING

    def stop(self, final_state: TaskStatus):
        # set task status to final_state
        self.status = final_state
