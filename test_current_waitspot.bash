#!/bin/bash

# NOTE: Test with finishing request set to [nothing], AND remove [supplies] as a parking spot

# FIX: Prevent startup race condition.
# Polling the ROS 2 network to ensure the RMF fleet adapter is fully initialized before firing dispatch commands.
while ! ros2 topic list | grep -q "/fleet_states"; do
  sleep 2
done

# Initialize robot positions
ros2 run rmf_demos_tasks dispatch_go_to_place -p tinyRobot1_charger -F tinyRobot -R tinyRobot1 --use_sim_time
ros2 run rmf_demos_tasks dispatch_go_to_place -p tinyRobot2_charger -F tinyRobot -R tinyRobot2 --use_sim_time
ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot1 --timeout 500
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed"
        exit -1
fi
ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot2 --timeout 500
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed"
        exit -1
fi


# Send tinyRobot1 to [tinyRobot2_charger]. It should be allocated to its current position [tinyRobot1_charger],
# since it is a valid waitspot.
ros2 run rmf_demos_tasks dispatch_go_to_place -p tinyRobot2_charger  -F tinyRobot -R tinyRobot1 --use_sim_time
sleep 5

# Send tinyRobot2 to [supplies] to free up space for tinyRobot1. Both robots should complete their tasks successfully.
ros2 run rmf_demos_tasks dispatch_go_to_place -p supplies  -F tinyRobot -R tinyRobot2 --use_sim_time
ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot1 --timeout 500
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed"
        exit -1
fi
ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot2 --timeout 500
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed"
        exit -1
fi
