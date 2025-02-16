from enum import Enum


class TaskStatus(Enum):
    DEPLOYED = "deployed"
    RUNNING = "running"
    ABORTED = "aborted"
    FAILED = "failed"
    SUCCESS = "success"
