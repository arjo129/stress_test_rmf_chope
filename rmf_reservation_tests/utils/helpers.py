import json
import time
from typing import Any, Callable, Optional, TYPE_CHECKING

import rclpy

if TYPE_CHECKING:
    from .observers import FleetStateObserver, TaskSummaryObserver


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
        self.spin_until(predicate, timeout_sec, timeout_msg)

    def spin_until(
        self,
        predicate: Callable[[], bool],
        timeout_sec: float,
        timeout_msg: str,
    ) -> None:
        start = now_monotonic()
        while rclpy.ok():
            self._executor.spin_once(timeout_sec=0.1)
            hook = getattr(predicate, "on_spin", None)
            if callable(hook):
                hook()
            if predicate():
                return
            if now_monotonic() - start > timeout_sec:
                raise AssertionError(timeout_msg)
        raise AssertionError("ROS shutdown before condition was met")


def wait_for_task_assignment(
    waiter: "ConditionWaiter",
    fleet_observer: "FleetStateObserver",
    task_observer: "TaskSummaryObserver",
    robot_name: str,
    task_id: str,
    timeout_sec: float,
) -> None:
    waiter.spin_until(
        lambda: task_observer.summary(task_id) is not None,
        timeout_sec,
        f"Task summary not observed for {task_id}",
    )
    waiter.spin_until(
        lambda: fleet_observer.robot_task_id(robot_name) == task_id,
        timeout_sec,
        f"{robot_name} did not acquire task {task_id} in time",
    )


def debug_dump(
    label: str,
    fleet_observer: Any,
    task_observer: Any,
    tracker: Any,
) -> None:
    print(f"[debug_dump] {label}")

    robots = getattr(fleet_observer, "_robots", {})
    if robots:
        for name, snapshot in robots.items():
            location = safe_getattr(snapshot, "location", None)
            task_id = safe_getattr(snapshot, "task_id", None)
            mode = safe_getattr(snapshot, "mode", None)
            print(
                f"[debug_dump] robot name={name} location={location} "
                f"task_id={task_id} mode={mode}"
            )
    else:
        for name in getattr(fleet_observer, "robot_names", lambda: [])():
            location = safe_getattr(fleet_observer, "robot_location", lambda _: None)(
                name
            )
            task_id = safe_getattr(fleet_observer, "robot_task_id", lambda _: None)(
                name
            )
            print(
                f"[debug_dump] robot name={name} location={location} "
                f"task_id={task_id} mode=None"
            )

    summaries = getattr(task_observer, "_summaries", {})
    if summaries:
        for task_id, summary in summaries.items():
            state = safe_getattr(summary, "state", None)
            status = safe_getattr(summary, "status", None)
            print(
                f"[debug_dump] task id={task_id} state={state} status={status}"
            )

    places = set()
    for source in ("_events", "_waiting", "_current_owner"):
        places.update(getattr(tracker, source, {}).keys())
    for place in sorted(places):
        owner = safe_getattr(tracker, "current_owner", lambda _: None)(place)
        waiting = safe_getattr(tracker, "waiting_queue", lambda _: [])(place)
        events = safe_getattr(tracker, "all_events", lambda _: [])(place)
        print(
            f"[debug_dump] place={place} owner={owner} waiting={waiting} "
            f"events={[f'{e.timestamp:.3f}:{e.event_type}:{e.robot}' for e in events]}"
        )
