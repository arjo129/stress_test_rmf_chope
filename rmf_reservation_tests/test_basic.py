import rclpy

from rmf_reservation_tests.utils.assertions import (
    assert_only_one_robot_in_place,
    assert_place_known,
    assert_task_completed,
)
from rmf_reservation_tests.utils.helpers import now_monotonic


FLEET_NAME = "tinyRobot"
ROBOT_1 = "tinyRobot1"
ROBOT_2 = "tinyRobot2"
CHARGER_1 = "tinyRobot1_charger"
CHARGER_2 = "tinyRobot2_charger"
PANTRY = "pantry"
LOUNGE = "lounge"


def _wait_for_robot_at(waiter, fleet_observer, robot_name, place, timeout):
    waiter.wait_for(
        lambda: fleet_observer.robot_location(robot_name) == place,
        timeout_sec=timeout,
        timeout_msg=f"{robot_name} did not reach {place}",
    )


def _wait_for_task_complete(waiter, task_observer, task_id, timeout):
    waiter.wait_for(
        lambda: task_observer.is_completed(task_id),
        timeout_sec=timeout,
        timeout_msg=f"Task {task_id} did not complete",
    )


def _wait_for_task_assignment(
    waiter,
    fleet_observer,
    task_observer,
    robot_name,
    task_id,
    timeout,
):
    waiter.wait_for(
        lambda: fleet_observer.robot_task_id(robot_name) == task_id
        and task_observer.summary(task_id) is not None,
        timeout_sec=timeout,
        timeout_msg=f"{robot_name} did not acquire task {task_id} in time",
    )


def _wait_for_task_complete_with_snapshots(
    executor,
    task_observer,
    reservation_observer,
    fleet_observer,
    place,
    robots,
    blocking_robot,
    task_id,
    timeout,
):
    start = now_monotonic()
    while rclpy.ok():
        executor.spin_once(timeout_sec=0.1)
        reservation_observer.snapshot(place, robots)
        if (
            blocking_robot
            and fleet_observer.robot_location(blocking_robot) == place
            and not task_observer.is_completed(task_id)
        ):
            raise AssertionError(
                f"{blocking_robot} entered {place} before task {task_id} completed"
            )
        if task_observer.is_completed(task_id):
            return
        if now_monotonic() - start > timeout:
            raise AssertionError(f"Task {task_id} did not complete")
    raise AssertionError("ROS shutdown before task completion")


def test_basic_reservation_flow(
    dispatcher,
    executor,
    waiter,
    fleet_observer,
    task_observer,
    reservation_observer,
):
    waiter.wait_for(
        lambda: fleet_observer.robot_location(ROBOT_1) is not None
        and fleet_observer.robot_location(ROBOT_2) is not None,
        timeout_sec=20.0,
        timeout_msg="Fleet state did not publish robot locations",
    )
    assert_place_known(fleet_observer, [ROBOT_1, ROBOT_2])

    start_time = now_monotonic()

    task_r1_init = dispatcher.dispatch_go_to_place(
        FLEET_NAME, ROBOT_1, [CHARGER_1]
    )
    task_r2_init = dispatcher.dispatch_go_to_place(
        FLEET_NAME, ROBOT_2, [CHARGER_2]
    )

    _wait_for_task_complete(waiter, task_observer, task_r1_init, 120.0)
    _wait_for_task_complete(waiter, task_observer, task_r2_init, 120.0)

    _wait_for_robot_at(waiter, fleet_observer, ROBOT_1, CHARGER_1, 30.0)
    _wait_for_robot_at(waiter, fleet_observer, ROBOT_2, CHARGER_2, 30.0)

    # Sequential contention for pantry.
    dispatch_t2 = now_monotonic()
    task_r2_pantry = dispatcher.dispatch_go_to_place(
        FLEET_NAME, ROBOT_2, [PANTRY]
    )

    _wait_for_task_assignment(
        waiter,
        fleet_observer,
        task_observer,
        ROBOT_2,
        task_r2_pantry,
        30.0,
    )
    pantry_assigned_at = now_monotonic()

    dispatch_t1 = now_monotonic()
    task_r1_pantry = dispatcher.dispatch_go_to_place(
        FLEET_NAME, ROBOT_1, [PANTRY]
    )

    # Ensure only one robot occupies pantry at any time.
    _wait_for_task_complete_with_snapshots(
        executor,
        task_observer,
        reservation_observer,
        fleet_observer,
        PANTRY,
        [ROBOT_1, ROBOT_2],
        ROBOT_1,
        task_r2_pantry,
        180.0,
    )

    task_r2_lounge = dispatcher.dispatch_go_to_place(
        FLEET_NAME, ROBOT_2, [LOUNGE]
    )
    _wait_for_task_complete(waiter, task_observer, task_r2_lounge, 120.0)

    _wait_for_task_complete(waiter, task_observer, task_r1_pantry, 180.0)
    r1_pantry_completed_at = now_monotonic()

    assert_task_completed(task_observer, task_r2_lounge)
    assert_task_completed(task_observer, task_r1_pantry)

    assert_only_one_robot_in_place(reservation_observer, PANTRY, [ROBOT_1, ROBOT_2])

    # Metrics
    completion_time = now_monotonic() - start_time
    pantry_acquire_time = pantry_assigned_at - dispatch_t2
    pantry_wait_time = r1_pantry_completed_at - dispatch_t1

    print(
        "Metrics: total=%.2fs, pantry_wait=%.2fs, pantry_acquire=%.2fs"
        % (completion_time, pantry_wait_time, pantry_acquire_time)
    )
