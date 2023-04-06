from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator
from hurry.filesize import size


class ResultsGetModel(BaseModel):
    task_stats: Optional[dict]
    id: int
    mode: str
    project_id: Optional[int]
    results: str
    task_duration: float
    task_id: str
    task_result_id: str
    task_status: str
    ts: Optional[str]
    timestamp: Optional[int]

    @validator('task_stats')
    def format_stats(cls, value: Optional[dict]):
        if not value:
            return value
        usage_delta = (
                value['cpu_stats']['cpu_usage']['total_usage'] -
                value['precpu_stats']['cpu_usage']['total_usage']
        )
        system_delta = (
                value['cpu_stats']['system_cpu_usage'] -
                value['precpu_stats']['system_cpu_usage']
        )
        online_cpus = value["cpu_stats"].get("online_cpus",
                                             len(value["cpu_stats"]["cpu_usage"].get("percpu_usage", [None])))

        memory_usage = size(value["memory_stats"]["usage"]) if value.get('memory_stats') else value["memory_usage"]
        return {
            "cpu_usage": round(usage_delta / system_delta, 2) * online_cpus * 100,
            "memory_usage": memory_usage
        }

    @validator('ts')
    def set_ts(cls, value, values):
        if isinstance(value, str):
            return value
        values['timestamp'] = value
        return datetime.fromtimestamp(value).isoformat()
