from typing import BinaryIO, List
from ..models.tasks import Task

from pydantic import BaseModel, validator


class TaskPutModelPD(BaseModel):
    task_name: str
    task_package: str
    runtime: str
    task_handler: str
    task_parameters: List[dict]

    @validator('task_package')
    def validate_task_package(cls, value: str, values: dict):
        if value:
            assert Task.query.filter_by(zippath=f'tasks/{value}').first(), f'There no such package file in database' \
                                                                           f' {value} to perform an update.'
        return value


class TaskCreateModelPD(BaseModel):
    project_id: int
    task_name: str
    task_package: str
    runtime: str
    task_handler: str
    engine_location: str
    cpu_cores: int
    memory: int
    timeout: int
    task_parameters: List[dict]

    @validator('task_name')
    def validate_task_exists(cls, value: str, values: dict):
        assert not Task.query.filter_by(task_name=value, project_id=values['project_id']).first(), f'Task with name {value} already exists'
        return value

    @validator('task_package')
    def validate_task_package(cls, value: str, values: dict):
        assert not Task.query.filter_by(zippath=f'tasks/{value}').first(), f'Task package {value} already exists'
        return value

    @validator('task_parameters')
    def validate_task_parameter_unique_name(cls, value: list):
        import collections
        # duplicates = [item for item, count in collections.Counter(i.name for i in value).items() if count > 1]
        # assert not duplicates, f'Duplicated names not allowed: {duplicates}'
        return value
