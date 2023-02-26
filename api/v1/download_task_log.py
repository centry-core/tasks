from io import BytesIO

from flask import send_file, abort

from flask_restful import Resource

from tools import MinioClient



class API(Resource):
    url_params = [
        '<int:project_id>/<string:task_name>/<string:task_result_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int, task_name: str, task_result_id: str):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        minio_client = MinioClient(project)
        bucket_name = str(task_name).replace("_", "").replace(" ", "").lower()
        try:
            file = minio_client.download_file(bucket_name,  f'{task_result_id}.log')
            logging.info(f'file  -{file}')
            try:
                return send_file(BytesIO(file), attachment_filename=file)
            except TypeError:  # new flask
                return send_file(BytesIO(file), download_name=f'{task_result_id}.log', as_attachment=True)
        except:
            abort(404)
