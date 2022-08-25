import sys
import os
import argparse
import pandas as pd
from sdwsn_controller.result_analysis import run_analysis


def main():
    parser = argparse.ArgumentParser(
        description='This script loads the results of the training and plots the \
            average episode length and accumulative reward.')

    parser.add_argument('path', type=str,
                        help="path and name to CSV file to load.")
    parser.add_argument('name', type=str,
                        help="name for your results.")
    parser.add_argument('-r', '--results-path', type=str, default='./results/',
                        help='Path to save results')

    args = parser.parse_args()

    file = args.path
    name = args.name
    results_path = args.results_path

    df = pd.read_csv(file)

    os.makedirs(results_path, exist_ok=True)

    run_analysis.plot_training_progress(df, name, results_path)


if __name__ == '__main__':
    main()

    sys.exit(0)
