from typing import Optional, Union

from pydantic import BaseModel, validator
import json


class TaskCreateModel(BaseModel):
    mode: str = 'default'
    project_id: Optional[int]
    task_id: str
    zippath: dict
    task_name: str
    task_handler: str
    runtime: str
    region: str
    webhook: str = ''
    env_vars: str = '{}'

    class Config:
        fields = {'task_handler': 'invoke_func', 'task_name': 'funcname'}

    @validator('env_vars')
    def env_vars_valid_json(cls, value: Union[dict, str]):
        if isinstance(value, str):
            try:
                json.loads(value)
            except:
                assert False, 'env_vars is not a valid json string'
            return value
        else:
            return json.dumps(value)

    @validator('project_id')
    def assure_project_id_in_project_mode(cls, value: Optional[int], values: dict):
        if value:
            assert values['mode'] == 'default', 'project_id is available only in project mode'
        else:
            assert values['mode'] != 'default', 'project_id is required for project mode'
        return value
