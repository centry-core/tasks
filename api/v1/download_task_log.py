from io import BytesIO
from flask import send_file, abort
from tools import MinioClient, api_tools, MinioClientAdmin, auth

class ProjectApi(api_tools.APIModeHandler):
    @auth.decorators.check_api(["configuration.tasks.tasks.create"])
    def get(self, project_id: int, task_name: str, task_result_id: str):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        minio_client = MinioClient(project)
        bucket_name = str(task_name).replace("_", "").replace(" ", "").lower()
        try:
            file = minio_client.download_file(bucket_name, f'{task_result_id}.log')
            try:
                return send_file(BytesIO(file), attachment_filename=file)
            except TypeError:  # new flask
                return send_file(BytesIO(file), download_name=f'{task_result_id}.log', as_attachment=True)
        except:
            abort(404)


class AdminApi(api_tools.APIModeHandler):
    @auth.decorators.check_api(["configuration.tasks.tasks.create"])
    def get(self, project_id: int, task_name: str, task_result_id: str):
        minio_client = MinioClientAdmin()
        bucket_name = str(task_name).replace("_", "").replace(" ", "").lower()
        try:
            file = minio_client.download_file(bucket_name, f'{task_result_id}.log')
            try:
                return send_file(BytesIO(file), attachment_filename=file)
            except TypeError:  # new flask
                return send_file(BytesIO(file), download_name=f'{task_result_id}.log', as_attachment=True)
        except:
            abort(404)


class API(api_tools.APIBase):
    url_params = [
        '<string:project_id>/<string:task_name>/<string:task_result_id>',
        '<string:mode>/<string:project_id>/<string:task_name>/<string:task_result_id>',
    ]
    mode_handlers = {
        'default': ProjectApi,
        'administration': AdminApi,
    }
