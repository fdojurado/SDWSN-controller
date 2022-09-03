import sys
import os
import argparse
import pandas as pd
from sdwsn_controller.result_analysis import run_analysis


def main():
    parser = argparse.ArgumentParser(
        description='This script loads the results, in CSV format, of the training and plots the \
            average episode length and accumulative reward. This is currently working only with three csv files.')

    parser.add_argument('path', nargs='+',
                        help="path and name to CSV file to load, or list of CSV files.")
    parser.add_argument('-n', '--name', type=str, default='results',
                        help="name for your results.")
    parser.add_argument('-r', '--results-path', type=str, default='./results/',
                        help='Path to save results')

    args = parser.parse_args()

    file = args.path
    name = args.name
    results_path = args.results_path

    os.makedirs(results_path, exist_ok=True)

    frames = []
    count = 0

    for csv_file in file:
        print(f"csv file: {csv_file}")
        count += 1
        df = pd.read_csv(csv_file)
        df.rename(columns={'Step': 'Step'+str(count)}, inplace=True)
        df.rename(columns={'Value': 'Value'+str(count)}, inplace=True)
        frames.append(df)

    result = pd.concat(frames, axis=1)
    # Delete any previous file with the same name
    if os.path.exists(results_path+"_"+name+".csv"):
        os.remove(results_path+"_"+name+".csv")
        print("The file has been deleted successfully")
    else:
        print("The file does not exist!")

    result.to_csv(results_path+name+".csv")

    run_analysis.plot_training_progress(result, name, results_path)


if __name__ == '__main__':
    main()

    sys.exit(0)
