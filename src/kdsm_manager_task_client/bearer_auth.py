from typing import TYPE_CHECKING

from requests import PreparedRequest
from requests.auth import AuthBase

if TYPE_CHECKING:
    from kdsm_manager_task_client.task import Task


class BearerAuth(AuthBase):
    def __init__(self,
                 task: "Task",
                 authorization_header_name: str = "Authorization",
                 authorization_header_prefix: str = "Bearer ",
                 authorization_header_delimiter: str = ":"):
        self.task = task
        self.authorization_header_name = authorization_header_name
        self.authorization_header_prefix = authorization_header_prefix
        self.authorization_header_delimiter = authorization_header_delimiter

    def __call__(self, request: PreparedRequest):
        if self.authorization_header_name not in request.headers:
            request.headers[self.authorization_header_name] = (f"{self.authorization_header_prefix}"
                                                               f"{self.task.id}"
                                                               f"{self.authorization_header_delimiter}"
                                                               f"{self.task.api_token}")
        return request
