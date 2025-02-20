from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings
from wiederverwendbar.logger import LoggerSettings


class Settings(BaseSettings, LoggerSettings):
    model_config = {
        "env_prefix": "KDSM_MANAGER_TASK_CLIENT_",
        "case_sensitive": False
    }

    # general
    id: int | None = Field(default=None, title="Task Id.", description="Id of task in kdsm-manager.")
    api_token: str | None = Field(default=None, title="Task Token.", description="Token of task in kdsm-manager.")
    api_url: str = Field(default="localhost/kdsm-manager/api", title="Task Url.", description="Url of task in kdsm-manager.")
    ssl: bool = Field(default=False, title="Use SSL.", description="Use SSL for communication with kdsm-manager.")
    ssl_verify: bool = Field(default=True, title="Verify SSL.", description="Verify SSL for communication with kdsm-manager.")

    def __init__(self, **values: Any):
        super().__init__(**values)

        # noinspection HttpUrlsUsage
        if self.api_url.startswith("http://"):
            self.api_url = self.api_url[7:]
        if self.api_url.startswith("https://"):
            self.api_url = self.api_url[8:]
        if self.api_url.endswith("/"):
            self.api_url = self.api_url[:-1]
