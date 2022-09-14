import sys
import os
import argparse
import pandas as pd
from sdwsn_controller.result_analysis import run_analysis


def pre_processing(csv_files):
    frames = []
    for cv_file in csv_files:
        # print(f"elise_file: {elise_file}")
        df = pd.read_csv(cv_file)
        df.drop(0, inplace=True)
        df['counter'] = range(len(df))
        frames.append(df)

    result = pd.concat(frames)

    return result


def rm_file(path, name):
    if os.path.exists(path+"_"+name+".csv"):
        os.remove(path+"_"+name+".csv")
        print("The file has been deleted successfully")
    else:
        print("The file does not exist!")


def main():
    parser = argparse.ArgumentParser(
        description='This script loads the results of the Orchestra experiment and plots \
        all charts including power, delay, reliability.')

    parser.add_argument('-e', '--elise-results', nargs='+',
                        help="path and name to ELISE CSV file to load, or list of CSV files.")
    parser.add_argument('-o', '--orchestra-results', nargs='+',
                        help="path and name to Orchestra CSV file to load, or list of CSV files.")
    parser.add_argument('-n', '--name', type=str, default='results',
                        help="name for your results.")
    parser.add_argument('-r', '--results-path', type=str, default='./results/',
                        help='Path to save results')

    args = parser.parse_args()

    elise_csv_files = args.elise_results
    orchestra_csv_files = args.orchestra_results
    name = args.name
    results_path = args.results_path

    os.makedirs(results_path, exist_ok=True)

    # ELISE pre-processing
    elise_result = pre_processing(elise_csv_files)
    # Delete any previous file with the same name
    rm_file(results_path, name+"_elise")
    elise_result.to_csv(results_path+name+"_elise.csv")

    # Orchestra pre-processing
    orchestra_result = pre_processing(orchestra_csv_files)
    rm_file(results_path, name+"_orchestra")
    orchestra_result.to_csv(results_path+name+"_orchestra.csv")

    if len(elise_csv_files) > 1:
        print("Calculating average.")
        # Plot power
        run_analysis.plot_results_bar_chart(elise_result, name+'_power', results_path,
                                            'counter', 'power_avg', 'Network average power $[\mu W]$',
                                            orchestra_result,
                                            [4300, 4600])
        # Plot delay
        run_analysis.plot_results_bar_chart(elise_result, name+'_delay', results_path,
                                            'counter', 'delay_avg', 'Network average delay $[ms]$',
                                            orchestra_result)

        # Plot reliability
        run_analysis.plot_results_bar_chart(elise_result, name+'_reliability', results_path,
                                            'counter', 'pdr_mean', 'Network average reliability',
                                            orchestra_result,
                                            [0.92, 0.97])


if __name__ == '__main__':
    main()

    sys.exit(0)
