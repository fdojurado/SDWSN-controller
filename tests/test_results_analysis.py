import sys
import os
import argparse
import pathlib
import pandas as pd
from sdwsn_controller.result_analysis import run_analysis


def main():
    parser = argparse.ArgumentParser(
        description='This script loads the results of the experiment and plots \
        the all charts.')

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

    run_analysis.plot(df, name, results_path)

    run_analysis.plot_against_sf_size(df, name, results_path)

    run_analysis.plot_fit_curves(df, name+"_fitted_curves", results_path)


if __name__ == '__main__':
    main()

    sys.exit(0)
