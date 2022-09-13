import sys
import os
import argparse
import pandas as pd
from sdwsn_controller.result_analysis import run_analysis


def main():
    parser = argparse.ArgumentParser(
        description='This script loads the results of the Orchestra experiment and plots \
        all charts including power, delay, reliability.')

    parser.add_argument('-e', '--elise-results', nargs='+',
                        help="path and name to CSV file to load, or list of CSV files.")
    parser.add_argument('-n', '--name', type=str, default='results',
                        help="name for your results.")
    parser.add_argument('-r', '--results-path', type=str, default='./results/',
                        help='Path to save results')

    args = parser.parse_args()

    elise_csv_files = args.elise_results
    name = args.name
    results_path = args.results_path

    os.makedirs(results_path, exist_ok=True)

    frames = []

    for elise_file in elise_csv_files:
        # print(f"elise_file: {elise_file}")
        df = pd.read_csv(elise_file)
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

    if len(elise_csv_files) > 1:
        print("Calculating average.")
        # Plot power
        run_analysis.plot_results_bar_chart(result, name+'_power', results_path,
                                            'counter', 'power_avg', 'Network average power $[\mu W]$', [4300, 4600])
        # Plot delay
        run_analysis.plot_results_bar_chart(result, name+'_delay', results_path,
                                            'counter', 'delay_avg', 'Network average delay $[ms]$')

        # Plot reliability
        run_analysis.plot_results_bar_chart(result, name+'_reliability', results_path,
                                            'counter', 'pdr_mean', 'Network average reliability', [0.92, 0.97])


if __name__ == '__main__':
    main()

    sys.exit(0)
