#!/bin/bash
ros2 run rmf_demos_tasks dispatch_go_to_place -p tinyRobot1_charger -F tinyRobot -R tinyRobot2 --use_sim_time
ros2 run rmf_demos_tasks dispatch_go_to_place -p tinyRobot2_charger  -F tinyRobot -R tinyRobot1 --use_sim_time
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

ros2 run rmf_demos_tasks dispatch_go_to_place -p tinyRobot1_charger -F tinyRobot -R tinyRobot1 --use_sim_time
ros2 run rmf_demos_tasks get_robot_location -F tinyRobot -R tinyRobot1 --timeout 300 -B supplies
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed"
        exit -1
fi
ros2 run rmf_demos_tasks dispatch_go_to_place -p supplies -F tinyRobot -R tinyRobot2 --use_sim_time
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
ros2 run rmf_demos_tasks dispatch_go_to_place -p supplies -F tinyRobot -R tinyRobot1 --use_sim_time
ros2 run rmf_demos_tasks dispatch_go_to_place -p tinyRobot1_charger -F tinyRobot -R tinyRobot2 --use_sim_time
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