from pydantic import BaseModel
from wiederverwendbar.logger import LogLevels


class SubtaskLogModel(BaseModel):
    model_config = {
        "use_enum_values": True,
    }

    class Exception(BaseModel):
        message: str
        code: int
        stack_trace: str

    file_name: str
    log_level: LogLevels
    line_number: int
    logger_name: str
    message: str
    method: str
    module: str
    thread: int
    thread_name: str
    timestamp: float
    exception: Exception | None = None
    extra: dict | None = None
