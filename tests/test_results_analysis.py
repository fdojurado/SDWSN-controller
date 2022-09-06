import sys
import os
import argparse
import pandas as pd
from sdwsn_controller.result_analysis import run_analysis


def main():
    parser = argparse.ArgumentParser(
        description='This script loads the results of the experiment and plots \
        all charts: Power vs. SF, Power vs. Reward, etc.')

    parser.add_argument('path', nargs='+',
                        help="path and name to CSV file to load, or list of CSV files.")
    parser.add_argument('-n', '--name', type=str, default='results',
                        help="name for your results.")
    parser.add_argument('-r', '--results-path', type=str, default='./results/',
                        help='Path to save results')

    args = parser.parse_args()

    csv_files = args.path
    name = args.name
    results_path = args.results_path

    os.makedirs(results_path, exist_ok=True)

    frames = []

    for file in csv_files:
        # print(f"file: {file}")
        df = pd.read_csv(file)
        df.drop(0, inplace=True)
        df['counter'] = range(len(df))
        frames.append(df)

    # print(frames)
    result = pd.concat(frames)
    # Delete any previous file with the same name
    if os.path.exists(results_path+"_"+name+".csv"):
        os.remove(results_path+"_"+name+".csv")
        print("The file has been deleted successfully")
    else:
        print("The file does not exist!")

    result.to_csv(results_path+name+".csv")

    if len(csv_files) > 1:
        print("Calculating average.")
         # Plot power
        run_analysis.plot_results(result, name+'_power', results_path,
                                  'counter', 'power_avg', 'Network average power [mW]', 'current_sf_len', True)
        # Plot delay
        run_analysis.plot_results(result, name+'_delay', results_path,
                                  'counter', 'delay_avg', 'Network average delay [ms]', 'current_sf_len', True)
        # Plot reliability
        run_analysis.plot_results(result, name+'_reliability', results_path,
                                  'counter', 'pdr_mean', 'Network average reliability', 'current_sf_len', True)
         # Reward vs slotframe size
        run_analysis.plot_results(result, name+'_reward', results_path,
                                  'counter', 'reward', 'Immediate reward', 'current_sf_len', True)

    else:
        print("Simple graph.")
        # Plot power
        run_analysis.plot_results(result, name+'_power', results_path,
                                  'counter', 'power_avg', r'$\hat{P_N}$', 'current_sf_len')
        # Plot delay
        run_analysis.plot_results(result, name+'_delay', results_path,
                                  'counter', 'delay_avg', r'$\hat{D_N}$', 'current_sf_len')
        # Plot reliability
        run_analysis.plot_results(result, name+'_reliability', results_path,
                                  'counter', 'pdr_mean', r'$\hat{R_N}$', 'current_sf_len')
        # Reward vs slotframe size
        run_analysis.plot_results(result, name+'_reward', results_path,
                                  'counter', 'reward', 'Immediate reward', 'current_sf_len')


if __name__ == '__main__':
    main()

    sys.exit(0)
