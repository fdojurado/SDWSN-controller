import sys
import os
import argparse
import pandas as pd
from sdwsn_controller.result_analysis import run_analysis


def main():
    parser = argparse.ArgumentParser(
        description='This script loads the results of the approximation model \
            results and plots the fitted curves')

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

    # run_analysis.plot(df, name, results_path)

    # run_analysis.plot_against_sf_size(df, name, results_path)

    # run_analysis.plot_fit_curves(df, name, results_path)
    # Normalized power
    run_analysis.plot_fit_curves(
        df,
        name+'_power',
        results_path,
        'current_sf_len',
        'power_unbiased',
        r'$|C|$',
        r'$\widetilde{P}$',
        4,
        [8, 0.89],
        [0.86, 0.9]
    )
    # Normalized delay
    run_analysis.plot_fit_curves(
        df,
        name+'_delay',
        results_path,
        'current_sf_len',
        'delay_unbiased',
        r'$|C|$',
        r'$\widetilde{D}$',
        3,
        [8, 0.045],
        [0, 0.06]
    )
    run_analysis.plot_fit_curves(
        df,
        name+'_reliability',
        results_path,
        'current_sf_len',
        'pdr_unbiased',
        r'$|C|$',
        r'$\widetilde{R}$',
        1,
        [25, 0.7],
        [0.65, 1]
    )
    # run_analysis.average_network_pdr_ci_sf_size(df, 'pdr', results_path)


if __name__ == '__main__':
    main()

    sys.exit(0)
