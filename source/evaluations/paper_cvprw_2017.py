# -*- coding: utf-8 -*-

############################################################################
#  This file is part of the 4D Light Field Benchmark.                      #
#                                                                          #
#  This work is licensed under the Creative Commons                        #
#  Attribution-NonCommercial-ShareAlike 4.0 International License.         #
#  To view a copy of this license,                                         #
#  visit http://creativecommons.org/licenses/by-nc-sa/4.0/.                #
#                                                                          #
#  Authors: Katrin Honauer & Ole Johannsen                                 #
#  Contact: contact@lightfield-analysis.net                                #
#  Website: www.lightfield-analysis.net                                    #
#                                                                          #
#  The 4D Light Field Benchmark was jointly created by the University of   #
#  Konstanz and the HCI at Heidelberg University. If you use any part of   #
#  the benchmark, please cite our paper "A dataset and evaluation          #
#  methodology for depth estimation on 4D light fields". Thanks!           #
#                                                                          #
#  @inproceedings{honauer2016benchmark,                                    #
#    title={A dataset and evaluation methodology for depth estimation on   #
#           4D light fields},                                              #
#    author={Honauer, Katrin and Johannsen, Ole and Kondermann, Daniel     #
#            and Goldluecke, Bastian},                                     #
#    booktitle={Asian Conference on Computer Vision},                      #
#    year={2016},                                                          #
#    organization={Springer}                                               #
#    }                                                                     #
#                                                                          #
############################################################################

import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np

from algorithms import PerPixMedianDiff, PerPixBest
from evaluations import bad_pix_series, metric_overviews, radar_chart, meta_algo_comparisons
from metrics import *
import settings
from utils import misc, plotting
from utils.logger import log


def plot_benchmark_scene_overview(benchmark_scenes, subdir="overview", fs=16):
    # prepare grid figure
    rows, cols = 2, 12
    fig = plt.figure(figsize=(21.6, 4))
    grids = plotting.prepare_grid(rows, cols)

    # plot center view and ground truth for each scene
    for idx_s, scene in enumerate(benchmark_scenes):

        center_view = scene.get_center_view()
        plt.subplot(grids[idx_s])
        plt.imshow(center_view)
        plt.title("\n\n" + scene.get_display_name(), fontsize=fs)

        try:
            gt = scene.get_gt()
            plt.subplot(grids[cols+idx_s])
            if scene.hidden_gt():
                gt = plotting.pixelize(gt, noise_factor=0.5)
            plt.imshow(gt, **settings.disp_map_args(scene))
        except IOError as e:
            # skip potentially missing ground truth of test scenes
            log.info(e)
            continue

    # add text
    height = 785
    plt.gca().annotate("(a) Stratified Scenes", (400, 420), (500, height),
                       fontsize=fs, xycoords='figure pixels')
    plt.gca().annotate("(b) Training Scenes", (400, 420), (1910, height),
                       fontsize=fs, xycoords='figure pixels')
    plt.gca().annotate("(c) Test Scenes (Hidden Ground Truth)", (400, 420), (3070, height),
                       fontsize=fs, xycoords='figure pixels')

    # save figure
    fig_path = plotting.get_path_to_figure("benchmark_scenes", subdir=subdir)
    plotting.save_tight_figure(fig, fig_path, hide_frames=True, remove_ticks=True, hspace=0.02, wspace=0.02, dpi=200)


def plot_scene_difficulty(scenes, subdir="overview", fs=10):

    n_scenes_per_row = 4
    rows, cols = 6, n_scenes_per_row + 1
    fig = plt.figure(figsize=(6, 9))
    grid, cb_height, cb_width = plotting.prepare_grid_with_colorbar(rows, cols, scenes[0])
    colorbar_args = {"height": cb_height, "width": cb_width, "colorbar_bins": 2, "fontsize": fs}

    median_algo = PerPixMedianDiff()
    best_algo = PerPixBest()

    for idx_s, scene in enumerate(scenes):
        # prepare data
        gt = scene.get_gt()
        median_result = misc.get_algo_result(scene, median_algo)
        best_result = misc.get_algo_result(scene, best_algo)

        idx_row = idx_s / n_scenes_per_row * 2
        idx_col = (idx_s % n_scenes_per_row)
        add_ylabel = not (idx_s % n_scenes_per_row)  # is first column
        add_colorbar = idx_col == (n_scenes_per_row - 1)  # is last column

        # plot errors for median result
        plt.subplot(grid[idx_row * cols + idx_col])
        plt.title(scene.get_display_name(), fontsize=fs)
        cb = plt.imshow(np.abs(gt - median_result), **settings.abs_diff_map_args())

        if add_ylabel:
            plt.ylabel("|GT - %s|" % median_algo.get_display_name(), fontsize=fs-2)
        if add_colorbar:
            plotting.add_colorbar(grid[(idx_row) * cols + idx_col + 1], cb, **colorbar_args)

        # plot error for best result
        plt.subplot(grid[(idx_row+1) * cols + idx_col])
        cb = plt.imshow(np.abs(gt - best_result), **settings.abs_diff_map_args())

        if add_ylabel:
            plt.ylabel("|GT - %s|" % best_algo.get_display_name(), fontsize=fs-2)
        if add_colorbar:
            plotting.add_colorbar(grid[(idx_row+1) * cols + idx_col + 1], cb, **colorbar_args)

    fig_path = plotting.get_path_to_figure("scene_difficulty", subdir=subdir)
    plotting.save_tight_figure(fig, fig_path, hide_frames=True, remove_ticks=True, hspace=0.08, wspace=0.03)


def plot_normals_explanation(scene, algorithm, fs=14, subdir="overview"):
    # prepare figure
    rows, cols = 1, 4
    fig = plt.figure(figsize=(10, 4))
    grid, cb_height, cb_width = plotting.prepare_grid_with_colorbar(rows, cols, scene)

    # prepare metrics
    normals_contin = MAEContinSurf()
    normals_planes = MAEPlanes()

    # prepare data
    gt = scene.get_gt()
    algo_result = misc.get_algo_result(scene, algorithm)
    mask = normals_contin.get_evaluation_mask(scene) + normals_planes.get_evaluation_mask(scene)
    score_normals, vis_normals = normals_contin.get_score_from_mask(algo_result, gt, scene, mask,
                                                                    with_visualization=True)

    # plot ground truth normals
    plt.subplot(grid[0])
    plt.imshow(scene.get_normal_vis_from_disp_map(gt))
    plt.title("Ground Truth Normals", fontsize=fs)

    # plot algorithm normals
    plt.subplot(grid[1])
    plt.imshow(scene.get_normal_vis_from_disp_map(algo_result))
    plt.title("Algorithm Normals", fontsize=fs)

    # plot median angular error with colorbar
    plt.subplot(grid[2])
    cb = plt.imshow(vis_normals, **settings.metric_args(normals_contin))
    plt.title("Median Angular Error: %0.1f" % score_normals, fontsize=fs)
    plt.subplot(grid[3])
    plotting.add_colorbar(grid[3], cb, cb_height, cb_width, colorbar_bins=4, fontsize=fs)

    # save figure
    fig_path = plotting.get_path_to_figure("metrics_%s_%s" % (scene.get_name(), algorithm.get_name()), subdir=subdir)
    plotting.save_tight_figure(fig, fig_path, hide_frames=False, remove_ticks=True, hspace=0.04, wspace=0.03)


def plot_bad_pix_series(algorithms, with_cached_scores=False, penalize_missing_pixels=False, subdir="bad_pix"):
    scene_sets = [[misc.get_stratified_scenes(), "Stratified Scenes", "stratified"]]
    if settings.USE_TEST_SCENE_GT:
        scene_sets.append([misc.get_training_scenes()+misc.get_test_scenes(), "Test and Training Scenes", "photorealistic"])
    else:
        scene_sets.append([misc.get_training_scenes(), "Training Scenes", "training"])

    for scene_set, title, fig_name in scene_sets:
        bad_pix_series.plot(algorithms, scene_set,
                            with_cached_scores=with_cached_scores,
                            penalize_missing_pixels=penalize_missing_pixels,
                            title=title, subdir=subdir, fig_name="bad_pix_series_" + fig_name)


def plot_radar_charts(algorithms, log_runtime=True, subdir="radar"):
    base_metrics = [Runtime(log=log_runtime), MSE(), Quantile(25),
                    BadPix(0.01), BadPix(0.03), BadPix(0.07)]

    region_metrics = [MAEPlanes(), MAEContinSurf(),
                      BumpinessPlanes(), BumpinessContinSurf(),
                      FineFattening(), FineThinning(), Discontinuities()]

    # stratified scenes and applicable metrics
    metrics = base_metrics + misc.get_stratified_metrics()
    metric_names = [m.get_display_name().replace(":", "\n") for m in metrics]
    max_per_metric = [5, 16, 2, 120, 80, 40, 40, 8, 6, 6, 24, 128, 48, 64, 100]
    radar_chart.plot(algorithms,
                     scenes=misc.get_stratified_scenes(),
                     metrics=metrics,
                     axis_labels=metric_names,
                     max_per_metric=max_per_metric,
                     title="Median Scores for Stratified Scenes",
                     fig_name="radar_stratified",
                     subdir=subdir)

    # photorealistic scenes and applicable metrics
    metrics = base_metrics + region_metrics
    metric_names = [m.get_display_name().replace(" ", "\n") for m in metrics]
    max_per_metric = [5, 12, 2, 128, 72, 32, 80, 80, 4, 4, 80, 16, 72]
    radar_chart.plot(algorithms,
                     scenes=misc.get_training_scenes() + misc.get_test_scenes(),
                     metrics=metrics,
                     axis_labels=metric_names,
                     max_per_metric=max_per_metric,
                     title="Median Scores for Test and Training Scenes",
                     fig_name="radar_photorealistic",
                     subdir=subdir)

    radar_chart.compare_relative_performances(algorithms, misc.get_training_scenes(), metrics, all_but=0)
    radar_chart.compare_relative_performances(algorithms, misc.get_training_scenes(), metrics, all_but=1)


def plot_normals_overview(algorithms, scenes, subdir="overview"):
    metric_overviews.plot_normals(algorithms, scenes, subdir=subdir)


def plot_high_accuracy(algorithms, scenes, subdir="overview"):
    metrics = [BadPix(0.07), BadPix(0.01), Quantile(25)]
    metric_overviews.plot_general_overview(algorithms, scenes, metrics, fig_name="high_accuracy", subdir=subdir)


def plot_discont_overview(algorithms, scene, n_rows=2, fs=15, subdir="overview", xmin=150, ymin=230, ww=250):

    # prepare figure grid
    n_vis_types = 2
    n_entries_per_row = int(np.ceil((len(algorithms) + 1) / float(n_rows)))
    rows, cols = (n_vis_types * n_rows), n_entries_per_row + 1

    fig = plt.figure(figsize=(cols * 1.7, 1.45 * rows * 1.5))
    grid, cb_height, cb_width = plotting.prepare_grid_with_colorbar(rows, cols, scene)
    colorbar_args = {"height": cb_height, "width": cb_width, "colorbar_bins": 7, "fontsize": fs}

    # prepare data
    median_algo = PerPixMedianDiff()
    gt = scene.get_gt()
    median_result = misc.get_algo_result(scene, median_algo)
    center_view = scene.get_center_view()

    # center view
    plt.subplot(grid[0])
    plt.imshow(center_view[ymin:ymin + ww, xmin:xmin + ww])
    plt.title("Center View", fontsize=fs)
    plt.ylabel("DispMap", fontsize=fs)
    plt.subplot(grid[cols])
    plt.ylabel("MedianDiff", fontsize=fs)

    for idx_a, algorithm in enumerate(algorithms):
        algo_result = misc.get_algo_result(scene, algorithm)
        idx = idx_a + 1

        add_ylabel = not idx % n_entries_per_row  # is first column
        add_colorbar = not ((idx + 1) % n_entries_per_row)  # is last column
        idx_row = (idx / n_entries_per_row) * n_vis_types
        idx_col = idx % n_entries_per_row

        # top row with algorithm disparity map
        plt.subplot(grid[idx_row * cols + idx_col])
        cb_depth = plt.imshow(algo_result[ymin:ymin + ww, xmin:xmin + ww], **settings.disp_map_args(scene))
        plt.title(algorithm.get_display_name(), fontsize=fs)

        if add_ylabel:
            plt.ylabel("DispMap", fontsize=fs)
        if add_colorbar:
            plotting.add_colorbar(grid[idx_row * cols + idx_col + 1], cb_depth, **colorbar_args)

        # second row with median diff
        plt.subplot(grid[(idx_row + 1) * cols + idx_col])
        median_diff = (np.abs(median_result - gt) - np.abs(algo_result - gt))[ymin:ymin + ww, xmin:xmin + ww]
        cb_error = plt.imshow(median_diff, interpolation="none", cmap=cm.RdYlGn, vmin=-.05, vmax=.05)

        if add_ylabel:
            plt.ylabel("MedianDiff", fontsize=fs)
        if add_colorbar:
            plotting.add_colorbar(grid[(idx_row + 1) * cols + idx_col + 1], cb_error, **colorbar_args)

    fig_path = plotting.get_path_to_figure("discont_%s" % scene.get_name(), subdir=subdir)
    plotting.save_tight_figure(fig, fig_path, hide_frames=True, remove_ticks=True, hspace=0.03, wspace=0.03, dpi=100)


def plot_median_comparisons(scenes, algorithms, subdir, with_gt_row=True):
    meta_algo_comparisons.plot(scenes, algorithms, PerPixMedianDiff(), subdir=subdir, with_gt_row=with_gt_row)

