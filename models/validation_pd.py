from typing import BinaryIO
from ..models.tasks import Task

from pydantic import BaseModel, validator
from pylon.core.tools import log


class TaskCreateModelPD(BaseModel):
    task_name: str
    task_package: str
    runtime: str
    task_handler: str
    task_package: [str, BinaryIO]
    engine_location: str
    cpu_cores: int
    memory: int
    timeout: int

    @validator('task_name')
    def validate_task_exists(cls, value: str, values: dict):
        assert not Task.query.filter_by(task_name=value).first(), f'Task with name {value} already exists'
        return value

    @validator('task_package')
    def validate_task_package(cls, value: str, values: dict):
        assert not Task.query.filter_by(zippath=f'tasks/{value}').first(), f'Task package {value} already exists'
        return value
