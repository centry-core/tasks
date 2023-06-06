from typing import List, Optional

from pydantic import BaseModel, validator, root_validator
from pylon.core.tools import log

from ..models.tasks import Task


class TaskPutModelPD(BaseModel):
    mode: str = 'default'
    task_name: str
    task_package: str
    runtime: str
    task_handler: str
    task_parameters: List[dict]
    monitoring_settings: dict = {}


class TaskCreateModelPD(TaskPutModelPD):
    project_id: Optional[int] = None
    engine_location: str
    cpu_cores: int
    memory: int
    timeout: int

    @property
    def env_vars(self) -> dict:
        return {
            "cpu_cores": self.cpu_cores,
            "memory": self.memory,
            "timeout": self.timeout,
            "task_parameters": self.task_parameters,
            "monitoring_settings": self.monitoring_settings,
        }

    @validator('project_id', always=True)
    def check_for_project_mode(cls, value: Optional[int], values: dict):
        log.info(f'check_for_project_mode {values=} {value=}')
        if values['mode'] == 'default':
            assert value, 'project_id is required'
        return value

    @validator('task_package')
    def validate_task_package(cls, value: str, values: dict):
        mode = values['mode']
        assert not Task.query.filter(
            Task.zippath == f'tasks/{value}',
            Task.mode == mode,
        ).first(), f'Task package {value} already exists'
        return value

    @root_validator(pre=True)
    def validate_task_exists(cls, values: dict):
        log.info(f'validate_task_exists {values=}')
        mode = values['mode']
        query = Task.query.filter(
            Task.task_name == values['task_name'],
            Task.mode == mode
        )
        if mode == 'default':
            log.info(f'validate_task_exists {values=}')
            project_id = values['project_id']
            query.filter(Task.project_id == project_id)
        assert not query.first(), f'Task with name {values["task_name"]} already exists'
        return values
