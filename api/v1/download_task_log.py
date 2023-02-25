from io import BytesIO

from flask import send_file, abort

from flask_restful import Resource

from tools import MinioClient

from ...models.tasks import Task


class API(Resource):
    url_params = [
        '<int:project_id>/<string:task_result_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int, task_result_id: str):
        task_result_id = f'{task_result_id}.log'
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        minio_client = MinioClient(project)
        task_name = Task.query.filter_by(task_result_id=task_result_id, project_id=project_id).first()
        bucket_name = str(task_name).replace("_", "").replace(" ", "").lower()
        try:
            file = minio_client.download_file(bucket_name=bucket_name, file_name=task_result_id)
            try:
                return send_file(BytesIO(file), attachment_filename=file)
            except TypeError:  # new flask
                return send_file(BytesIO(file), download_name=task_result_id, as_attachment=True)
        except:
            abort(404)
