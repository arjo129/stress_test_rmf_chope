#!/bin/bash

# To enroll in the reservation system
ros2 run rmf_demos_tasks dispatch_go_to_place -p lounge -F tinyRobot -R tinyRobot2 --use_sim_time
ros2 run rmf_demos_tasks dispatch_go_to_place -p pantry -F tinyRobot -R tinyRobot1 --use_sim_time


ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot2 --timeout 500
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed"
        exit -1
fi
ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot1 --timeout 500
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed"
        exit -1
fi

ros2 run rmf_demos_tasks dispatch_patrol -F tinyRobot -R tinyRobot1 -p tinyRobot1_charger supplies -n 2 --use_sim_time
ros2 run rmf_demos_tasks dispatch_patrol -F tinyRobot -R tinyRobot2 -p supplies tinyRobot1_charger -n 2 --use_sim_time

ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot2 --timeout 500
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed"
        exit -1
fi
ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot1 --timeout 500
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed"
        exit -1
fi