#!/usr/bin/env python3
import re
from numpy import average
import pandas as pd
import numpy as np
import matplotlib.pyplot as pl
import math
from numpy import arange
from scipy.optimize import curve_fit
from sdwsn_database.database import OBSERVATIONS


#######################################################
def average_network_pdr(df):
    fig, ax = pl.subplots()  # Create a figure containing a single axes.
    # Plot the power consumption
    ax_ticks = np.arange(0, 1, 0.5)
    ax.set_yticks(ax_ticks)
    ax.plot(range(len(df['timestamp'])), df['pdr_mean'], 'b-o')
    ax.set_xlabel('Cycles')
    ax.set_ylabel('PDR', color='b')
    # Plot the slotframe size if a different axis
    ax2 = ax.twinx()
    ticks = np.arange(0, 60, 5)
    ax2.set_yticks(ticks)
    ax2.plot(range(len(df['timestamp'])), df['current_sf_len'], 'g-o')
    ax2.set_ylabel('Slotframe size', color='g')

    pl.savefig("pdr.pdf", bbox_inches='tight')
    pl.close()
#######################################################


def average_network_delay(df):
    fig, ax = pl.subplots()  # Create a figure containing a single axes.
    # Plot the power consumption
    ax.plot(range(len(df['timestamp'])), df['delay_avg'], 'b-o')
    ax.set_xlabel('Cycles')
    ax.set_ylabel('Delay (ms)', color='b')
    # Plot the slotframe size if a different axis
    ax2 = ax.twinx()
    ticks = np.arange(0, 60, 5)
    ax2.set_yticks(ticks)
    ax2.plot(range(len(df['timestamp'])), df['current_sf_len'], 'g-o')
    ax2.set_ylabel('Slotframe size', color='g')

    pl.savefig("delay.pdf", bbox_inches='tight')
    pl.close()


#######################################################
def average_network_power_consumption(df):
    # Remove first row
    fig, ax = pl.subplots()  # Create a figure containing a single axes.
    # Plot the power consumption
    ax.plot(range(len(df['timestamp'])), df['power_avg'], 'b-o')
    ax.set_xlabel('Cycles')
    ax.set_ylabel('Power (mW)', color='b')
    # Plot the slotframe size if a different axis
    ax2 = ax.twinx()
    ticks = np.arange(0, 60, 5)
    ax2.set_yticks(ticks)
    ax2.plot(range(len(df['timestamp'])), df['current_sf_len'], 'g-o')
    ax2.set_ylabel('Slotframe size', color='g')

    pl.savefig("power.pdf", bbox_inches='tight')
    pl.close()


#######################################################
# Plot the results of a given metric as a bar chart
def reward_plot(df, reward, values):
    pl.figure(figsize=(5, 4))
    fig, ax = pl.subplots()  # Create a figure containing a single axes.
    ax2 = ax.twinx()
    ticks = np.arange(0, 60, 5)
    ax2.set_yticks(ticks)
    # Plot some data on the axes.
    ax.plot(range(len(reward['timestamp'])), values.cumsum(), 'b-o')
    # Plot some data on the axes.
    ax2.plot(range(len(df['timestamp'])), df['current_sf_len'], 'g-o')
    # last ts in schedule
    ax2.plot(range(len(df['timestamp'])), df['last_ts_in_schedule'], 'r-o')

    ax.set_xlabel('Cycles')
    ax.set_ylabel('Reward', color='b')
    ax2.set_ylabel('Slotframe size', color='g')

    # # Add a legend.
    # ax.legend();

    pl.savefig("plot_rl.pdf", bbox_inches='tight')
    pl.close()


#######################################################
def plot(df, name):
    title_font_size = 8
    x_axis_font_size = 8
    y_axis_font_size = 8
    ticks_font_size = 7
    data_marker_size = 1.5
    legend_font_size = 6
    title_fontweight = 'bold'
    axis_labels_fontstyle = 'italic'
    # Drop first row
    df.drop(0, inplace=True)
    fig, axs = pl.subplots(2, 2, layout='constrained')
    alpha_weight = df['alpha'].iloc[0]
    beta_weight = df['beta'].iloc[0]
    delta_weight = df['delta'].iloc[0]
    last_ts = df['last_ts_in_schedule'].iloc[0]
    fig.suptitle(r'$\alpha={},\beta={},\delta={},last~ts={}$'.format(
        alpha_weight, beta_weight, delta_weight, last_ts), fontsize=title_font_size)
    # $\alpha=0.8,\beta=0.1,\delta=0.1$
    # First char is the reward and slotframe size over time
    reward = df.copy(deep=True)
    values = reward['reward'].astype(float)
    # values = values * -1
    axs[0, 0].set_title('Reward and SF size over time',
                        fontsize=title_font_size, fontweight=title_fontweight)
    axs[0, 0].set_xlabel('Cycles', fontsize=x_axis_font_size,
                         fontstyle=axis_labels_fontstyle)
    axs[0, 0].set_ylabel('Reward', fontsize=y_axis_font_size,
                         fontstyle=axis_labels_fontstyle)
    axs[0, 0].tick_params(axis='both', which='major',
                          labelsize=ticks_font_size)
    axs2 = axs[0, 0].twinx()
    axs2.tick_params(axis='both', which='major', labelsize=ticks_font_size)
    axs2.set_ylabel('Slotframe size', fontsize=y_axis_font_size,
                    fontstyle=axis_labels_fontstyle)
    l1, = axs[0, 0].plot(range(len(reward['timestamp'])),
                         values, 'b-o', markersize=data_marker_size)
    l2, = axs2.plot(range(len(df['timestamp'])), df['current_sf_len'],
                    'g-o', markersize=data_marker_size)
    axs2.legend([l1, l2], ['Reward', 'SF size'], fontsize=legend_font_size)

    # Plot power and SF size
    axs[0, 1].set_title('Network power and SF size over time',
                        fontsize=title_font_size, fontweight=title_fontweight)
    axs[0, 1].set_xlabel('Cycles', fontsize=x_axis_font_size,
                         fontstyle=axis_labels_fontstyle)
    axs[0, 1].set_ylabel(
        'Power [mW]', fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)
    axs[0, 1].tick_params(axis='both', which='major',
                          labelsize=ticks_font_size)
    axs2 = axs[0, 1].twinx()
    axs2.tick_params(axis='both', which='major', labelsize=ticks_font_size)
    axs2.set_ylabel('Slotframe size', fontsize=y_axis_font_size,
                    fontstyle=axis_labels_fontstyle)
    l1, = axs[0, 1].plot(range(len(df['timestamp'])), df['power_avg'],
                         'b-o', markersize=data_marker_size)
    l2, = axs2.plot(range(len(df['timestamp'])), df['current_sf_len'],
                    'g-o', markersize=data_marker_size)
    axs2.legend([l1, l2], ['Power', 'SF size'],
                fontsize=legend_font_size, loc='upper center')

    # Plot delay and SF size
    axs[1, 0].set_title('Network delay and SF size over time',
                        fontsize=title_font_size, fontweight=title_fontweight)
    axs[1, 0].set_xlabel('Cycles', fontsize=x_axis_font_size,
                         fontstyle=axis_labels_fontstyle)
    axs[1, 0].set_ylabel(
        'delay [ms]', fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)
    axs[1, 0].tick_params(axis='both', which='major',
                          labelsize=ticks_font_size)
    axs2 = axs[1, 0].twinx()
    axs2.tick_params(axis='both', which='major', labelsize=ticks_font_size)
    axs2.set_ylabel('Slotframe size', fontsize=y_axis_font_size,
                    fontstyle=axis_labels_fontstyle)
    l1, = axs[1, 0].plot(range(len(df['timestamp'])), df['delay_avg'],
                         'b-o', markersize=data_marker_size)
    l2, = axs2.plot(range(len(df['timestamp'])), df['current_sf_len'],
                    'g-o', markersize=data_marker_size)
    axs2.legend([l1, l2], ['Delay', 'SF size'],
                fontsize=legend_font_size, loc='upper center')

    # Plot PDR and SF size
    axs[1, 1].set_title('Network PDR and SF size over time',
                        fontsize=title_font_size, fontweight=title_fontweight)
    axs[1, 1].set_xlabel('Cycles', fontsize=x_axis_font_size,
                         fontstyle=axis_labels_fontstyle)
    axs[1, 1].set_ylabel('PDR', fontsize=y_axis_font_size,
                         fontstyle=axis_labels_fontstyle)
    axs[1, 1].tick_params(axis='both', which='major',
                          labelsize=ticks_font_size)
    axs2 = axs[1, 1].twinx()
    axs2.tick_params(axis='both', which='major', labelsize=ticks_font_size)
    axs2.set_ylabel('Slotframe size', fontsize=y_axis_font_size,
                    fontstyle=axis_labels_fontstyle)
    l1, = axs[1, 1].plot(range(len(df['timestamp'])), df['pdr_mean'],
                         'b-o', markersize=data_marker_size)
    l2, = axs2.plot(range(len(df['timestamp'])), df['current_sf_len'],
                    'g-o', markersize=data_marker_size)
    axs[1, 1].set_yticks(np.arange(0, max(df['pdr_mean'])+0.1, 0.2))
    axs2.legend([l1, l2], ['PDR', 'SF size'],
                fontsize=legend_font_size, loc='lower center')

    pl.savefig(name+'.pdf'.format(
        alpha_weight, beta_weight, delta_weight, last_ts), bbox_inches='tight')
    pl.close()
#######################################################


def calculate_confidence_interval(df, x_name, y_name):
    # print(df)
    # print('-'*30)

    stats = df.groupby([x_name])[
        y_name].agg(['mean', 'count', 'std'])

    stats = stats.reset_index()

    # print(stats)
    # print('-'*30)

    ci95_hi = []
    ci95_lo = []

    for i in stats.index:
        _, m, c, s = stats.loc[i]
        ci95_hi.append(m + 1.96*s/math.sqrt(c))
        ci95_lo.append(m - 1.96*s/math.sqrt(c))

    stats['ci95_hi'] = ci95_hi
    stats['ci95_lo'] = ci95_lo
    # print(stats)
    return stats
#######################################################


def plot_against_sf_size(df, name):
    title_font_size = 8
    x_axis_font_size = 8
    y_axis_font_size = 8
    ticks_font_size = 7
    data_marker_size = 1.5
    legend_font_size = 6
    title_fontweight = 'bold'
    axis_labels_fontstyle = 'italic'
    # Drop first row
    fig, axs = pl.subplots(2, 2, layout='constrained')
    alpha_weight = df['alpha'].iloc[0]
    beta_weight = df['beta'].iloc[0]
    delta_weight = df['delta'].iloc[0]
    last_ts = df['last_ts_in_schedule'].iloc[0]
    fig.suptitle(r'$\alpha={},\beta={},\delta={},last~ts={}$'.format(
        alpha_weight, beta_weight, delta_weight, last_ts), fontsize=title_font_size)
    # $\alpha=0.8,\beta=0.1,\delta=0.1$
    # First plot is the reward vs. slotframe size
    reward = df.copy(deep=True)
    values = reward['reward'].astype(float)
    axs[0, 0].set_title('Reward vs SF size',
                        fontsize=title_font_size, fontweight=title_fontweight)
    axs[0, 0].set_xlabel('SF size', fontsize=x_axis_font_size,
                         fontstyle=axis_labels_fontstyle)
    axs[0, 0].set_ylabel('Reward', fontsize=y_axis_font_size,
                         fontstyle=axis_labels_fontstyle)
    axs[0, 0].tick_params(axis='both', which='major',
                          labelsize=ticks_font_size)
    # Confidence interval for all sf size
    stats = calculate_confidence_interval(df, 'current_sf_len', 'reward')

    x = stats['current_sf_len']
    y = stats['mean']

    axs[0, 0].plot(x, y, 'b-o', markersize=data_marker_size)
    axs[0, 0].fill_between(x, stats['ci95_hi'],
                           stats['ci95_lo'], color='b', alpha=.1)

    # Second plot: Power vs. slotframe size
    axs[0, 1].set_title('Network avg. power vs. SF size',
                        fontsize=title_font_size, fontweight=title_fontweight)
    axs[0, 1].set_xlabel('SF size', fontsize=x_axis_font_size,
                         fontstyle=axis_labels_fontstyle)
    axs[0, 1].set_ylabel(
        'Power [mW]', fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)
    axs[0, 1].tick_params(axis='both', which='major',
                          labelsize=ticks_font_size)
    # Confidence interval for all sf size
    stats = calculate_confidence_interval(df, 'current_sf_len', 'power_avg')

    x = stats['current_sf_len']
    y = stats['mean']

    axs[0, 1].plot(x, y, 'b-o', markersize=data_marker_size)
    axs[0, 1].fill_between(x, stats['ci95_hi'],
                           stats['ci95_lo'], color='b', alpha=.1)

    # Third plot: Delay vs. slotframe size
    axs[1, 0].set_title('Network avg. delay vs. SF size',
                        fontsize=title_font_size, fontweight=title_fontweight)
    axs[1, 0].set_xlabel('SF size', fontsize=x_axis_font_size,
                         fontstyle=axis_labels_fontstyle)
    axs[1, 0].set_ylabel(
        'Delay [ms]', fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)
    axs[1, 0].tick_params(axis='both', which='major',
                          labelsize=ticks_font_size)
    # Confidence interval for all sf size
    stats = calculate_confidence_interval(df, 'current_sf_len', 'delay_avg')

    x = stats['current_sf_len']
    y = stats['mean']

    axs[1, 0].plot(x, y, 'b-o', markersize=data_marker_size)
    axs[1, 0].fill_between(x, stats['ci95_hi'],
                           stats['ci95_lo'], color='b', alpha=.1)

    # Fourth plot: PDR vs. slotframe size
    axs[1, 1].set_title('Network avg. PDR vs. SF size',
                        fontsize=title_font_size, fontweight=title_fontweight)
    axs[1, 1].set_xlabel('SF size', fontsize=x_axis_font_size,
                         fontstyle=axis_labels_fontstyle)
    axs[1, 1].set_ylabel(
        'PDR', fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)
    axs[1, 1].tick_params(axis='both', which='major',
                          labelsize=ticks_font_size)
    # Confidence interval for all sf size
    stats = calculate_confidence_interval(df, 'current_sf_len', 'pdr_mean')

    x = stats['current_sf_len']
    y = stats['mean']

    axs[1, 1].plot(x, y, 'b-o', markersize=data_marker_size)
    axs[1, 1].fill_between(x, stats['ci95_hi'],
                           stats['ci95_lo'], color='b', alpha=.1)
    axs[1, 1].set_yticks(np.arange(0.8, 1.05, 0.05))

    # Save plot

    pl.savefig(name+'_sf_size.pdf'.format(
        alpha_weight, beta_weight, delta_weight, last_ts), bbox_inches='tight')
    pl.close()

#######################################################
# Run the application


def run_analysis(Database, name):
    # Load observations
    data = Database.find(OBSERVATIONS, {})

    # Expand the cursor and construct the DataFrame
    df = pd.DataFrame(data)

    # Plots in 4 axis
    plot(df, name)

    # Plot chars against the SF size
    plot_against_sf_size(df, name)

    # Fit curves for power, delay, PDR.
    # plot_fit_curves(df)