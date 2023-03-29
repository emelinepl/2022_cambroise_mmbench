# -*- coding: utf-8 -*-
##########################################################################
# NSAp - Copyright (C) CEA, 2022 - 2023
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Define the predicction workflows.
"""
# Imports
import os
import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
from sklearn import linear_model
from sklearn import metrics
from sklearn.model_selection import cross_val_score
from mmbench.color_utils import (
    print_title, print_subtitle, print_text, print_result,
    print_error)
from mmbench.plotting import plot_bar


def benchmark_pred_exp(dataset, datasetdir, outdir):
    """ Compare the learned latent space of different models using
    prediction analysis.

    Parameters
    ----------
    dataset: str
        the dataset name: euaims or hbn.
    datasetdir: str
        the path to the dataset associated data.
    outdir: str
        the destination folder.

    Notes
    -----
    - The samples are generated with the 'bench-latent' sub-command and are
      stored in the 'outdir' in two files named 'latent_vecs_<dataset>.npz'
      and 'latent_vecs_train_<dataset>.npz' for the
      test and train sets, respectively..
    - The associated metadata are stored in two others files named
      'latent_meta_<dataset>.tsv' and 'latent_meta_train_<dataset>.tsv'.
    - The samples shape is (n_samples, n_subjects, latent_dim). All samples
      must have the same number of samples and subjects, but possibly
      different latent dimensions.
    - The metadata columns must be the same.
    """
    print_title("COMPARE MODELS USING REGRESSIONS "
                f"OR CLASSIFICATION WITH ML ANALYSIS: {dataset}")
    benchdir = outdir
    print_text(f"Benchmark directory: {benchdir}")

    print_subtitle("Loading data...")
    latent_data_test = np.load(
        os.path.join(benchdir, f"latent_vecs_{dataset}.npz"))
    latent_data_train = np.load(
        os.path.join(benchdir, f"latent_vecs_train_{dataset}.npz"))
    assert (sorted(latent_data_test.keys()) ==
            sorted(latent_data_train.keys())), (
                "latent data must have the same keys")
    meta_df = pd.read_csv(
        os.path.join(benchdir, f"latent_meta_{dataset}.tsv"), sep="\t")
    meta_df_tr = pd.read_csv(
        os.path.join(benchdir, f"latent_meta_train_{dataset}.tsv"), sep="\t")
    assert (sorted(meta_df.columns) == sorted(meta_df_tr.columns)), (
        "metadata must have the same columns.")
    clinical_scores = meta_df_tr.columns
    predict_results = dict()
    for latent_key in latent_data_test:
        samples = latent_data_train[latent_key]
        samples_test = latent_data_test[latent_key]
        assert samples.shape[-1] == samples_test.shape[-1], (
            "The train and test data must be generated by the same model.")
        n_samples, _, _ = samples.shape

    print_subtitle("Train model...")
    res_cv_list = []
    for qname in clinical_scores:
        y_train = meta_df_tr[qname]
        y_test = meta_df[qname]
        for latent_key in latent_data_test:
            print_text(f"- {qname} - {latent_key}...")
            res, res_cv = [], []
            samples_train = latent_data_train[latent_key]
            samples_test = latent_data_test[latent_key]
            for idx in tqdm(range(n_samples)):
                clf, scoring = get_predictor(y_train)
                scores = cross_val_score(
                    clf, samples_train[idx], y_train, cv=5, scoring=scoring,
                    n_jobs=-1)
                clf.fit(samples_train[idx], y_train)
                res_cv.append(f"{scores.mean():.2f} +/- {scores.std():.2f}")
                scorer = metrics.get_scorer(scoring)
                res.append(scorer(clf, samples_test[idx], y_test))
            res_cv_df = pd.DataFrame.from_dict(
                {"model": range(n_samples), "score": res_cv})
            res_cv_df["qname"] = qname
            res_cv_df["latent"] = latent_key
            print(res_cv_df)
            res_cv_list.append(res_cv_df)
            predict_results.setdefault(qname, {})[latent_key] = np.asarray(res)
    predict_df = pd.DataFrame.from_dict(predict_results, orient="index")
    predict_df = pd.concat([predict_df[col].explode() for col in predict_df],
                           axis="columns")
    predict_df.to_csv(os.path.join(benchdir, "predict.tsv"), sep="\t",
                      index=False)
    _df = pd.concat(res_cv_list)
    _df.to_csv(os.path.join(benchdir, "predict_cv.tsv"), sep="\t",
               index=False)

    print_subtitle("Display statistics...")
    ncols = 3
    nrows = int(np.ceil(len(clinical_scores) / ncols))
    plt.figure(figsize=np.array((ncols, nrows)) * 4)
    pairwise_stats = []
    for idx, qname in enumerate(clinical_scores):
        ax = plt.subplot(nrows, ncols, idx + 1)
        pairwise_stat_df = plot_bar(
            qname, predict_results, ax=ax, figsize=None, dpi=300, fontsize=7,
            fontsize_star=12, fontweight="bold", line_width=2.5,
            marker_size=3, title=qname.upper(),
            do_one_sample_stars=False, palette="Set2")
        if pairwise_stat_df is not None:
            pairwise_stats.append(pairwise_stat_df)
    if len(pairwise_stats) > 0:
        pairwise_stat_df = pd.concat(pairwise_stats)
        pairwise_stat_df.to_csv(
            os.path.join(benchdir, "predict_pairwise_stats.tsv"), sep="\t",
            index=False)
    plt.subplots_adjust(
        left=None, bottom=None, right=None, top=None, wspace=.5, hspace=.5)
    plt.suptitle(f"{dataset.upper()} PREDICT RESULTS", fontsize=20, y=.95)
    filename = os.path.join(benchdir, f"predict_{dataset}.png")
    plt.savefig(filename)
    print_result(f"PREDICT: {filename}")


def get_predictor(data):
    """ Return a classifier and a ROCAuc metric if the data is of type int or
    str, otherwise a regressor and a MAE metric.

    Parameters
    ----------
    data: list
        list of value that will be submitted to a predictor.

    Returns
    -------
    predictor: linear_model
        A classifier or a regressor
    scoring: str or callable
        a scorer callable object/function with signature which returns a
        single value.
    """
    data = np.array(data)
    is_int = ((data - data.astype(int) == 0).all()
              if not isinstance(data[0], str) else False)
    if isinstance(data[0], str) or is_int:
        predictor = linear_model.RidgeClassifier()
        scoring = "balanced_accuracy"
    else:
        predictor = linear_model.Ridge(alpha=.5)
        scoring = "neg_mean_absolute_error"
    return predictor, scoring
