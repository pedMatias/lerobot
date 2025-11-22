#!/usr/bin/env python

# Copyright 2025 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import time
from functools import cached_property
from typing import Any

from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.robots.so101_follower import SO101Follower
from lerobot.robots.so101_follower.config_so101_follower import SO101FollowerConfig

from ..robot import Robot
from .config_multi_so101_follower import MultiSO101FollowerConfig

logger = logging.getLogger(__name__)


class MultiSO101Follower(Robot):
    """
    Multi-arm SO-101 Follower configuration supporting N arms.
    Each arm is connected to a separate serial port and can replay the same dataset simultaneously.
    Arms are automatically named arm1, arm2, arm3, etc. based on the order of ports provided.
    """

    config_class = MultiSO101FollowerConfig
    name = "multi_so101_follower"

    def __init__(self, config: MultiSO101FollowerConfig):
        super().__init__(config)
        self.config = config

        if not config.arm_ports:
            raise ValueError("arm_ports must contain at least one port")

        # Create arms dynamically based on the number of ports provided
        self.arms = {}
        self.arm_names = []

        for idx, port in enumerate(config.arm_ports, start=1):
            arm_name = f"arm{idx}"
            self.arm_names.append(arm_name)

            arm_config = SO101FollowerConfig(
                id=f"{config.id}_{arm_name}" if config.id else None,
                calibration_dir=config.calibration_dir,
                port=port,
                disable_torque_on_disconnect=config.disable_torque_on_disconnect,
                max_relative_target=config.max_relative_target,
                use_degrees=config.use_degrees,
                cameras={},
            )

            self.arms[arm_name] = SO101Follower(arm_config)

        self.cameras = make_cameras_from_configs(config.cameras)

    @property
    def _motors_ft(self) -> dict[str, type]:
        """Generate motor features with arm name prefixes (e.g., arm1_shoulder_pan.pos)"""
        motors_ft = {}
        for arm_name, arm in self.arms.items():
            for motor in arm.bus.motors:
                motors_ft[f"{arm_name}_{motor}.pos"] = float
        return motors_ft

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3) for cam in self.cameras
        }

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        return {**self._motors_ft, **self._cameras_ft}

    @cached_property
    def action_features(self) -> dict[str, type]:
        return self._motors_ft

    @property
    def is_connected(self) -> bool:
        return all(arm.bus.is_connected for arm in self.arms.values()) and all(
            cam.is_connected for cam in self.cameras.values()
        )

    def connect(self, calibrate: bool = True) -> None:
        for arm_name, arm in self.arms.items():
            logger.info(f"Connecting {arm_name}...")
            arm.connect(calibrate)

        for cam in self.cameras.values():
            cam.connect()

    @property
    def is_calibrated(self) -> bool:
        return all(arm.is_calibrated for arm in self.arms.values())

    def calibrate(self) -> None:
        for arm_name, arm in self.arms.items():
            logger.info(f"Calibrating {arm_name}...")
            arm.calibrate()

    def configure(self) -> None:
        for arm in self.arms.values():
            arm.configure()

    def setup_motors(self) -> None:
        for arm in self.arms.values():
            arm.setup_motors()

    def get_observation(self) -> dict[str, Any]:
        obs_dict = {}

        # Get observations from all arms and add arm name prefix
        for arm_name, arm in self.arms.items():
            arm_obs = arm.get_observation()
            obs_dict.update({f"{arm_name}_{key}": value for key, value in arm_obs.items()})

        # Get camera observations
        for cam_key, cam in self.cameras.items():
            start = time.perf_counter()
            obs_dict[cam_key] = cam.async_read()
            dt_ms = (time.perf_counter() - start) * 1e3
            logger.debug(f"{self} read {cam_key}: {dt_ms:.1f}ms")

        return obs_dict

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """
        Routes actions to appropriate arms.

        For single-arm datasets replayed on multiple arms:
        - If action keys have no prefix, broadcast to all arms
        - If action keys have arm prefixes (arm1_, arm2_), route to specific arms
        """
        result = {}

        # Check if actions have arm prefixes
        has_prefixes = any(key.startswith(f"{arm_name}_") for arm_name in self.arm_names for key in action.keys())

        if has_prefixes:
            # Actions have arm-specific prefixes, route to specific arms
            for arm_name, arm in self.arms.items():
                # Extract actions for this arm
                arm_action = {
                    key.removeprefix(f"{arm_name}_"): value
                    for key, value in action.items()
                    if key.startswith(f"{arm_name}_")
                }

                if arm_action:
                    send_action_result = arm.send_action(arm_action)
                    # Add prefix back
                    result.update({f"{arm_name}_{key}": value for key, value in send_action_result.items()})
        else:
            # No prefixes - broadcast same action to all arms
            for arm_name, arm in self.arms.items():
                send_action_result = arm.send_action(action)
                # Add prefix to results
                result.update({f"{arm_name}_{key}": value for key, value in send_action_result.items()})

        return result

    def disconnect(self):
        for arm in self.arms.values():
            arm.disconnect()

        for cam in self.cameras.values():
            cam.disconnect()
