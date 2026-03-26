from dataclasses import dataclass
import threading
import time
from typing import Dict, List, Optional, Set

import rclpy
from rclpy.qos import QoSProfile

from rmf_fleet_msgs.msg import FleetState
from rmf_task_msgs.msg import TaskSummary

from .helpers import get_location_name, safe_getattr

try:
    from rmf_reservation_msgs.msg import Claim, Release, ReservationRequest, Ticket
except ImportError as exc:
    raise ImportError(
        "rmf_reservation_msgs not found — install the rmf_reservation package"
    ) from exc


@dataclass
class RobotSnapshot:
    name: str
    location: Optional[str]
    task_id: Optional[str]
    mode: Optional[str]


class FleetStateObserver:
    def __init__(self, node: rclpy.node.Node, topic: str = "/fleet_states"):
        self._node = node
        self._robots: Dict[str, RobotSnapshot] = {}
        self._qos = QoSProfile(depth=10)
        topic = node.declare_parameter(
            "fleet_states_topic", topic
        ).get_parameter_value().string_value
        self._subscription = node.create_subscription(
            FleetState, topic, self._callback, self._qos
        )

    def _callback(self, msg: FleetState) -> None:
        for robot in msg.robots:
            name = safe_getattr(robot, "name", "")
            if not name:
                continue
            location = get_location_name(robot)
            task_id = safe_getattr(robot, "task_id", None)
            mode = None
            mode_msg = safe_getattr(robot, "mode", None)
            if mode_msg is not None:
                mode = safe_getattr(mode_msg, "mode", None)
            self._robots[name] = RobotSnapshot(name, location, task_id, mode)

    def robot_location(self, robot_name: str) -> Optional[str]:
        snapshot = self._robots.get(robot_name)
        return snapshot.location if snapshot else None

    def robot_task_id(self, robot_name: str) -> Optional[str]:
        snapshot = self._robots.get(robot_name)
        return snapshot.task_id if snapshot else None

    def robot_names(self) -> List[str]:
        return list(self._robots.keys())


class TaskSummaryObserver:
    def __init__(self, node: rclpy.node.Node, topic: str = "/task_summaries"):
        self._node = node
        self._summaries: Dict[str, TaskSummary] = {}
        self._qos = QoSProfile(depth=20)
        topic = node.declare_parameter(
            "task_summaries_topic", topic
        ).get_parameter_value().string_value
        self._subscription = node.create_subscription(
            TaskSummary, topic, self._callback, self._qos
        )

    def _callback(self, msg: TaskSummary) -> None:
        task_id = safe_getattr(msg, "task_id", None)
        if task_id:
            self._summaries[task_id] = msg

    def summary(self, task_id: str) -> Optional[TaskSummary]:
        return self._summaries.get(task_id)

    def state(self, task_id: str) -> Optional[int]:
        summary = self.summary(task_id)
        if summary is None:
            return None
        return safe_getattr(summary, "state", None)

    def status(self, task_id: str) -> Optional[str]:
        summary = self.summary(task_id)
        if summary is None:
            return None
        return safe_getattr(summary, "status", None)

    def is_completed(self, task_id: str) -> bool:
        summary = self.summary(task_id)
        if summary is None:
            return False
        if hasattr(summary, "STATE_COMPLETED"):
            return summary.state == summary.STATE_COMPLETED
        if isinstance(summary.status, str):
            return summary.status.lower() in {"completed", "success"}
        return False


@dataclass(frozen=True)
class ReservationEvent:
    timestamp: float
    event_type: str
    robot: str
    place: str


class ReservationStateTracker:
    def __init__(self, node: rclpy.node.Node):
        self._node = node
        self._lock = threading.RLock()
        self._waiting: Dict[str, List[str]] = {}
        self._current_owner: Dict[str, Optional[str]] = {}
        self._events: Dict[str, List[ReservationEvent]] = {}
        self._qos = QoSProfile(depth=20)

        self._request_sub = node.create_subscription(
            ReservationRequest,
            "/rmf_reservation/request",
            self._on_request,
            self._qos,
        )
        self._ticket_sub = node.create_subscription(
            Ticket,
            "/rmf_reservation/ticket",
            self._on_ticket,
            self._qos,
        )
        self._claim_sub = node.create_subscription(
            Claim,
            "/rmf_reservation/claim",
            self._on_claim,
            self._qos,
        )
        self._release_sub = node.create_subscription(
            Release,
            "/rmf_reservation/release",
            self._on_release,
            self._qos,
        )

    def __repr__(self) -> str:
        with self._lock:
            places = sorted(self._events.keys())
            owners = {place: self._current_owner.get(place) for place in places}
            waiting = {place: list(self._waiting.get(place, [])) for place in places}
        return (
            f"ReservationStateTracker(places={places}, "
            f"owners={owners}, waiting={waiting})"
        )

    def current_owner(self, place: str) -> Optional[str]:
        with self._lock:
            return self._current_owner.get(place)

    def waiting_queue(self, place: str) -> List[str]:
        with self._lock:
            return list(self._waiting.get(place, []))

    def all_events(self, place: str) -> List[ReservationEvent]:
        with self._lock:
            return list(self._events.get(place, []))

    def _on_request(self, msg: ReservationRequest) -> None:
        place = msg.place_name
        robot = msg.robot_name
        self._append_event(place, "request", robot)
        with self._lock:
            waiting = self._waiting.setdefault(place, [])
            if robot not in waiting and self._current_owner.get(place) != robot:
                waiting.append(robot)

    def _on_ticket(self, msg: Ticket) -> None:
        place = msg.place_name
        robot = msg.robot_name
        self._append_event(place, "ticket", robot)

    def _on_claim(self, msg: Claim) -> None:
        place = msg.place_name
        robot = msg.robot_name
        self._append_event(place, "claim", robot)
        with self._lock:
            self._current_owner[place] = robot
            waiting = self._waiting.setdefault(place, [])
            if robot in waiting:
                waiting.remove(robot)

    def _on_release(self, msg: Release) -> None:
        place = msg.place_name
        robot = msg.robot_name
        self._append_event(place, "release", robot)
        with self._lock:
            if self._current_owner.get(place) == robot:
                self._current_owner[place] = None

    def _append_event(self, place: str, event_type: str, robot: str) -> None:
        event = ReservationEvent(
            timestamp=time.monotonic(),
            event_type=event_type,
            robot=robot,
            place=place,
        )
        with self._lock:
            self._events.setdefault(place, []).append(event)
