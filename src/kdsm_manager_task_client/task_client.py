from kdsm_manager_task_client.default import Default
from kdsm_manager_task_client.task_status import TaskStatus


class TaskClient:
    def __init__(self,
                 api_token: str,
                 api_url: str | Default = Default(),
                 ssl: bool | Default = Default(),
                 ssl_verify: bool | Default = Default()):
        # api_token
        self._api_token: str = api_token

        # api_url
        if type(api_url) is Default:
            api_url = "localhost/kdsm-manager/api"
        self._api_url: str = api_url

        # ssl
        if type(ssl) is Default:
            ssl = False
        self.ssl: bool = ssl

        # ssl_verify
        if type(ssl_verify) is Default:
            ssl_verify = True
        self.ssl_verify: bool = ssl_verify

        # internal attrs
        self._connected: bool = False
        self._name: str | None = None
        self._status: TaskStatus | None = None

    def __str__(self):
        return f"{self.__class__.__name__}(api_url={self.api_url}, ssl={self.ssl}, ssl_verify={self.ssl_verify})"

    @property
    def api_token(self) -> str:
        return self._api_token

    @api_token.setter
    def api_token(self, value: str):
        self._api_token = value

    @property
    def api_url(self) -> str:
        if not self.ssl:
            # noinspection HttpUrlsUsage
            api_url = "http://" + self._api_url
        else:
            api_url = "https://" + self._api_url
        return api_url

    @api_url.setter
    def api_url(self, value: str):
        # noinspection HttpUrlsUsage
        if value.startswith("http://"):
            value = value[7:]
        if value.startswith("https://"):
            value = value[8:]
        if value.endswith("/"):
            value = value[:-1]
        self._api_url = value

    @property
    def api_task_url(self):
        return self.api_url + "/task"

    @property
    def api_task_websocket_url(self):
        if not self.ssl:
            api_task_websocket_url = "ws://" + self.api_task_url[7:] + "/ws"
        else:
            api_task_websocket_url = "wss://" + self.api_task_url[8:] + "/ws"
        return api_task_websocket_url

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def name(self) -> str:
        if self._name is None:
            raise AttributeError("Name is only available after client is connected!")
        return self._name

    @property
    def status(self) -> TaskStatus:
        if self._status is None:
            raise AttributeError("Status is only available after client is connected!")
        return self._status

    def connect(self):
        if self.connected:
            raise RuntimeError("Client is already connected!")

    def disconnect(self):
        if not self.connected:
            raise RuntimeError("Client is already disconnected!")
