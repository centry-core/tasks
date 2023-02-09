from collections import defaultdict
from datetime import datetime

from flask import request, make_response
from flask_restful import Resource
from tools import api_tools

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
            data["ts"] = api_tools.format_date(datetime.fromtimestamp(row.ts))
            rows[task.task_name].append(data)
        return make_response({"total": len(task_result), "rows": rows}, 200)

    def post(self, project_id: int):
        data = request.json
        task_result = create_task_result(project_id, data)
        resp = {"message": "Accepted", "code": 200, "task_id": task_result.id}
        return make_response(resp, resp.get('code', 200))
