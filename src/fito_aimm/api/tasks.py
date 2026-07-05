from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from uuid import uuid4


class AnalysisTaskManager:
    def __init__(self, max_workers: int = 2):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks: dict[str, Future] = {}

    def submit(self, fn, *args, **kwargs) -> str:
        task_id = f"task_{uuid4().hex[:10]}"
        self.tasks[task_id] = self.executor.submit(fn, *args, **kwargs)
        return task_id

    def status(self, task_id: str) -> dict[str, object]:
        future = self.tasks[task_id]
        if future.running():
            return {"task_id": task_id, "status": "running"}
        if not future.done():
            return {"task_id": task_id, "status": "pending"}
        return {"task_id": task_id, "status": "completed", "result": future.result()}

    def wait(self, task_id: str):
        return self.tasks[task_id].result()
