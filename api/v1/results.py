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
        task_result.commit()

        resp = {"message": "Accepted", "code": 202, "task_result_id": task_result.task_result_id}
        return make_response(resp, resp.get('code', 202))
