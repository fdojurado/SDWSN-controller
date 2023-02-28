#!/usr/bin/python3
#
# Copyright (C) 2022  Fernando Jurado-Lasso <ffjla@dtu.dk>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from sdwsn_controller.config import SDWSNControllerConfig, CONTROLLERS
from rich.logging import RichHandler
import logging.config
import sys

CONFIG_FILE = "native_controller_orchestra.json"


def run_data_plane(env):
    num_actions = 0
    for _ in range(1):
        env.reset()
        done = False
        acc_reward = 0
        # Set initial user requirements
        env.controller.user_requirements = (0.4, 0.3, 0.3)
        while (not done):
            if num_actions == 40:
                env.controller.user_requirements = (0.1, 0.8, 0.1)
            if num_actions == 80:
                env.controller.user_requirements = (0.8, 0.1, 0.1)
            if num_actions == 120:
                env.controller.user_requirements = (0.1, 0.1, 0.8)
            num_actions += 1
            action = 2
            obs, reward, done, _ = env.step(action)
            acc_reward += reward
            if done:
                print(f"episode done. reward: {acc_reward}")
                env.render()

    env.close()


def main():

    # -------------------- Create logger --------------------
    logger = logging.getLogger('main')

    formatter = logging.Formatter(
        '%(asctime)s - %(message)s')
    logger.setLevel(logging.DEBUG)

    stream_handler = RichHandler(rich_tracebacks=True)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    logFilePath = "my.log"
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s |  %(levelname)s: %(message)s')
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=logFilePath, when='midnight', backupCount=30)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    # -------------------- setup controller --------------------
    config = SDWSNControllerConfig.from_json_file(CONFIG_FILE)
    controller_class = CONTROLLERS[config.controller_type]
    controller = controller_class(config)
    # --------------------Start data plane ------------------------
    # Let's start the data plane first
    run_data_plane(controller.reinforcement_learning.env)

    logger.info('done, exiting.')

    controller.stop()

    return


if __name__ == '__main__':
    main()
    sys.exit(0)
