#!/bin/bash

# NOTE: Test with finishing request set to [nothing]

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


# Send tinyRobot2 to [coe], then send tinyRobot1 to [coe]
ros2 run rmf_demos_tasks dispatch_go_to_place -p coe -F tinyRobot -R tinyRobot2 --use_sim_time
ros2 run rmf_demos_tasks dispatch_go_to_place -p coe -F tinyRobot -R tinyRobot1 --use_sim_time

# Send a follow-up task for tinyRobot2 to [tinyRobot2_charger] after it completes the previous task
ros2 run rmf_demos_tasks dispatch_go_to_place -p tinyRobot2_charger -F tinyRobot -R tinyRobot2 --use_sim_time
sleep 6

# Cancel tinyRobot2's [coe] task. tinyRobot2 should move to tinyRobot2_charger, and [coe] will
# be freed up for tinyRobot1
ros2 run rmf_demos_tasks cancel_robot_task -F tinyRobot -R tinyRobot2
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
