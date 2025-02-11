from typing import List, Optional

from pydantic.v1 import BaseModel, validator, root_validator
from sqlalchemy import Integer, String, Boolean
from pylon.core.tools import log

from ..models.tasks import Task


class S3Integration(BaseModel):
    integration_id: int
    is_local: bool


class TaskPutModelPD(BaseModel):
    mode: str = 'default'
    task_name: str
    s3_settings: S3Integration
    validate_package: bool = True
    task_package: str
    runtime: str
    task_handler: str
    task_parameters: List[dict]
    monitoring_settings: dict = {}

    @validator('task_package')
    def validate_task_package(cls, value: str, values: dict):
        if values['validate_package']:
            mode = values['mode']
            s3_settings = values['s3_settings']
            assert not Task.query.filter(
                Task.mode == mode,
                Task.zippath['integration_id'].astext.cast(Integer) == s3_settings.integration_id,
                Task.zippath['is_local'].astext.cast(Boolean) == s3_settings.is_local,
                Task.zippath['bucket_name'].astext.cast(String) == 'tasks',
                Task.zippath['file_name'].astext.cast(String) == value,
            ).first(), f'Task package {value} already exists'
        return value


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
