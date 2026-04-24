#!/bin/bash

# NOTE: Test with finishing request set to [nothing]
# Monitor /robot_collisions for collision events.
# The topic uses rmf_fleet_msgs/msg/RobotCollision messages.
# These messages indicate an emergency stop/collision event in the simulation.
COLLISION_LOG=$(mktemp)
ros2 topic echo /robot_collisions rmf_fleet_msgs/msg/RobotCollision \
    --no-daemon 2>/dev/null > "$COLLISION_LOG" &
COLLISION_MONITOR_PID=$!

cleanup() {
    kill "$COLLISION_MONITOR_PID" 2>/dev/null
    wait "$COLLISION_MONITOR_PID" 2>/dev/null
    if [ -s "$COLLISION_LOG" ]; then
        echo "Test failed: reservation system failure — emergency stop detected"
        cat "$COLLISION_LOG"
        exit 1
    fi
    rm -f "$COLLISION_LOG"
}
trap cleanup EXIT

# Initialize robot positions
ros2 run rmf_demos_tasks dispatch_go_to_place -p tinyRobot1_charger -F tinyRobot -R tinyRobot1 --use_sim_time
ros2 run rmf_demos_tasks dispatch_go_to_place -p tinyRobot2_charger -F tinyRobot -R tinyRobot2 --use_sim_time
ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot1 --timeout 500
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed: tinyRobot1 did not reach charger"
        exit 1
fi
ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot2 --timeout 500
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed: tinyRobot2 did not reach charger"
        exit 1
fi

ros2 run rmf_demos_tasks dispatch_go_to_place -p pantry -F tinyRobot -R tinyRobot2 --use_sim_time
sleep 10
ros2 run rmf_demos_tasks dispatch_go_to_place -p pantry -F tinyRobot -R tinyRobot1 --use_sim_time
ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot2 --timeout 200
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed: tinyRobot2 did not reach pantry"
        exit 1
fi

ros2 run rmf_demos_tasks dispatch_go_to_place -p lounge -F tinyRobot -R tinyRobot2 --use_sim_time
ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot2 --timeout 200
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed: tinyRobot2 did not reach lounge"
        exit 1
fi

ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot1 --timeout 200
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed: tinyRobot1 did not reach pantry"
        exit 1
fi
