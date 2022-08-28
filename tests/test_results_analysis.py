import sys
import os
import argparse
import pandas as pd
from sdwsn_controller.result_analysis import run_analysis


def main():
    parser = argparse.ArgumentParser(
        description='This script loads the results of the experiment and plots \
        all charts: Power vs. SF, Power vs. Reward, etc.')

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

    # Plot power
    run_analysis.plot_results(df, name+'power', results_path,
                              range(len(df['timestamp'])), df['power_normalized'].astype(float), r'$\hat{P_N}$', df['reward'].astype(float), df['current_sf_len'].astype(int))

    # Plot delay
    run_analysis.plot_results(df, name+'delay', results_path,
                              range(len(df['timestamp'])), df['delay_normalized'].astype(float), r'$\hat{D_N}$', df['reward'].astype(float), df['current_sf_len'].astype(int))
    # Plot reliability
    run_analysis.plot_results(df, name+'reliability', results_path,
                              range(len(df['timestamp'])), df['pdr_mean'].astype(float), r'$\hat{R_N}$', df['reward'].astype(float), df['current_sf_len'].astype(int))


if __name__ == '__main__':
    main()

    sys.exit(0)
