from rmf_reservation_tests.utils.assertions import (
    assert_no_starvation,
    assert_only_one_robot_in_place,
    assert_place_known,
    assert_place_released_before_next_entry,
    assert_reservation_order,
    assert_task_completed,
)
from rmf_reservation_tests.utils.helpers import debug_dump, now_monotonic


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
    waiter,
    task_observer,
    reservation_observer,
    place,
    robots,
    task_id,
    timeout,
):
    class _SnapshotPredicate:
        def __init__(self, observer, tracker, target_place, target_robots, target_id):
            self._observer = observer
            self._tracker = tracker
            self._place = target_place
            self._robots = target_robots
            self._task_id = target_id

        def on_spin(self) -> None:
            self._observer.snapshot(self._place, self._robots)

        def __call__(self) -> bool:
            return self._tracker.is_completed(self._task_id)

    predicate = _SnapshotPredicate(
        reservation_observer, task_observer, place, robots, task_id
    )
    waiter.spin_until(predicate, timeout, f"Task {task_id} did not complete")


def test_basic_reservation_flow(
    dispatcher,
    waiter,
    fleet_observer,
    task_observer,
    reservation_observer,
):
    try:
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
            waiter,
            task_observer,
            reservation_observer,
            PANTRY,
            [ROBOT_1, ROBOT_2],
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
        assert_reservation_order(reservation_observer, PANTRY, ROBOT_2, ROBOT_1)
        assert_place_released_before_next_entry(reservation_observer, PANTRY)

        # Metrics
        completion_time = now_monotonic() - start_time
        pantry_acquire_time = pantry_assigned_at - dispatch_t2
        pantry_wait_time = r1_pantry_completed_at - dispatch_t1

        assert_no_starvation(
            pantry_wait_time,
            90.0,
            context="pantry_wait_time",
        )
        assert_no_starvation(
            pantry_acquire_time,
            30.0,
            context="pantry_acquire_time",
        )
        _ = completion_time
    except AssertionError:
        debug_dump(
            "test_basic_reservation_flow failure",
            fleet_observer,
            task_observer,
            reservation_observer,
        )
        raise