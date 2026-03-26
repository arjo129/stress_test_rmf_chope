import pytest
import rclpy
from rclpy.executors import MultiThreadedExecutor

from .utils.dispatcher import TaskDispatcher
from .utils.observers import FleetStateObserver, ReservationObserver, TaskSummaryObserver
from .utils.helpers import ConditionWaiter


@pytest.fixture(scope="session", autouse=True)
def ros_context():
    rclpy.init()
    yield
    rclpy.shutdown()


@pytest.fixture()
def ros_node():
    node = rclpy.create_node("rmf_reservation_tests")
    try:
        yield node
    finally:
        node.destroy_node()


@pytest.fixture()
def executor(ros_node):
    executor = MultiThreadedExecutor()
    executor.add_node(ros_node)
    try:
        yield executor
    finally:
        executor.remove_node(ros_node)


@pytest.fixture()
def waiter(ros_node, executor):
    return ConditionWaiter(ros_node, executor)


@pytest.fixture()
def dispatcher(ros_node, executor):
    return TaskDispatcher(ros_node, executor)


@pytest.fixture()
def fleet_observer(ros_node):
    return FleetStateObserver(ros_node)


@pytest.fixture()
def task_observer(ros_node):
    return TaskSummaryObserver(ros_node)


@pytest.fixture()
def reservation_observer(fleet_observer):
    return ReservationObserver(fleet_observer)
