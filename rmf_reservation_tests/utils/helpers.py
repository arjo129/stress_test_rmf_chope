import json
import time
from typing import Any, Callable, Optional

import rclpy


def now_monotonic() -> float:
    return time.monotonic()


def safe_getattr(obj: Any, name: str, default: Any = None) -> Any:
    return getattr(obj, name, default)


def get_location_name(robot_state: Any) -> Optional[str]:
    location = safe_getattr(robot_state, "location", None)
    if location is None:
        return None
    name = safe_getattr(location, "name", None)
    if isinstance(name, str) and name:
        return name
    return None


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


class ConditionWaiter:
    def __init__(self, node: rclpy.node.Node, executor: rclpy.executors.Executor):
        self._node = node
        self._executor = executor

    def wait_for(
        self,
        predicate: Callable[[], bool],
        timeout_sec: float,
        timeout_msg: str,
    ) -> None:
        start = now_monotonic()
        while rclpy.ok():
            self._executor.spin_once(timeout_sec=0.1)
            if predicate():
                return
            if now_monotonic() - start > timeout_sec:
                raise AssertionError(timeout_msg)
        raise AssertionError("ROS shutdown before condition was met")
