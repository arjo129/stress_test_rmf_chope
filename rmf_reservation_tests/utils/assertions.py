from typing import Iterable, List, Optional, Set

from .helpers import safe_getattr
from .observers import FleetStateObserver, ReservationObserver, TaskSummaryObserver


def assert_place_known(fleet_observer: FleetStateObserver, robot_names: List[str]) -> None:
    unknown = [name for name in robot_names if fleet_observer.robot_location(name) is None]
    if unknown:
        raise AssertionError(
            f"Robot locations missing for: {', '.join(unknown)}. "
            "Ensure fleet state publishes location names."
        )


def assert_only_one_robot_in_place(
    reservation_observer: ReservationObserver,
    place: str,
    robots: List[str],
) -> None:
    history = reservation_observer.history(place)
    for occupants in history:
        if len(occupants) > 1:
            raise AssertionError(
                f"Multiple robots in {place}: {sorted(occupants)}"
            )


def assert_task_completed(task_observer: TaskSummaryObserver, task_id: str) -> None:
    if not task_observer.is_completed(task_id):
        state = task_observer.state(task_id)
        status = task_observer.status(task_id)
        raise AssertionError(
            f"Task {task_id} did not complete. state={state} status={status}"
        )


def assert_no_starvation(wait_time_sec: float, max_wait_sec: float) -> None:
    if wait_time_sec > max_wait_sec:
        raise AssertionError(
            f"Waiting time exceeded limit: {wait_time_sec:.2f}s > {max_wait_sec:.2f}s"
        )
