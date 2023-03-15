const ApiFetchTasks = async () => {
    const res = await fetch(`/api/v1/tasks/tasks/${getSelectedProjectId()}`, {
        method: 'GET',
    })
    return res.json();
}
const ApiDeleteTask = async (taskId) => {
    const res = await fetch(`/api/v1/tasks/tasks/${getSelectedProjectId()}/${taskId}`, {
        method: 'DELETE',
    })
}
const ApiCheckStatus = async (taskId) => {
    const res = await fetch (`/api/v1/tasks/task_status/${getSelectedProjectId()}/${taskId}`,{
        method: 'GET',
    })
    return res.json();
}
const ApiWebsocketURLByResultId = async (taskId, resultId) => {
    const res = await fetch (`/api/v1/tasks/loki_url/${getSelectedProjectId()}/?task_id=${taskId}&task_result_id=${resultId}`,{
        method: 'GET',
    })
    return res.json();
}
const ApiLastResultId = async (taskId) => {
    const res = await fetch (`/api/v1/tasks/loki_url/${getSelectedProjectId()}/?task_id=${taskId}`,{
        method: 'GET',
    })
    return res.json();
}
const ApiTasksResult = async (taskId) => {
    const res = await fetch (`/api/v1/tasks/results/${getSelectedProjectId()}/${taskId}`,{
        method: 'GET',
    })
    return res.json();
}