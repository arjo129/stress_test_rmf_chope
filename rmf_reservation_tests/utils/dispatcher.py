import uuid
from typing import List, Optional

import rclpy
from rclpy.task import Future

from rmf_task_msgs.srv import DispatchTask

from .helpers import ConditionWaiter, json_dumps


class TaskDispatcher:
    def __init__(self, node: rclpy.node.Node, executor: rclpy.executors.Executor):
        self._node = node
        self._executor = executor
        self._waiter = ConditionWaiter(node, executor)
        self._client = node.create_client(DispatchTask, self._service_name())

    def _service_name(self) -> str:
        return self._node.declare_parameter(
            "dispatch_service", "/dispatch_task"
        ).get_parameter_value().string_value

    def _wait_for_service(self) -> None:
        self._waiter.wait_for(
            lambda: self._client.service_is_ready(),
            timeout_sec=10.0,
            timeout_msg="Dispatch service not available",
        )

    def dispatch_go_to_place(
        self,
        fleet_name: str,
        robot_name: str,
        places: List[str],
        task_id: Optional[str] = None,
        requester: str = "rmf_reservation_tests",
    ) -> str:
        self._wait_for_service()
        request = DispatchTask.Request()
        task_id = task_id or str(uuid.uuid4())
        payload = {
            "type": "go_to_place",
            "fleet": fleet_name,
            "robot": robot_name,
            "places": places,
        }

        self._set_if_exists(request, "task_id", task_id)
        self._set_if_exists(request, "requester", requester)
        self._set_if_exists(request, "fleet_name", fleet_name)
        self._set_if_exists(request, "task_type", "go_to_place")
        self._set_if_exists(request, "payload", json_dumps(payload))
        self._set_if_exists(request, "task_profile", json_dumps(payload))
        self._set_if_exists(request, "description", json_dumps(payload))
        self._set_time_fields(request)

        future = self._client.call_async(request)
        self._wait_for_future(future, 10.0, "Dispatch call timed out")
        response = future.result()
        if response is None:
            raise AssertionError("Dispatch service returned no response")

        response_task_id = self._extract_task_id(response)
        return response_task_id or task_id

    def _wait_for_future(self, future: Future, timeout: float, msg: str) -> None:
        self._waiter.wait_for(lambda: future.done(), timeout, msg)

    def _set_if_exists(self, request: DispatchTask.Request, field: str, value) -> None:
        if hasattr(request, field):
            setattr(request, field, value)

    def _set_time_fields(self, request: DispatchTask.Request) -> None:
        now = self._node.get_clock().now()
        time_msg = now.to_msg()
        if hasattr(request, "start_time"):
            request.start_time = time_msg
        if hasattr(request, "unix_millis_time"):
            request.unix_millis_time = now.nanoseconds // 1_000_000

    def _extract_task_id(self, response: DispatchTask.Response) -> Optional[str]:
        for field in ("task_id", "task_id_state", "assignment_id"):
            if hasattr(response, field):
                value = getattr(response, field)
                if isinstance(value, str) and value:
                    return value
        return None
