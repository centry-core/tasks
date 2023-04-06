const ApiFetchTasks = async () => {
    const api_url = V.build_api_url('tasks', 'tasks')
    const res = await fetch(`${api_url}/${getSelectedProjectId()}`, {
        method: 'GET',
    })
    return res.json();
}
const ApiDeleteTask = async (taskId) => {
    const api_url = V.build_api_url('tasks', 'tasks')
    const res = await fetch(`${api_url}/${getSelectedProjectId()}/${taskId}`, {
        method: 'DELETE',
    })
}
const ApiCheckStatus = async (taskId) => {
    const api_url = V.build_api_url('tasks', 'task_status')
    const res = await fetch (`${api_url}/${getSelectedProjectId()}/${taskId}`,{
        method: 'GET',
    })
    return res.json();
}
const ApiWebsocketURLByResultId = async (taskId, resultId) => {
    const api_url = V.build_api_url('tasks', 'loki_url')
    const res = await fetch (`${api_url}/${getSelectedProjectId()}/?task_id=${taskId}&task_result_id=${resultId}`,{
        method: 'GET',
    })
    return res.json();
}
const ApiLastResultId = async (taskId) => {
    const api_url = V.build_api_url('tasks', 'loki_url')
    const res = await fetch (`${api_url}/${getSelectedProjectId()}/?task_id=${taskId}`,{
        method: 'GET',
    })
    return res.json();
}
const ApiTasksResult = async (taskId) => {
    const api_url = V.build_api_url('tasks', 'results')
    const res = await fetch (`${api_url}/${getSelectedProjectId()}/${taskId}`,{
        method: 'GET',
    })
    return res.json();
}