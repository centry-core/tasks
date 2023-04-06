import json
from typing import BinaryIO, List, Optional
from ..models.tasks import Task

from pydantic import BaseModel, validator


class TaskPutModelPD(BaseModel):
    mode: str = 'default'
    task_name: str
    task_package: str
    runtime: str
    task_handler: str
    task_parameters: List[dict]

    # @validator('task_package')
    # def validate_task_package(cls, value: str, values: dict):
    #     if value:
    #         assert Task.query.filter_by(zippath=f'tasks/{value}').first(), f'There no such package file in database' \
    #                                                                        f' {value} to perform an update.'
    #     return value


class TaskCreateModelPD(TaskPutModelPD):
    project_id: Optional[int] = None
    engine_location: str
    cpu_cores: int
    memory: int
    timeout: int

    # class Config:
    #     fields = {
            # 'funcname': 'task_name',
            # 'invoke_func': 'task_handler',
            # 'region': 'engine_location',

            # 'task_name': 'funcname',
            # 'task_handler': 'invoke_func',
            # 'engine_location': 'region',
        # }

    @property
    def _env_vars(self) -> dict:
        return {
            "cpu_cores": self.cpu_cores,
            "memory": self.memory,
            "timeout": self.timeout,
            "task_parameters": self.task_parameters
        }

    @validator('task_name')
    def validate_task_exists(cls, value: str, values: dict):
        mode = values['mode']
        query = Task.query.filter(
            Task.task_name == value,
            Task.mode == mode
        )
        if mode == 'default':
            project_id = values['project_id']
            query.filter(Task.project_id == project_id)
        assert not query.first(), f'Task with name {value} already exists'
        return value

    @validator('task_package')
    def validate_task_package(cls, value: str, values: dict):
        mode = values['mode']
        assert not Task.query.filter(
            Task.zippath == f'tasks/{value}',
            Task.mode == mode,
        ).first(), f'Task package {value} already exists'
        return value

    # @validator('task_parameters')
    # def validate_task_parameter_unique_name(cls, value: list):
    #     import collections
    #     # duplicates = [item for item, count in collections.Counter(i.name for i in value).items() if count > 1]
    #     # assert not duplicates, f'Duplicated names not allowed: {duplicates}'
    #     return value

    @validator('project_id', always=True)
    def check_for_project_mode(cls, value: Optional[int], values: dict):
        if values['mode'] == 'default':
            assert value, 'project_id is required'
        return value


# data = json.loads('{"task_name":"gdfsgdfg","task_package":"rabbit_queue_checker (6).zip","runtime":"Python 3.8","task_handler":"dfgdfg","engine_location":"default","cpu_cores":1,"memory":4,"timeout":500,"task_parameters":[]}')
# data['mode'] = 'administration'
# x = TaskCreateModelPD.parse_obj(data)
# print(x.dict(by_alias=True))