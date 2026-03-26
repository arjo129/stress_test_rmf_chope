from typing import Iterable, List, Optional, Set

from .helpers import safe_getattr
from .observers import (
    FleetStateObserver,
    ReservationObserver,
    ReservationStateTracker,
    TaskSummaryObserver,
)


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
        # Only consider robots under test, ignore unrelated robots in the system
        relevant_occupants = [robot for robot in occupants if robot in robots]
        if len(relevant_occupants) > 1:
            raise AssertionError(
                f"Multiple robots in {place}: {sorted(relevant_occupants)}"
            )


def assert_task_completed(task_observer: TaskSummaryObserver, task_id: str) -> None:
    if not task_observer.is_completed(task_id):
        state = task_observer.state(task_id)
        status = task_observer.status(task_id)
        raise AssertionError(
            f"Task {task_id} did not complete. state={state} status={status}"
        )


def assert_no_starvation(
    wait_time_sec: float,
    max_wait_sec: float,
    context: str = "",
) -> None:
    if wait_time_sec > max_wait_sec:
        prefix = f"{context}: " if context else ""
        raise AssertionError(
            f"{prefix}Waiting time exceeded limit: {wait_time_sec:.2f}s > {max_wait_sec:.2f}s"
        )


def _event_history(tracker: ReservationStateTracker, place: str) -> str:
    events = tracker.all_events(place)
    if not events:
        return "[no events]"
    return " | ".join(
        f"{event.timestamp:.3f}:{event.event_type}:{event.robot}"
        for event in events
    )


def assert_reservation_order(
    tracker: ReservationStateTracker,
    place: str,
    first_robot: str,
    second_robot: str,
) -> None:
    events = tracker.all_events(place)
    first_claim = None
    second_claim = None
    for idx, event in enumerate(events):
        if event.event_type == "claim" and event.robot == first_robot:
            first_claim = idx
            break
    for idx, event in enumerate(events):
        if event.event_type == "claim" and event.robot == second_robot:
            second_claim = idx
            break
    if first_claim is None or second_claim is None:
        raise AssertionError(
            "Missing claim event for one or both robots. "
            f"place={place} first={first_robot} second={second_robot} "
            f"history={_event_history(tracker, place)}"
        )
    if first_claim >= second_claim:
        raise AssertionError(
            "Claim order violated. "
            f"place={place} first={first_robot} second={second_robot} "
            f"history={_event_history(tracker, place)}"
        )


def assert_place_released_before_next_entry(
    tracker: ReservationStateTracker,
    place: str,
) -> None:
    events = tracker.all_events(place)
    for idx, event in enumerate(events):
        if event.event_type != "claim":
            continue
        claim_robot = event.robot
        release_found = False
        for next_event in events[idx + 1 :]:
            if next_event.event_type == "claim":
                break
            if next_event.event_type == "release" and next_event.robot == claim_robot:
                release_found = True
                break
        if not release_found:
            raise AssertionError(
                "Missing release before next claim. "
                f"place={place} robot={claim_robot} "
                f"history={_event_history(tracker, place)}"
            )


def assert_robot_waited(
    tracker: ReservationStateTracker,
    robot: str,
    place: str,
) -> None:
    events = tracker.all_events(place)
    claim_index = None
    request_index = None
    for idx, event in enumerate(events):
        if event.event_type == "claim" and event.robot == robot:
            claim_index = idx
            break
    if claim_index is None:
        raise AssertionError(
            "No claim event for robot. "
            f"place={place} robot={robot} "
            f"history={_event_history(tracker, place)}"
        )
    for idx, event in enumerate(events[:claim_index]):
        if event.event_type == "request" and event.robot == robot:
            request_index = idx
            break
    if request_index is None:
        raise AssertionError(
            "Robot did not wait before claim. "
            f"place={place} robot={robot} "
            f"history={_event_history(tracker, place)}"
        )
