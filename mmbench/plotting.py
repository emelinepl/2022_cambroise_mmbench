# -*- coding: utf-8 -*-
##########################################################################
# NSAp - Copyright (C) CEA, 2022
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Plotting utility functions.
"""

# Imports
from itertools import combinations
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.stats import ttest_1samp
from scipy.stats import ttest_ind as ttest


def plot_mat(key, mat, ax=None, figsize=(5, 2), dpi=300, fontsize=16,
             fontweight="bold", title=None, vmin=None, vmax=None):
    """ Display a mat array.

    Parameters
    ----------
    key: str
        the mat array identifier.
    mat: array (n, n)
        the mat array to display.
    ax: matplotlib.axes.Axes, default None
        the axes used to display the plot.
    figsize: (float, float), default (5, 2)
        width, height in inches.
    dpi: float, default 300
        the resolution of the figure in dots-per-inch.
    fontsize: int or str, default 16
        size in points or relative size, e.g., 'smaller', 'x-large'.
    fontweight: str, default 'bold'
        the font weight, e.g. 'normal', 'bold', 'heavy', 'light', 'ultrabold'
        or 'ultralight'.
    title: str, default None
        the title displayed on the figure.
    vmin: float, default None
        minimum value on y-axis of figures
    vmax: float, default None
        maximum value on y-axis of figures
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=figsize, dpi=dpi)
    ax.imshow(mat, aspect="auto", cmap="Reds", vmin=vmin, vmax=vmax)
    if title is None:
        plt.title(key, fontsize=fontsize * 1.5, pad=2, fontweight=fontweight)
    else:
        plt.title(title, fontsize=fontsize * 1.5, pad=2, fontweight=fontweight)


def plot_bar(key, rsa, ax=None, figsize=(5, 2), dpi=300, fontsize=16,
             fontsize_star=25, fontweight="bold", line_width=2.5,
             marker_size=.1, title=None, palette="Spectral", report_t=False,
             do_pairwise_stars=False, do_one_sample_stars=True, yname="model fit (r)"):
    """ Display results with bar plots.

    Parameters
    ----------
    key: str
        the analysis identifier.
    rsa: dict of dict
        the sampling data with the analysis identifiers as first key and
        experimental conditions as second key.
    ax: matplotlib.axes.Axes, default None
        the axes used to display the plot.
    figsize: (float, float), default (5, 2)
        width, height in inches.
    dpi: float, default 300
        the resolution of the figure in dots-per-inch.
    fontsize: int or str, default 16
        size in points or relative size, e.g., 'smaller', 'x-large'.
    fontsize_star: int or str, default 25
        size in points or relative size, e.g., 'smaller', 'x-large' used to
        display pairwise statistics.
    fontweight: str, default 'bold'
        the font weight, e.g. 'normal', 'bold', 'heavy', 'light', 'ultrabold'
        or 'ultralight'.
    line_width: int, default 2.5
        the bar plot line width.
    marker_size: int, default .1
        the sampling scatter plot marker size.
    title: str, default None
        the title displayed on the figure.
    palette: palette name, list, or dict
        colors to use for the different levels of the hue variable.
        Should be something that can be interpreted by color_palette(), or a
        dictionary mapping hue levels to matplotlib colors.
    report_t: bool, default False
        optionally, generate a report with pairwise statistics.
    do_pairwise_stars: bool, default False
        optionally, display pairwise statistics.
    do_one_sample_stars: bool, default True
        optionally, display sampling statistics.
    yname: str
        optionally, name of the metric on y-axis

    Returns
    -------
    pairwise_stat_df: pandas.DataFrame or None
        the generated pairwise statistics.
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=figsize, dpi=dpi)

    data = rsa[key]
    _data = {}
    for cond in list(data.keys()):
        _data.setdefault("model fit (r)", []).extend(data[cond])
        _data.setdefault("condition", []).extend([cond] * len(data[cond]))
    data_df = pd.DataFrame.from_dict(_data)

    sns.stripplot(data=data_df,
                  x="condition",
                  y="model fit (r)",
                  jitter=0.15,
                  alpha=1.0,
                  color="k",
                  size=marker_size)
    plot = sns.barplot(data=data_df,
                       x="condition",
                       y="model fit (r)",
                       errcolor="r",
                       alpha=0.3,
                       linewidth=line_width,
                       errwidth=line_width,
                       palette=palette)
    for patch in plot.containers[0]:
        fc = patch.get_edgecolor()
        patch.set_edgecolor(mcolors.to_rgba(fc, 1.))
    locs, labels = plt.yticks()
    new_y = locs
    new_y = np.linspace(locs[0], locs[-1], 6)
    plt.yticks(new_y, labels=[f"{yy:.2f}" for yy in new_y], fontsize=fontsize,
               fontweight=fontweight)
    plt.ylabel(yname, fontsize=fontsize, fontweight=fontweight)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    for axis in ["top", "bottom", "left", "right"]:
        ax.spines[axis].set_linewidth(line_width)
    xlabels = [item.get_text() for item in ax.get_xticklabels()]
    _xlabels = ["\n".join(item.split("_")[:-1]) for item in xlabels]
    ax.set_xticklabels(_xlabels, fontsize=fontsize, fontweight=fontweight)
    x_label = ax.axes.get_xaxis().get_label()
    x_label.set_visible(False)
    ylim = plt.ylim()
    plt.ylim(np.array(ylim) * (1, 1.1))
    if title is None:
        plt.title(key, fontsize=fontsize * 1.5, pad=2, fontweight=fontweight)
    else:
        plt.title(title, fontsize=fontsize * 1.5, pad=2, fontweight=fontweight)

    if do_one_sample_stars:
        one_sample_thresh = np.array((1, .05, .001, .0001))
        one_sample_stars = np.array(("n.s.", "*", "**", "***"))
        for idx, name in enumerate(xlabels):
            one_sample = ttest_1samp(data[name], 0)
            these_stars = one_sample_stars[
                max(np.nonzero(one_sample.pvalue < one_sample_thresh)[0])]
            _xlabels[idx] = f"{_xlabels[idx]}\n({these_stars})"
        ax.set_xticklabels(_xlabels, fontsize=fontsize, fontweight=fontweight)

    if report_t or do_pairwise_stars:
        size = len(xlabels)
        pairwise_t = np.zeros((size, size))
        pairwise_p = np.zeros((size, size))
        _data = dict()
        for idx1, name1 in enumerate(xlabels):
            for idx2, name2 in enumerate(xlabels):
                n_samples = len(data[name1])
                tval, pval = ttest(data[name1], data[name2])
                if pval > .001:
                    print(f"{key} {name1} >  {name2} | "
                          f"t({n_samples-1}) = {tval:.2f} p = {pval:.2f}")
                else:
                    print(f"{key} {name1} >  {name2} | "
                          f"t({n_samples-1}) = {tval:.2f} p < .001")
                pairwise_t[idx1, idx2] = tval
                pairwise_p[idx1, idx2] = pval
                _data.setdefault("pair", []).append(
                    f"qname-{key}_src-{name1.replace('_', '-')}_"
                    f"dest-{name2.replace('_', '-')}")
                _data.setdefault("tval", []).append(tval)
                _data.setdefault("pval", []).append(pval)
        pairwise_stat_df = pd.DataFrame.from_dict(_data)
    else:
        pairwise_stat_df = None

    if do_pairwise_stars:
        from statannotations.Annotator import Annotator
        pairwise_sample_thresh = np.array((1, .05, .001, .0001))
        pairwise_sample_stars = np.array(("n.s.", "*", "**", "***"))
        comps = list(combinations(range(len(xlabels)), 2))
        pairs, annotations = [], []
        for comp_idx, this_comp in enumerate(comps):
            sig_idx = max(np.nonzero(
                pairwise_p[this_comp[0], this_comp[1]] <
                pairwise_sample_thresh)[0])
            if sig_idx != 0:
                stars = pairwise_sample_stars[sig_idx]
                pairs.append([xlabels[this_comp[0]], xlabels[this_comp[1]]])
                annotations.append(stars)
        if len(pairs) > 0:
            annotator = Annotator(
                ax, pairs, data=data_df, x="condition", y="model fit (r)",
                order=xlabels)
            annotator.set_custom_annotations(annotations)
            annotator.annotate()

    return pairwise_stat_df


def plot_curve(x_data, mat, ax=None, figsize=(5, 2), dpi=300, fontsize=16,
               fontweight="bold", title=None):
    """ Display a list of curve.

    Parameters
    ----------
    x_data: list
        the abscissa of the graph.
    mat: array (n_curve, n_points)
        the matrix containing ordinates of each curve.
    ax: matplotlib.axes.Axes, default None
        the axes used to display the plot.
    figsize: (float, float), default (5, 2)
        width, height in inches.
    dpi: float, default 300
        the resolution of the figure in dots-per-inch.
    fontsize: int or str, default 16
        size in points or relative size, e.g., 'smaller', 'x-large'.
    fontweight: str, default 'bold'
        the font weight, e.g. 'normal', 'bold', 'heavy', 'light', 'ultrabold'
        or 'ultralight'.
    title: str, default None
        the title displayed on the figure.
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=figsize, dpi=dpi)
    for idx, elem in enumerate(mat):
        ax.plot(x_data, elem, label=f"to {idx+1}")
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    if title is None:
        plt.title(x_data, fontsize=fontsize * 1.5, pad=2,
                  fontweight=fontweight)
    else:
        plt.title(title, fontsize=fontsize * 1.5, pad=2, fontweight=fontweight)
