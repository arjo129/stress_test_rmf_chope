#!/bin/bash
ros2 run rmf_demos_tasks dispatch_go_to_place -p pantry -F tinyRobot -R tinyRobot2 --use_sim_time
sleep 10
ros2 run rmf_demos_tasks dispatch_go_to_place -p pantry  -F tinyRobot -R tinyRobot1 --use_sim_time
ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot2 --timeout 200
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed"
        exit -1
fi

ros2 run rmf_demos_tasks dispatch_go_to_place -p lounge -F tinyRobot -R tinyRobot2 --use_sim_time
ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot2 --timeout 200
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed"
        exit -1
fi

ros2 run rmf_demos_tasks wait_for_task_complete -F tinyRobot -R tinyRobot1 --timeout 200
ret=$?
if [ $ret -ne 0 ]; then
        echo "Test failed"
        exit -1
fi
