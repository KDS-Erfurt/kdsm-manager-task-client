from enum import Enum


class TaskStatus(Enum):
    DEPLOYED = "deployed"
    RUNNING = "running"
    FAILED = "failed"
    SUCCESS = "success"
