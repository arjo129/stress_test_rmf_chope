# RMF Reservation Tests

This test suite replaces the ad-hoc bash scenario with a deterministic, headless, CI-friendly Python test for RMF reservation behavior.

## What It Covers

- Deterministic task dispatch via ROS 2 services
- Observability of fleet and task states via subscriptions
- Reservation assertions (single occupancy, release, no starvation)
- Metrics reporting for CI visibility

## Structure

- test_basic.py: Scenario orchestration
- utils/dispatcher.py: Task dispatch wrapper
- utils/observers.py: Fleet/task observers
- utils/assertions.py: Assertions and invariants
- utils/helpers.py: Wait utilities

## Running With colcon

From a ROS 2 workspace:

```
colcon test --packages-select stress_test_rmf_chope
```

## Notes

- This test expects RMF core nodes and fleet adapters to be running headless.
- Set the dispatch service name via the node parameter `dispatch_service` if different from `/dispatch_task`.
- Topics used: `/fleet_states`, `/task_summaries`.
