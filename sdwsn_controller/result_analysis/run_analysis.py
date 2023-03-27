#!/usr/bin/python3
#
# Copyright (C) 2022  Fernando Jurado-Lasso <ffjla@dtu.dk>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pandas as pd
import numpy as np
import matplotlib.pyplot as pl
import math
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
    ax.plot(range(len(df['timestamp'])), df['delay_mean'], 'b-o')
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
    ax.plot(range(len(df['timestamp'])), df['power_mean'], 'b-o')
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
    fig.suptitle(r'$\alpha={},\beta={},\delta={},last~ts={}, reward={}$'.
                 format(alpha_weight, beta_weight, delta_weight,
                        last_ts, episode_reward),
                 fontsize=title_font_size)
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
        'Power [mW]', fontsize=y_axis_font_size,
        fontstyle=axis_labels_fontstyle)
    axs[0, 1].tick_params(axis='both', which='major',
                          labelsize=ticks_font_size)
    axs2 = axs[0, 1].twinx()
    axs2.tick_params(axis='both', which='major', labelsize=ticks_font_size)
    axs2.set_ylabel('Slotframe size', fontsize=y_axis_font_size,
                    fontstyle=axis_labels_fontstyle)
    l1, = axs[0, 1].plot(range(len(df['timestamp'])), df['power_mean'],
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
        'delay [ms]', fontsize=y_axis_font_size,
        fontstyle=axis_labels_fontstyle)
    axs[1, 0].tick_params(axis='both', which='major',
                          labelsize=ticks_font_size)
    axs2 = axs[1, 0].twinx()
    axs2.tick_params(axis='both', which='major', labelsize=ticks_font_size)
    axs2.set_ylabel('Slotframe size', fontsize=y_axis_font_size,
                    fontstyle=axis_labels_fontstyle)
    l1, = axs[1, 0].plot(range(len(df['timestamp'])), df['delay_mean'],
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

    pl.savefig(path+name+'.pdf', bbox_inches='tight')
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


def plot_against_sf_size(df, title, path):
    plot_against_sf_df = df.copy()
    title_font_size = 8
    x_axis_font_size = 8
    y_axis_font_size = 8
    ticks_font_size = 7
    data_marker_size = 1.5
    title_fontweight = 'bold'
    axis_labels_fontstyle = 'italic'
    # Drop first row
    reward = df.copy(deep=True)
    values = reward['reward'].astype(float)
    episode_reward = values.sum()

    fig, axs = pl.subplots(2, 2, layout='constrained')
    alpha_weight = plot_against_sf_df['alpha'].iloc[0]
    beta_weight = plot_against_sf_df['beta'].iloc[0]
    delta_weight = plot_against_sf_df['delta'].iloc[0]
    last_ts = plot_against_sf_df['last_ts_in_schedule'].iloc[0]
    fig.suptitle(r'$\alpha={},\beta={},\delta={},last~ts={}, reward={}$'
                 .format(alpha_weight, beta_weight, delta_weight,
                         last_ts, episode_reward),
                 fontsize=title_font_size)
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
    stats = calculate_confidence_interval(
        plot_against_sf_df, 'current_sf_len', 'reward')

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
        'power_normalized', fontsize=y_axis_font_size,
        fontstyle=axis_labels_fontstyle)
    axs[0, 1].tick_params(axis='both', which='major',
                          labelsize=ticks_font_size)
    # Confidence interval for all sf size
    stats = calculate_confidence_interval(
        plot_against_sf_df, 'current_sf_len', 'power_normalized')

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
        'Delay normalized', fontsize=y_axis_font_size,
        fontstyle=axis_labels_fontstyle)
    axs[1, 0].tick_params(axis='both', which='major',
                          labelsize=ticks_font_size)
    # Confidence interval for all sf size
    stats = calculate_confidence_interval(
        plot_against_sf_df, 'current_sf_len', 'delay_normalized')

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
    stats = calculate_confidence_interval(
        plot_against_sf_df, 'current_sf_len', 'pdr_mean')

    x = stats['current_sf_len']
    y = stats['mean']

    axs[1, 1].plot(x, y, 'b-o', markersize=data_marker_size)
    axs[1, 1].fill_between(x, stats['ci95_hi'],
                           stats['ci95_lo'], color='b', alpha=.1)
    axs[1, 1].set_yticks(np.arange(0.8, 1.05, 0.05))

    # Save plot

    pl.savefig(path+title+'.pdf', bbox_inches='tight')
    pl.savefig(path+title+'.png', bbox_inches='tight', dpi=400)
    pl.close()
#######################################################


def plot_training_progress(df, title, path):

    x_axis_font_size = 14
    y_axis_font_size = 14
    ticks_font_size = 12
    data_marker_size = 3.5
    legend_font_size = 12
    axis_labels_fontstyle = 'normal'

    def millions(x, pos):
        'The two args are the value and tick position'
        return '%1.0fk' % (x*1e-3)

    formatter = FuncFormatter(millions)

    _, axs = pl.subplots(layout='constrained')

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


def plot_results(df, title, path, x, y1, y1_name, y1_legend, y2, y2_name,
                 y2_legend, text_loc, ci=False, y1_limit=None, label_loc=None):
    x_axis_font_size = 14
    y_axis_font_size = 14
    ticks_font_size = 12
    data_marker_size = 3.5
    legend_font_size = 12
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
                         y2_legend], loc=label_loc, fontsize=legend_font_size,
              facecolor='white', framealpha=1)

    ax.grid(True, 'major', 'both', linestyle='--',
            color='0.75', linewidth=0.6)
    ax.grid(True, 'minor', 'both', linestyle=':',
            color='0.85', linewidth=0.5)

    ax.set_xlabel('Iteration', fontsize=x_axis_font_size,
                  fontstyle=axis_labels_fontstyle)
    ax.set_ylabel(
        y1_name, fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)

    # y min and max
    ymin, ymax = ax.get_ylim()
    ax.vlines(x=[40, 80, 120], ymin=ymin, ymax=ymax,
              colors='red', ls='--', lw=1)

    ax.text(20, text_loc[0], r'$1$', style='italic',
            bbox={'facecolor': 'red', 'alpha': 0.6, 'pad': 3},
            fontsize=legend_font_size)
    ax.text(60, text_loc[1], r'$2$', style='italic', bbox={
            'facecolor': 'red', 'alpha': 0.6, 'pad': 3},
            fontsize=legend_font_size)
    ax.text(100, text_loc[2], r'$3$', style='italic', bbox={
            'facecolor': 'red', 'alpha': 0.6, 'pad': 3},
            fontsize=legend_font_size)
    ax.text(140, text_loc[3], r'$4$', style='italic', bbox={
            'facecolor': 'red', 'alpha': 0.6, 'pad': 2},
            fontsize=legend_font_size)

    pl.savefig(path+title+'.pdf', bbox_inches='tight')
    pl.savefig(path+title+'.png', bbox_inches='tight', dpi=400)
    pl.close()

#######################################################


def plot_results_bar_chart(df, title, path,
                           x, y1, y1_name,
                           orch_df,
                           y1_limit=None):
    y_axis_font_size = 17
    ticks_font_size = 12.8
    axis_labels_fontstyle = 'normal'

    fig, ax = pl.subplots()
    fig.subplots_adjust(right=0.85)

    ax.tick_params(axis='y', which='major',
                   labelsize=ticks_font_size+2)
    ax.tick_params(axis='x', which='major',
                   labelsize=ticks_font_size)

    ax.tick_params(axis='x', which='minor', bottom=False)

    ax.minorticks_on()

    stats = calculate_confidence_interval(
        df, x, y1)

    y_stats = stats['mean']

    if y1_limit is not None:
        ax.set_ylim(y1_limit)

    # Plot balanced user requirements first
    df = y_stats.iloc[10:35, ]
    balanced_mean = df.mean()
    balanced_std = df.std()
    balanced_error_plus = 1.96*balanced_std/math.sqrt(35-10)
    # Plot delay user requirements first
    df = y_stats.iloc[50:75, ]
    delay_mean = df.mean()
    delay_std = df.std()
    delay_error_plus = 1.96*delay_std/math.sqrt(75-50)
    # Plot power user requirements first
    df = y_stats.iloc[95:115, ]
    power_mean = df.mean()
    power_std = df.std()
    power_error_plus = 1.96*power_std/math.sqrt(115-95)
    # Plot reliability user requirements first
    df = y_stats.iloc[135:155, ]
    reliability_mean = df.mean()
    reliability_std = df.std()
    reliability_error_plus = 1.96*reliability_std/math.sqrt(155-135)

    x_axis = ['Balanced\n' +
              r'$\alpha=0.4,$'+'\n'+r'$\beta=0.3,$'+'\n'+r'$\gamma = 0.3$',
              'Delay\n' +
              r'$\alpha=0.1,$'+'\n'+r'$\beta=0.8,$'+'\n'+r'$\gamma = 0.1$',
              'Power\n' +
              r'$\alpha=0.8,$'+'\n'+r'$\beta=0.1,$'+'\n'+r'$\gamma = 0.1$',
              'Reliability\n' +
              r'$\alpha=0.1,$'+'\n'+r'$\beta=0.1,$'+'\n'+r'$\gamma = 0.8$',
              'Orchestra']

    ax.grid(True, 'major', 'both', linestyle='--',
            color='0.75', linewidth=0.6, zorder=0)
    ax.grid(True, 'minor', 'both', linestyle=':',
            color='0.85', linewidth=0.5, zorder=0)

    ax.set_ylabel(
        y1_name, fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)

    # Orchestra results
    orch_stats = calculate_confidence_interval(
        orch_df, x, y1)

    orchestra_mean = orch_stats['mean']
    orch_mean = orchestra_mean.mean()
    orch_std = orchestra_mean.std()
    orch_error_plus = 1.96*orch_std/math.sqrt(len(orchestra_mean))

    means = [balanced_mean, delay_mean,
             power_mean, reliability_mean, orch_mean]
    errors = [balanced_error_plus, delay_error_plus,
              power_error_plus, reliability_error_plus, orch_error_plus]

    bar_colors = ['C0', 'C0', 'C0', 'C0', 'C3']

    ax.bar(x_axis, means, yerr=errors, zorder=3,  color=bar_colors, alpha=0.95,
           edgecolor="black", linewidth=0.5)
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
    title_fontweight = 'bold'
    axis_labels_fontstyle = 'italic'

    _, (ax1, ax2) = pl.subplots(1, 2, layout='constrained')

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


def plot_fit_curves(df, title, path, x_axis, y_axis, x_axis_name, y_axis_name,
                    degree, txt_loc=None, y_axis_limit=None):
    """
    We try to fit the curves for power, delay and
    PDR.
    """
    plot_fit_df = df.copy()
    x_axis_font_size = 14
    y_axis_font_size = 14
    ticks_font_size = 12
    equation_font_size = 7.4
    axis_labels_fontstyle = 'normal'

    _, ax = pl.subplots(layout='constrained', figsize=(6.4, 2))
    # fig.subplots_adjust(right=0.85)

    ax.tick_params(axis='both', which='major',
                   labelsize=ticks_font_size)
    ax.tick_params(axis='both', which='major',
                   labelsize=ticks_font_size)

    ax.minorticks_on()

    # Confidence interval
    stats = calculate_confidence_interval(
        plot_fit_df, x_axis, y_axis)

    x_stats = stats[x_axis]
    y_stats = stats['mean']
    ax.fill_between(x_stats, stats['ci95_hi'],
                    stats['ci95_lo'], color='b', alpha=.1)

    if y_axis_limit is not None:
        ax.set_ylim(y_axis_limit)

    ax.scatter(x_stats, y_stats, s=15, zorder=3)

    x = x_stats.to_numpy()
    y = y_stats.to_numpy()

    trend = np.polyfit(x, y, degree)
    power_trendpoly = np.poly1d(trend)

    if degree == 4:
        txt = r'$\widetilde{P}(|C|)=|C|^4*(%.2E)+|C|^3*(%.2E)+|C|^2*(%.2E)+|C| *(%.2E)+(%.2E)$' % (
            trend[0], trend[1], trend[2], trend[3], trend[4])
    if degree == 3:
        txt = r'$|C|^3*(%.2E)+|C|^2*(%.2E)+|C|*(%.2E)+(%.2E)$' % (
            trend[0], trend[1], trend[2], trend[3])
    if degree == 1:
        txt = r'$\widetilde{R}(|C|)=|C|*(%.2E)+(%.2E)$' % (trend[0], trend[1])

    ax.plot(x, power_trendpoly(x), zorder=3)

    if txt_loc is not None:
        ax.text(txt_loc[0], txt_loc[1], txt, style='italic',
                bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 3},
                fontsize=equation_font_size)
    else:
        # print the trend vector
        print(f'{title} trend vector: {trend}')

    ax.grid(True, 'major', 'both', linestyle='--',
            color='0.75', linewidth=0.6, zorder=0)
    ax.grid(True, 'minor', 'both', linestyle=':',
            color='0.85', linewidth=0.5, zorder=0)

    ax.set_xlabel(x_axis_name, fontsize=x_axis_font_size,
                  fontstyle=axis_labels_fontstyle)
    ax.set_ylabel(
        y_axis_name, fontsize=y_axis_font_size, fontstyle=axis_labels_fontstyle)

    pl.savefig(path+title+'.pdf', bbox_inches='tight')
    pl.savefig(path+title+'.png', bbox_inches='tight', dpi=400)
    pl.close()

#######################################################
# Run the application


def run_analysis(name, path, plot_sf_size: bool = False):
    df = pd.read_csv(path+name+".csv")

    # Plots in 4 axis
    plot(df, name, path)

    # Plot chars against the SF size
    if plot_sf_size:
        plot_against_sf_size(df, name, path)

    # Plot cumulative reward
    plot_episode_reward(df, name+"_reward", path)
