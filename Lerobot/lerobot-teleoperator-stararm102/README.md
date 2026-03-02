# LeRobot + teleop Integration

## Getting Started

```bash
pip install lerobot_teleoperator_stararm102

lerobot-teleoperate \
    --robot.type=lerobot_robot_stararm102 \
    --robot.port=/dev/ttyUSB1 \
    --robot.id=my_awesome_stararm102_follower_arm \
    --teleop.type=lerobot_teleoperator_stararm102 \
    --teleop.port=/dev/ttyUSB0 \
    --teleop.id=my_awesome_stararm102_leader_arm
```
