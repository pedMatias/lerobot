# LeRobot Commands Reference

This document contains example commands for working with SO-101 and SO-100 robot arms using the LeRobot framework.

## Table of Contents
- [Setup and Calibration](#setup-and-calibration)
- [Teleoperation](#teleoperation)
- [Recording](#recording)
- [Replay](#replay)

---

## Setup and Calibration

### Find Connected Ports
```bash
python .\src\lerobot\find_port.py
```

### Calibrate Follower Arm
```bash
python -m lerobot.calibrate --robot.type=so101_follower --robot.port=COM4 --robot.id=my_awesome_follower_arm
```

### Calibrate Leader Arm
```bash
python -m lerobot.calibrate --teleop.type=so101_leader --teleop.port=COM3 --teleop.id=my_awesome_leader_arm
```

---

## Teleoperation

### Basic Teleoperation (Leader → Follower)
```bash
python -m lerobot.teleoperate --robot.type=so101_follower --robot.port=COM4 --robot.id=my_awesome_follower_arm --teleop.type=so101_leader --teleop.port=COM3 --teleop.id=my_awesome_leader_arm
```

---

## Recording

### Basic Recording (Python Module)
```bash
python -m  lerobot.record --robot.type=so101_follower --robot.port=COM4 --teleop.type=so101_leader --teleop.port=COM3 --dataset.repo_id=pedMatias/my_routine --dataset.num_episodes=1
```

### Recording with Display and Task Name (CLI)
```bash
lerobot-record --robot.type=so101_follower --robot.port=COM4 --robot.id=my_awesome_follower_arm --teleop.type=so101_leader --teleop.port=COM3 --teleop.id=my_awesome_leader_arm --display_data=true --dataset.repo_id=pedMatias/record-test-dance --dataset.num_episodes=1 --dataset.single_task="Just Dance"
```

---

## Replay

### Single Follower Arm Replay
```bash
lerobot-replay --robot.type=so101_follower --robot.port=COM4 --robot.id=my_awesome_follower_arm --dataset.repo_id=pedMatias/record-test-dance-up-and-down-2 --dataset.root=~/.cache/huggingface/lerobot --dataset.episode=0
```

#### Leader Arm as Follower
```bash
lerobot-replay --robot.type=so101_follower --robot.port=COM3 --robot.id=leader_as_follower_arm --dataset.repo_id=pedMatias/record-test-dance-up-and-down-2 --dataset.root=~/.cache/huggingface/lerobot --dataset.episode=0
```

### Multi-Arm Setup (Multiple SO-101)
```bash
lerobot-replay --robot.type=multi_so101_follower --robot.arm_ports='["COM3","COM4"]' --robot.id=my_multi_follower --dataset.repo_id=pedMatias/record-test-dance-up-and-down-2 --dataset.episode=0
```

---

## Notes

- Replace `COM3`, `COM4` with your actual serial ports
- Use `find_port.py` to identify connected devices
- The `dataset.repo_id` should point to your HuggingFace repository
- Episode numbers start at 0
