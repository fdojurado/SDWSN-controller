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
import os
import sys


from sdwsn_controller.config import SDWSNControllerConfig, CONTROLLERS


from sdwsn_controller.result_analysis.run_analysis import run_analysis


import pandas as pd


from stable_baselines3 import PPO


CONFIG_FILE = "numerical_controller_rl.json"
TRAINED_MODEL = "./trained_model/best_model.zip"


def evaluation(env, model_path, controller, output_folder, simulation_name):
    model = PPO.load(model_path)

    # Test the trained agent
    for i in range(10):
        # Pandas df to store results at each iteration
        df = pd.DataFrame()
        obs, _ = env.reset()
        done = False
        acc_reward = 0
        # Get last observations non normalized
        observations = env.controller.get_state()
        assert 0 <= observations['alpha'] <= 1
        assert 0 <= observations['beta'] <= 1
        assert 0 <= observations['delta'] <= 1
        assert observations['last_ts_in_schedule'] > 1
        # get requirements
        user_req_type = controller.user_requirements_type
        print(f"user req: {controller.user_requirements}")
        match user_req_type:
            case 'energy':
                controller.current_slotframe_size = env.controller.last_tsch_link+5
            case 'delay':
                controller.current_slotframe_size = env.max_slotframe_size-5
            case 'pdr':
                controller.current_slotframe_size = env.max_slotframe_size-5
            case 'balanced':
                env.controller.current_slotframe_size = env.max_slotframe_size-5
            case _:
                print("Unknow user requirements.")
        while (not done):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            # Get last observations non normalized
            observations = controller.get_state()
            acc_reward += reward
            # Get last observations non normalized
            observations = controller.get_state()
            assert 0 <= observations['alpha'] <= 1
            assert 0 <= observations['beta'] <= 1
            assert 0 <= observations['delta'] <= 1
            assert observations['last_ts_in_schedule'] > 1
            # Add row to DataFrame
            new_cycle = pd.DataFrame([info])
            df = pd.concat([df, new_cycle], axis=0, ignore_index=True)
        df.to_csv(output_folder+simulation_name+str(i)+'.csv')
        run_analysis(simulation_name + str(i), output_folder)


def result_analysis(path, output_folder):
    df = pd.read_csv(path)
    # Normalized power
    run_analysis.plot_fit_curves(
        df=df,
        title='power',
        path=output_folder,
        x_axis='timestamp',
        y_axis='power_normalized',
        x_axis_name=r'$|C|$',
        y_axis_name=r'$\widetilde{P}$',
        degree=4,
        # txt_loc=[8, 0.89],
        # y_axis_limit=[0.86, 0.9]
    )
    # Normalized delay
    run_analysis.plot_fit_curves(
        df=df,
        title='delay',
        path=output_folder,
        x_axis='timestamp',
        y_axis='delay_normalized',
        x_axis_name=r'$|C|$',
        y_axis_name=r'$\widetilde{D}$',
        degree=3,
        # txt_loc=[8, 0.045],
        # y_axis_limit=[0, 0.95]
    )
    run_analysis.plot_fit_curves(
        df=df,
        title='reliability',
        path=output_folder,
        x_axis='timestamp',
        y_axis='pdr_mean',
        x_axis_name=r'$|C|$',
        y_axis_name=r'$\widetilde{R}$',
        degree=1,
        # txt_loc=[25, 0.7],
        # y_axis_limit=[0.65, 1]
    )
    # Metrics vs. Slotframe Size
    run_analysis.plot_against_sf_size(
        df=df,
        title="slotframe_size",
        path=output_folder
    )


def main():
    """
    This test the training, loading and testing of RL env.
    We dont use DB to avoid reducing the processing speed
    """
    # ----------------- RL environment, setup --------------------
    # Create output folder
    output_folder = './output/'
    os.makedirs(output_folder, exist_ok=True)

    # Monitor the environment
    log_dir = './tensorlog/'
    os.makedirs(log_dir, exist_ok=True)
    # Monitor the environment
    monitor_log_dir = './trained_model/'
    os.makedirs(monitor_log_dir, exist_ok=True)
    # -------------------- setup controller ---------------------
    config = SDWSNControllerConfig.from_json_file(CONFIG_FILE)
    controller_class = CONTROLLERS[config.controller_type]
    controller = controller_class(config)
    # ----------------- Test environment ----------------------------
    test_env = controller.reinforcement_learning.env
    evaluation(test_env, TRAINED_MODEL, controller=controller,
               output_folder=output_folder, simulation_name="test numerical")
    controller.stop()
    # Delete folders
    # try:
    #     shutil.rmtree(output_folder)
    # except OSError as e:
    #     print("Error: %s - %s." % (e.filename, e.strerror))
    # try:
    #     shutil.rmtree(log_dir)
    # except OSError as e:
    #     print("Error: %s - %s." % (e.filename, e.strerror))


if __name__ == '__main__':
    main()
    sys.exit(0)
