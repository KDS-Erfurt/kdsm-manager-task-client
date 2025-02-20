from enum import Enum


class TaskStatus(str, Enum):
    DEPLOYED = "deployed"
    RUNNING = "running"
    ABORTED = "aborted"
    FAILED = "failed"
    SUCCESS = "success"
