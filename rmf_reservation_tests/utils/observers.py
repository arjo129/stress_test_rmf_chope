from dataclasses import dataclass
from typing import Dict, List, Optional, Set

import rclpy
from rclpy.qos import QoSProfile

from rmf_fleet_msgs.msg import FleetState
from rmf_task_msgs.msg import TaskSummary

from .helpers import get_location_name, safe_getattr


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


class ReservationObserver:
    def __init__(self, fleet_observer: FleetStateObserver):
        self._fleet_observer = fleet_observer
        self._history: Dict[str, List[Set[str]]] = {}

    def snapshot(self, place: str, robots: List[str]) -> Set[str]:
        occupants = set()
        for robot in robots:
            if self._fleet_observer.robot_location(robot) == place:
                occupants.add(robot)
        self._history.setdefault(place, []).append(occupants)
        return occupants

    def history(self, place: str) -> List[Set[str]]:
        return self._history.get(place, [])
