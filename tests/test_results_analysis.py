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
                                  'counter', 'power_avg', 'Network average power $[\mu W]$', 'Network avg. power', 'current_sf_len', 'slotframe size ('+r'$\tau$'+')', r'$\tau$', [4390, 4390, 4390, 4390], True, None, (0.01, 0.55))
        # Plot delay
        run_analysis.plot_results(result, name+'_delay', results_path,
                                  'counter', 'delay_avg', 'Network average delay $[ms]$', 'Network avg. delay', 'current_sf_len', 'slotframe size ('+r'$\tau$'+')', r'$\tau$', [350, 350, 350, 350], True, None, (0.01, 0.8))
        # Plot reliability
        run_analysis.plot_results(result, name+'_reliability', results_path,
                                  'counter', 'pdr_mean', 'Network average reliability', 'Network avg. reliability', 'current_sf_len', 'slotframe size ('+r'$\tau$'+')', r'$\tau$', [0.775, 0.775, 0.775, 0.775], True, [0.7, 1.0], (0.01, 0.5))
        # Reward vs slotframe size
        run_analysis.plot_results(result, name+'_reward', results_path,
                                  'counter', 'reward', 'Average immediate reward', 'Avg. immediate reward', 'current_sf_len', 'slotframe size ('+r'$\tau$'+')', r'$\tau$', [1.050, 1.050, 01.050, 1.050], True, None, (0.01, 0.8))

    else:
        print("Simple graph.")
        # Plot power
        run_analysis.plot_results(result, name+'_power', results_path,
                                  'counter', 'power_avg', 'Network average power $[\mu W]$', 'Network avg. power', 'current_sf_len', 'slotframe size ('+r'$\tau$'+')', r'$\tau$', [10, 10, 10, 10], False, None, (0.01, 0.6))
        # Plot delay
        run_analysis.plot_results(result, name+'_delay', results_path,
                                  'counter', 'delay_avg', 'Network average delay $[ms]$', 'Network avg. delay', 'current_sf_len', 'slotframe size ('+r'$\tau$'+')', r'$\tau$', [10, 10, 10, 10])
        # Plot reliability
        run_analysis.plot_results(result, name+'_reliability', results_path,
                                  'counter', 'pdr_mean', 'Network average reliability', 'Network avg. reliability', 'current_sf_len', 'slotframe size ('+r'$\tau$'+')', r'$\tau$', [10, 10, 10, 10], False, [0.7, 1.0], (0.01, 0.5))
        # Reward vs slotframe size
        run_analysis.plot_results(result, name+'_reward', results_path,
                                  'counter', 'reward', 'Immediate reward', 'Immediate reward', 'current_sf_len', r'$\tau$', r'$\tau$')


if __name__ == '__main__':
    main()

    sys.exit(0)
