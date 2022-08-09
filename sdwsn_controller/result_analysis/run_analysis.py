#!/usr/bin/env python3
import re
from numpy import average
import pandas as pd
import numpy as np
import matplotlib.pyplot as pl
import math
from numpy import arange
from scipy.optimize import curve_fit
from sdwsn_controller.database.database import OBSERVATIONS
from stable_baselines3.common.results_plotter import load_results, ts2xy


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
def plot(df, name, path):
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

    reward = df.copy(deep=True)
    values = reward['reward'].astype(float)
    episode_reward = values.sum()

    fig, axs = pl.subplots(2, 2, layout='constrained')
    alpha_weight = df['alpha'].iloc[0]
    beta_weight = df['beta'].iloc[0]
    delta_weight = df['delta'].iloc[0]
    last_ts = df['last_ts_in_schedule'].iloc[0]
    fig.suptitle(r'$\alpha={},\beta={},\delta={},last~ts={}, reward={}$'.format(
        alpha_weight, beta_weight, delta_weight, last_ts, episode_reward), fontsize=title_font_size)
    # $\alpha=0.8,\beta=0.1,\delta=0.1$
    # First char is the reward and slotframe size over time
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

    pl.savefig(path+name+'.pdf'.format(
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


def plot_against_sf_size(df, name, path):
    title_font_size = 8
    x_axis_font_size = 8
    y_axis_font_size = 8
    ticks_font_size = 7
    data_marker_size = 1.5
    legend_font_size = 6
    title_fontweight = 'bold'
    axis_labels_fontstyle = 'italic'
    # Drop first row
    reward = df.copy(deep=True)
    values = reward['reward'].astype(float)
    episode_reward = values.sum()

    fig, axs = pl.subplots(2, 2, layout='constrained')
    alpha_weight = df['alpha'].iloc[0]
    beta_weight = df['beta'].iloc[0]
    delta_weight = df['delta'].iloc[0]
    last_ts = df['last_ts_in_schedule'].iloc[0]
    fig.suptitle(r'$\alpha={},\beta={},\delta={},last~ts={}, reward={}$'.format(
        alpha_weight, beta_weight, delta_weight, last_ts, episode_reward), fontsize=title_font_size)
    # $\alpha=0.8,\beta=0.1,\delta=0.1$
    # First plot is the reward vs. slotframe size
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
        'power_normalized', fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)
    axs[0, 1].tick_params(axis='both', which='major',
                          labelsize=ticks_font_size)
    # Confidence interval for all sf size
    stats = calculate_confidence_interval(df, 'current_sf_len', 'power_normalized')

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
        'Delay normalized', fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)
    axs[1, 0].tick_params(axis='both', which='major',
                          labelsize=ticks_font_size)
    # Confidence interval for all sf size
    stats = calculate_confidence_interval(df, 'current_sf_len', 'delay_normalized')

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

    pl.savefig(path+name+'_sf_size.pdf'.format(
        alpha_weight, beta_weight, delta_weight, last_ts), bbox_inches='tight')
    pl.close()
#######################################################


def plot_training_progress(log_dir, title="learning_curve"):

    title_font_size = 8
    x_axis_font_size = 8
    y_axis_font_size = 8
    ticks_font_size = 7
    data_marker_size = 1.5
    legend_font_size = 6
    title_fontweight = 'bold'
    axis_labels_fontstyle = 'italic'

    fig, axs = pl.subplots(layout='constrained')

    x, y = ts2xy(load_results(log_dir), 'timesteps')

    # Truncate x
    x = x[len(x) - len(y):]

    axs.set_title('Reward vs. timesteps',
                  fontsize=title_font_size, fontweight=title_fontweight)
    axs.set_xlabel('Timesteps', fontsize=x_axis_font_size,
                   fontstyle=axis_labels_fontstyle)
    axs.set_ylabel('Reward', fontsize=y_axis_font_size,
                   fontstyle=axis_labels_fontstyle)
    axs.tick_params(axis='both', which='major',
                    labelsize=ticks_font_size)

    axs.plot(x, y, 'b-o', markersize=data_marker_size)

    pl.savefig(title+'.pdf', bbox_inches='tight')
    pl.close()
#######################################################


def plot_episode_reward(df, title, path):

    title_font_size = 8
    x_axis_font_size = 8
    y_axis_font_size = 8
    ticks_font_size = 7
    data_marker_size = 1.5
    legend_font_size = 6
    title_fontweight = 'bold'
    axis_labels_fontstyle = 'italic'

    fig, (ax1, ax2) = pl.subplots(1, 2, layout='constrained')

    ax1.set_title('Reward vs. timesteps',
                  fontsize=title_font_size, fontweight=title_fontweight)
    ax1.set_xlabel('Timesteps', fontsize=x_axis_font_size,
                   fontstyle=axis_labels_fontstyle)
    ax1.set_ylabel('Reward', fontsize=y_axis_font_size,
                   fontstyle=axis_labels_fontstyle)
    ax1.tick_params(axis='both', which='major',
                    labelsize=ticks_font_size)
    x = range(len(df['timestamp']))
    y = df['reward'].astype(float)

    ax1.plot(x, y, 'b-o', markersize=data_marker_size)

    # Cumulative reward
    y = y.cumsum()

    ax2.set_title('Cumulative Reward vs. timesteps',
                  fontsize=title_font_size, fontweight=title_fontweight)
    ax2.set_xlabel('Timesteps', fontsize=x_axis_font_size,
                   fontstyle=axis_labels_fontstyle)
    ax2.set_ylabel('Reward', fontsize=y_axis_font_size,
                   fontstyle=axis_labels_fontstyle)
    ax2.tick_params(axis='both', which='major',
                    labelsize=ticks_font_size)

    ax2.plot(x, y, 'b-o', markersize=data_marker_size)

    pl.savefig(path+title+'.pdf', bbox_inches='tight')
    pl.close()
#######################################################


def plot_fit_curves(df, title, path):
    """ 
    We try to fit the curves for power, delay and
    PDR.
    """
    title_font_size = 8
    x_axis_font_size = 8
    y_axis_font_size = 8
    ticks_font_size = 7
    data_marker_size = 1.5
    legend_font_size = 6
    title_fontweight = 'bold'
    axis_labels_fontstyle = 'italic'

    fig, (ax1, ax2, ax3) = pl.subplots(3, layout='constrained')

    # Second plot: Power vs. slotframe size
    ax1.set_title('Network avg. power vs. SF size',
                  fontsize=title_font_size, fontweight=title_fontweight)
    ax1.set_xlabel('SF size', fontsize=x_axis_font_size,
                   fontstyle=axis_labels_fontstyle)
    ax1.set_ylabel(
        'Power', fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)
    ax1.tick_params(axis='both', which='major',
                    labelsize=ticks_font_size)
    # Confidence interval for all sf size
    stats = calculate_confidence_interval(
        df, 'current_sf_len', 'power_normalized')

    x = stats['current_sf_len']
    y = stats['mean']

    ax1.scatter(x, y, s=15)
    ax1.fill_between(x, stats['ci95_hi'],
                     stats['ci95_lo'], color='b', alpha=.1)

    x = x.to_numpy()
    y = y.to_numpy()

    trend = np.polyfit(x, y, 4)
    power_trendpoly = np.poly1d(trend)

    # ax1.text(25, 0.89, r'$y=x^2*%.2E+x*%.2E+%.2E$' % (trend[0], trend[1], trend[2]), style='italic',
    #          bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 3}, fontsize=5)

    # ax1.text(25, 0.89, 'colored text in axes coords',
    #          verticalalignment='bottom', horizontalalignment='right',
    #          color='black', fontsize=5)

    ax1.plot(x, power_trendpoly(x))

    print("power fitted curve polynomial coefficients")
    print(trend)

    # Third plot: Delay vs. slotframe size
    ax2.set_title('Network avg. delay vs. SF size',
                  fontsize=title_font_size, fontweight=title_fontweight)
    ax2.set_xlabel('SF size', fontsize=x_axis_font_size,
                   fontstyle=axis_labels_fontstyle)
    ax2.set_ylabel(
        'Delay', fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)
    ax2.tick_params(axis='both', which='major',
                    labelsize=ticks_font_size)
    # Confidence interval for all sf size
    stats = calculate_confidence_interval(
        df, 'current_sf_len', 'delay_normalized')

    x = stats['current_sf_len']
    y = stats['mean']

    ax2.scatter(x, y, s=15)
    ax2.fill_between(x, stats['ci95_hi'],
                     stats['ci95_lo'], color='b', alpha=.1)

    x = x.to_numpy()
    y = y.to_numpy()

    trend = np.polyfit(x, y, 3)
    delay_trendpoly = np.poly1d(trend)

    ax2.text(15, 0.03, r'$y=x^3*%.2E+x^2*%.2E+x*%.2E+%.2E$' % (trend[0], trend[1], trend[2], trend[3]), style='italic',
             bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 3}, fontsize=5)

    ax2.plot(x, delay_trendpoly(x))

    print("delay fitted curve polynomial coefficients")
    print(trend)

    # Fourth plot: PDR vs. slotframe size
    ax3.set_title('Network avg. PDR vs. SF size',
                  fontsize=title_font_size, fontweight=title_fontweight)
    ax3.set_xlabel('SF size', fontsize=x_axis_font_size,
                   fontstyle=axis_labels_fontstyle)
    ax3.set_ylabel(
        'PDR', fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)
    ax3.tick_params(axis='both', which='major',
                    labelsize=ticks_font_size)
    # Confidence interval for all sf size
    stats = calculate_confidence_interval(df, 'current_sf_len', 'pdr_mean')

    x = stats['current_sf_len']
    y = stats['mean']

    ax3.scatter(x, y, s=15)
    ax3.fill_between(x, stats['ci95_hi'],
                     stats['ci95_lo'], color='b', alpha=.1)

    x = x.to_numpy()
    y = y.to_numpy()

    trend = np.polyfit(x, y, 1)
    pdr_trendpoly = np.poly1d(trend)

    ax3.text(25, 0.6, r'$y=x*%.2E+%.2E$' % (trend[0], trend[1]), style='italic',
             bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 3}, fontsize=5)

    ax3.plot(x, pdr_trendpoly(x))

    ax3.set_ylim([0, 1])

    print("pdr fitted curve polynomial coefficients")
    print(trend)

    # # First plot: Reward vs. Slotframe size using the previous regressions
    # alpha_weight = df['alpha'].iloc[0]
    # beta_weight = df['beta'].iloc[0]
    # delta_weight = df['delta'].iloc[0]

    # axs[0, 0].set_title('Reward vs SF size',
    #                     fontsize=title_font_size, fontweight=title_fontweight)
    # axs[0, 0].set_xlabel('SF size', fontsize=x_axis_font_size,
    #                      fontstyle=axis_labels_fontstyle)
    # axs[0, 0].set_ylabel('Reward', fontsize=y_axis_font_size,
    #                      fontstyle=axis_labels_fontstyle)
    # axs[0, 0].tick_params(axis='both', which='major',
    #                       labelsize=ticks_font_size)
    # # Confidence interval for all sf size
    # stats = calculate_confidence_interval(df, 'current_sf_len', 'reward')

    # x = stats['current_sf_len']
    # y = stats['mean']

    # axs[0, 0].scatter(x, y)
    # axs[0, 0].fill_between(x, stats['ci95_hi'],
    #                        stats['ci95_lo'], color='b', alpha=.1)

    # x = x.to_numpy()
    # y = y.to_numpy()

    # y = -1*(alpha_weight*power_trendpoly(x)+beta_weight *
    #         delay_trendpoly(x)-delta_weight*pdr_trendpoly(x))

    # print("reward vector")
    # print(y)

    # axs[0, 0].plot(x, y)

    pl.savefig(path+title+'.pdf', bbox_inches='tight')
    pl.savefig(path+title+'.png', bbox_inches='tight', dpi=400)
    pl.close()

#######################################################
# Run the application


def run_analysis(Database, name, path, plot_sf_size: bool = False):
    db = Database.find_one(OBSERVATIONS, {})
    if db is None:
        print("Exiting analysis collection doesn't exist")
        return None
    # Load observations
    data = Database.find(OBSERVATIONS, {})

    # Expand the cursor and construct the DataFrame
    df = pd.DataFrame(data)

    # Plots in 4 axis
    plot(df, name, path)

    # Plot chars against the SF size
    if plot_sf_size:
        plot_against_sf_size(df, name, path)

    # Plot cumulative reward
    plot_episode_reward(df, name+"_reward", path)

    # Fit curves for power, delay, PDR.
    # print("df before fitted curves")
    # print(df.to_string())
    # plot_fit_curves(df, name+"_fitted_curves", path)
