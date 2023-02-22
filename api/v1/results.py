import logging
from collections import defaultdict
from datetime import datetime

from flask import request, make_response
from flask_restful import Resource
from tools import api_tools
from hurry.filesize import size

from ...models.results import TaskResults
from ...models.tasks import Task
from ...tools.task_tools import create_task_result


class API(Resource):
    url_params = [
        '<int:project_id>',
        '<int:project_id>/<string:task_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int, task_id: str):
        args = request.args
        rows = defaultdict(list)

        task_result = TaskResults.query.filter_by(project_id=project_id, task_id=task_id).all()
        for row in task_result:
            task = Task.query.filter_by(project_id=project_id, task_id=task_id).first()
            data = row.to_json()
            data["ts"] = api_tools.format_date(datetime.fromtimestamp(row.ts)) if row.ts else None
            if task_stats := data.pop("task_stats", None):
                usage_delta = (
                        task_stats['cpu_stats']['cpu_usage']['total_usage'] -
                        task_stats['precpu_stats']['cpu_usage']['total_usage']
                )
                system_delta = (
                        task_stats['cpu_stats']['system_cpu_usage'] -
                        task_stats['precpu_stats']['system_cpu_usage']
                )
                online_cpus = task_stats["cpu_stats"].get("online_cpus", len(task_stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [None])))

                memory_usage = size(task_stats["memory_stats"]["usage"]) if task_stats.get('memory_stats') else task_stats["memory_usage"]
                logging.info(f'updating task_stats {memory_usage}')
                data["task_stats"] = {
                    "cpu_usage": round(usage_delta / system_delta, 2) * online_cpus * 100,
                    "memory_usage": memory_usage
                }
            else:
                data["task_stats"] = task_stats

            rows[task.task_name].append(data)
        return make_response({"total": len(task_result), "rows": rows}, 200)

    def post(self, project_id: int):
        data = request.json
        logging.info(f'task result {data}')
        task_result = create_task_result(project_id, data)
        resp = {"message": "Created", "code": 201, "task_id": task_result.id}
        return make_response(resp, resp.get('code', 201))

    def put(self, project_id: int):
        data = request.json
        args = request.args
        task_result_id = args.get('task_result_id')
        task_result = TaskResults.query.filter_by(project_id=project_id, task_result_id=task_result_id).first()
        if not task_result:
            return {"message": "No such task_result_id in selected in project"}, 404

        task_result.ts = data.get('ts')
        task_result.task_duration = data.get('task_duration')
        task_result.log = data.get('log')
        task_result.results = data.get('results')
        task_result.task_status = data.get('task_status')
        task_result.task_stats = data.get('task_stats')
        task_result.commit()

        resp = {"message": "Accepted", "code": 202, "task_result_id": task_result.task_result_id}
        return make_response(resp, resp.get('code', 202))
