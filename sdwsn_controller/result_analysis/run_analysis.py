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
from matplotlib.ticker import FuncFormatter


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
    stats = calculate_confidence_interval(
        df, 'current_sf_len', 'power_normalized')

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
    stats = calculate_confidence_interval(
        df, 'current_sf_len', 'delay_normalized')

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


def plot_training_progress(df, title, path):

    title_font_size = 8
    x_axis_font_size = 14
    y_axis_font_size = 14
    ticks_font_size = 12
    data_marker_size = 3.5
    legend_font_size = 12
    title_fontweight = 'bold'
    axis_labels_fontstyle = 'normal'

    def millions(x, pos):
        'The two args are the value and tick position'
        return '%1.0fk' % (x*1e-3)

    formatter = FuncFormatter(millions)

    fig, axs = pl.subplots(layout='constrained')

    x1 = df['Step1']
    y1 = df['Value1']
    x2 = df['Step2']
    y2 = df['Value2']
    x3 = df['Step3']
    y3 = df['Value3']

    l1, = axs.plot(x1, y1, 'g-o', markersize=data_marker_size)

    axs.set_ylabel('Average accumulative reward', fontsize=y_axis_font_size,
                   fontstyle=axis_labels_fontstyle)

    axs.set_xlabel('Timesteps', fontsize=x_axis_font_size,
                   fontstyle=axis_labels_fontstyle)

    axs.tick_params(axis='both', which='major',
                    labelsize=ticks_font_size)
    axs.tick_params(axis='both', which='major',
                    labelsize=ticks_font_size)

    l2, = axs.plot(x2, y2, 'b-*', markersize=data_marker_size)
    l3, = axs.plot(x3, y3, 'r-s', markersize=data_marker_size)

    axs.legend([l1, l2, l3], ['DQN',
               'PPO', 'A2C'], fontsize=legend_font_size)

    axs.minorticks_on()

    axs.grid(True, 'major', 'both', linestyle='--',
             color='0.75', linewidth=0.6)
    axs.grid(True, 'minor', 'both', linestyle=':',
             color='0.85', linewidth=0.5)

    axs.xaxis.set_major_formatter(formatter)

    pl.savefig(path+title+'.pdf', bbox_inches='tight')
    pl.savefig(path+title+'.png', bbox_inches='tight', dpi=400)
    pl.close()
#######################################################


def plot_results(df, title, path, x, y1, y1_name, y1_legend, y2, y2_name, y2_legend, ci=False, y1_limit=None, label_loc=None):
    title_font_size = 8
    x_axis_font_size = 14
    y_axis_font_size = 14
    ticks_font_size = 12
    data_marker_size = 3.5
    legend_font_size = 12
    annotate_font_size = 9
    title_fontweight = 'bold'
    axis_labels_fontstyle = 'normal'

    fig, ax = pl.subplots()
    fig.subplots_adjust(right=0.85)

    ax.tick_params(axis='both', which='major',
                   labelsize=ticks_font_size)
    ax.tick_params(axis='both', which='major',
                   labelsize=ticks_font_size)

    ax.minorticks_on()

    # twin1 = ax.twinx()
    twin2 = ax.twinx()

    twin2.tick_params(axis='both', which='major',
                      labelsize=ticks_font_size)
    twin2.tick_params(axis='both', which='major',
                      labelsize=ticks_font_size)

    twin2.minorticks_on()

    # Offset the right spine of twin2.  The ticks and label have already been
    # placed on the right by twinx above.
    # twin2.spines.right.set_position(("axes", 1.2))
    # Confidence interval
    if ci:
        stats = calculate_confidence_interval(
            df, x, y1)

        x_stats = stats[x]
        y_stats = stats['mean']
        ax.fill_between(x_stats, stats['ci95_hi'],
                        stats['ci95_lo'], color='b', alpha=.1)
    else:
        x_stats = df[x]
        y_stats = df[y1]

    if y1_limit is not None:
        ax.set_ylim(y1_limit)

    l1, = ax.plot(x_stats, y_stats, "b-*",
                  label=y1_legend, markersize=data_marker_size)

    # Slotframe size
    if ci:
        stats = calculate_confidence_interval(
            df, x, y2)

        x_stats = stats[x]
        y_stats = stats['mean']
        twin2.fill_between(x_stats, stats['ci95_hi'],
                           stats['ci95_lo'], color='g', alpha=.1)
    else:
        x_stats = df[x]
        y_stats = df[y2]

    l2, = twin2.plot(x_stats, y_stats, "g-s",
                     label=y2_name, markersize=data_marker_size)

    twin2.set_ylabel(y2_name, fontsize=y_axis_font_size,
                     fontstyle=axis_labels_fontstyle)

    if label_loc is None:
        label_loc = 'best'

    ax.legend([l1, l2], [y1_legend,
                         y2_legend], loc=label_loc, fontsize=legend_font_size, facecolor='white', framealpha=1)

    ax.grid(True, 'major', 'both', linestyle='--',
            color='0.75', linewidth=0.6)
    ax.grid(True, 'minor', 'both', linestyle=':',
            color='0.85', linewidth=0.5)

    # p1, = ax.plot(x, y1, "b--*",
    #               label=name, markersize=data_marker_size)
    # p2, = twin1.plot(x, y2, "r-o", label="Reward",
    #                  markersize=data_marker_size)
    # p3, = twin2.plot(
    #     x, y2, "g:v", label="Slotframe size", markersize=data_marker_size)

    ax.set_xlabel('Iteration', fontsize=x_axis_font_size,
                  fontstyle=axis_labels_fontstyle)
    ax.set_ylabel(
        y1_name, fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)
    # twin1.set_ylabel(
    #     "Reward", fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)
    # twin2.set_ylabel(
    #     "Slotframe size ("+r'$\tau$'+')', fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)

    # # ax.yaxis.label.set_color(p1.get_color())
    # if y1_range is not None:
    #     ax.set_ylim(y1_range)
    # # twin1.yaxis.label.set_color(p2.get_color())
    # # twin1.set_ylim([0.65, 1.2])
    # # twin2.yaxis.label.set_color(p3.get_color())

    # tkw = dict(size=4, width=1.5)
    # # ax.tick_params(axis='y', colors=p1.get_color(), **tkw)
    # # twin1.tick_params(axis='y', colors=p2.get_color(), **tkw)
    # # twin2.tick_params(axis='y', colors=p3.get_color(), **tkw)
    # ax.tick_params(axis='x', **tkw)

    # # y min and max
    # ymin, ymax = ax.get_ylim()
    # ax.vlines(x=[40, 80, 120], ymin=ymin, ymax=ymax,
    #           colors='darkgrey', ls='--', lw=1)
    # # ax.vlines(x=[0, 17], ymin=ymin, ymax=ymax, colors='r')

    # # Set user requirements region
    # ax.text(-5, text_loc[0], r'$\alpha=0.4, \beta=0.3, \gamma=0.3$', style='italic',
    #         bbox={'facecolor': 'red', 'alpha': 0.6, 'pad': 3}, fontsize=legend_font_size)
    # ax.text(40, text_loc[1], r'$\alpha=0.1, \beta=0.8, \gamma=0.1$', style='italic', bbox={
    #         'facecolor': 'red', 'alpha': 0.6, 'pad': 3}, fontsize=legend_font_size)
    # ax.text(80, text_loc[2], r'$\alpha=0.8, \beta=0.1, \gamma=0.1$', style='italic', bbox={
    #         'facecolor': 'red', 'alpha': 0.6, 'pad': 3}, fontsize=legend_font_size)
    # ax.text(123, text_loc[3], r'$\alpha=0.1, \beta=0.1, \gamma=0.8$', style='italic', bbox={
    #         'facecolor': 'red', 'alpha': 0.6, 'pad': 2}, fontsize=legend_font_size)

    # if label_loc is None:
    #     label_loc = 'best'

    # if annotate is True:
    #     circle_rad = 16  # This is the radius, in points
    #     ax.plot(83.8, 1.117, 'o',
    #             ms=circle_rad * 2, mec='b', mfc='none', mew=1)
    #     # ax.annotate('Change of user \nrequirements', xy=(40, 1.08), xycoords='data',
    #     #             xytext=(40, 1.08),
    #     #             textcoords='offset points',
    #     #             color='b', size='large',
    #     #             arrowprops=dict(
    #     #                 arrowstyle='simple,tail_width=0.3,head_width=0.8,head_length=0.8',
    #     #                 facecolor='b', shrinkB=circle_rad * 1.2)
    #     #             )
    #     ax.annotate('Change in UR.', xy=(83.8, 1.117),  xycoords='data',
    #                 xytext=(45, 1.095), textcoords='data',
    #                 fontsize=annotate_font_size,
    #                 arrowprops=dict(
    #         arrowstyle='simple,tail_width=0.3,head_width=0.8,head_length=0.8',
    #         facecolor='b', shrinkB=circle_rad * 1.2)
    #     )

    # ax.legend(handles=[p1, p3], loc=label_loc,
    #           fontsize=legend_font_size, facecolor='white', framealpha=1)

    pl.savefig(path+title+'.pdf', bbox_inches='tight')
    pl.savefig(path+title+'.png', bbox_inches='tight', dpi=400)
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
    x_axis_font_size = 14
    y_axis_font_size = 14
    ticks_font_size = 12
    equation_font_size = 7.79
    data_marker_size = 1.5
    legend_font_size = 6
    title_fontweight = 'bold'
    axis_labels_fontstyle = 'italic'

    fig, (ax1, ax2, ax3) = pl.subplots(3, layout='constrained')

    # Second plot: Power vs. slotframe size
    # ax1.set_title('Network avg. power vs. SF size',
    #               fontsize=title_font_size, fontweight=title_fontweight)
    ax1.set_xlabel(r'$\tau$', fontsize=x_axis_font_size,
                   fontstyle=axis_labels_fontstyle)
    ax1.set_ylabel(
        r'$\hat{P_N}$', fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)
    ax1.tick_params(axis='both', which='major',
                    labelsize=ticks_font_size)

    ax1.minorticks_on()
    ax1.set_yticks(np.arange(0.85, 0.9, 0.01))
    ax1.grid(True, 'major', 'both', linestyle='--',
             color='0.75', linewidth=0.6)
    ax1.grid(True, 'minor', 'both', linestyle=':',
             color='0.85', linewidth=0.5)
    # ax1.set_yticks(np.arange(0, max(y), 2))
    # Confidence interval for all sf size
    stats = calculate_confidence_interval(
        df, 'current_sf_len', 'power_unbiased')

    x = stats['current_sf_len']
    y = stats['mean']

    ax1.scatter(x, y, s=15)
    ax1.fill_between(x, stats['ci95_hi'],
                     stats['ci95_lo'], color='b', alpha=.1)

    x = x.to_numpy()
    y = y.to_numpy()

    trend = np.polyfit(x, y, 4)
    power_trendpoly = np.poly1d(trend)

    ax1.text(8, 0.89, r'$\hat{P_N}(\tau)=\tau^4*(%.2E)+\tau^3*(%.2E)+\tau^2*(%.2E)+\tau*(%.2E)+(%.2E)$' % (trend[0], trend[1], trend[2], trend[3], trend[4]), style='italic',
             bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 3}, fontsize=equation_font_size)

    # ax1.text(25, 0.89, 'colored text in axes coords',
    #          verticalalignment='bottom', horizontalalignment='right',
    #          color='black', fontsize=5)

    ax1.plot(x, power_trendpoly(x))

    print("power fitted curve polynomial coefficients")
    print(trend)

    # Third plot: Delay vs. slotframe size
    # ax2.set_title('Network avg. delay vs. SF size',
    #               fontsize=title_font_size, fontweight=title_fontweight)
    ax2.set_xlabel(r'$\tau$', fontsize=x_axis_font_size,
                   fontstyle=axis_labels_fontstyle)
    ax2.set_ylabel(
        r'$\hat{D_N}$', fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)
    ax2.tick_params(axis='both', which='major',
                    labelsize=ticks_font_size)

    ax2.set_yticks(np.arange(0.01, 0.9, 0.02))

    # Turn on the minor TICKS, which are required for the minor GRID
    ax2.minorticks_on()
    ax2.grid(True, 'major', 'both', linestyle='--',
             color='0.75', linewidth=0.6)
    ax2.grid(True, 'minor', 'both', linestyle=':',
             color='0.85', linewidth=0.5)
    # Confidence interval for all sf size
    stats = calculate_confidence_interval(
        df, 'current_sf_len', 'delay_unbiased')

    x = stats['current_sf_len']
    y = stats['mean']

    ax2.scatter(x, y, s=15)
    ax2.fill_between(x, stats['ci95_hi'],
                     stats['ci95_lo'], color='b', alpha=.1)

    x = x.to_numpy()
    y = y.to_numpy()

    trend = np.polyfit(x, y, 3)
    delay_trendpoly = np.poly1d(trend)

    ax2.text(8, 0.045, r'$\hat{D_N}(\tau)=\tau^3*(%.2E)+\tau^2*(%.2E)+\tau*(%.2E)+(%.2E)$' % (trend[0], trend[1], trend[2], trend[3]), style='italic',
             bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 3}, fontsize=equation_font_size)

    ax2.plot(x, delay_trendpoly(x))

    print("delay fitted curve polynomial coefficients")
    print(trend)

    # Fourth plot: PDR vs. slotframe size
    # ax3.set_title('Network avg. PDR vs. SF size',
    #               fontsize=title_font_size, fontweight=title_fontweight)
    ax3.set_xlabel(r'$\tau$', fontsize=x_axis_font_size,
                   fontstyle=axis_labels_fontstyle)
    ax3.set_ylabel(
        r'$\hat{R_N}$', fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)
    ax3.tick_params(axis='both', which='major',
                    labelsize=ticks_font_size)

    ax3.set_yticks(np.arange(0.65, 1, 0.1))
    # Turn on the minor TICKS, which are required for the minor GRID
    ax3.minorticks_on()
    ax3.grid(True, 'major', 'both', linestyle='--',
             color='0.75', linewidth=0.6)
    ax3.grid(True, 'minor', 'both', linestyle=':',
             color='0.85', linewidth=0.5)
    # Confidence interval for all sf size
    stats = calculate_confidence_interval(df, 'current_sf_len', 'pdr_unbiased')

    x = stats['current_sf_len']
    y = stats['mean']

    ax3.scatter(x, y, s=15)
    ax3.fill_between(x, stats['ci95_hi'],
                     stats['ci95_lo'], color='b', alpha=.1)

    x = x.to_numpy()
    y = y.to_numpy()

    trend = np.polyfit(x, y, 1)
    pdr_trendpoly = np.poly1d(trend)

    ax3.text(25, 0.7, r'$\hat{R_N}(\tau)=\tau*(%.2E)+(%.2E)$' % (trend[0], trend[1]), style='italic',
             bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 3}, fontsize=equation_font_size)

    ax3.plot(x, pdr_trendpoly(x))

    ax3.set_ylim([0.65, 1])

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
