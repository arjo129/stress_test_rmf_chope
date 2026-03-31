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


# Start a patrol ask for tinyRobot1 to [hardware_2] and tinyRobot2 to [pantry]
ros2 run rmf_demos_tasks dispatch_patrol -F tinyRobot -R tinyRobot1 -p hardware_2  --use_sim_time
ros2 run rmf_demos_tasks dispatch_patrol -F tinyRobot -R tinyRobot2 -p pantry  --use_sim_time
sleep 10

# Trigger the emergency signal. Both robots should find a free spot to park.
ros2 topic pub /emergency_signal rmf_fleet_msgs/msg/EmergencySignal "{\"is_emergency\": true, \"fleet_names\": []}" --once --qos-reliability reliable --qos-durability transient_local
sleep 20

# Switch off the emergency signal. both robots should resume their tasks.
ros2 topic pub /emergency_signal rmf_fleet_msgs/msg/EmergencySignal "{\"is_emergency\": false, \"fleet_names\": []}" --once --qos-reliability reliable --qos-durability transient_local
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
