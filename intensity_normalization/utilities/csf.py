#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
intensity_normalization.utilities.csf

functions to create the CSF control mask
separated from other routines since it relies on ANTsPy

Author: Jacob Reinhold (jacob.reinhold@jhu.edu)

Created on: Jun 08, 2018
"""

from functools import reduce
from glob import glob
import logging
from operator import add
import os

import ants
import numpy as np

from intensity_normalization.errors import NormalizationError
from intensity_normalization.utilities import io

logger = logging.getLogger(__name__)


def csf_mask(img, brain_mask, csf_thresh=0.9, return_prob=False, mrf=0.25):
    """
    create a binary mask of csf using atropos (FMM) segmentation
    of a T1-w image

    Args:
        img (ants.core.ants_image.ANTsImage or nibabel.nifti1.Nifti1Image): target img
        brain_mask (ants.core.ants_image.ANTsImage or nibabel.nifti1.Nifti1Image): brain mask for img
        csf_thresh (float): membership threshold to count as CSF
        return_prob (bool): if true, then return membership values
            instead of binary (i.e., thresholded membership) mask
        mrf (float): markov random field parameter
            (i.e., smoothness parameter, higher is a smoother segmentation)

    Returns:
        csf (np.ndarray): binary CSF mask for img
    """
    # convert nibabel to antspy format images (to do atropos segmentation)
    if hasattr(img, 'get_data') and hasattr(brain_mask, 'get_data'):
        img = ants.from_nibabel(img)
        brain_mask = ants.from_nibabel(brain_mask)
    res = img.kmeans_segmentation(3, kmask=brain_mask, mrf=mrf)
    avg_intensity = [np.mean(img.numpy()[prob_img.numpy() > 0.5]) for prob_img in res['probabilityimages']]
    csf_arg = np.argmin(avg_intensity)
    csf = res['probabilityimages'][csf_arg].numpy()
    if not return_prob:
        csf = (csf > csf_thresh).astype(np.float32)
    return csf


def csf_mask_intersection(img_dir, masks=None, prob=1):
    """
    use all nifti T1w images in data_dir to create csf mask in common areas

    Args:
        img_dir (str): directory containing MR images to be normalized
        masks (str or ants.core.ants_image.ANTsImage): if images are not skull-stripped,
            then provide brain mask as either a corresponding directory or an individual mask
        prob (float): given all data, proportion of data labeled as csf to be
            used for intersection

    Returns:
        intersection (np.ndarray): binary mask of common csf areas for all provided imgs
    """
    if not (0 <= prob <= 1):
        raise NormalizationError('prob must be between 0 and 1. {} given.'.format(prob))
    data = sorted(glob(os.path.join(img_dir, '*.nii*')))
    masks = sorted(glob(os.path.join(masks, '*.nii*'))) if isinstance(masks, str) else [masks] * len(data)
    csf = []
    for i, (img, mask) in enumerate(zip(data, masks)):
        _, base, _ = io.split_filename(img)
        logger.info('Creating CSF mask for image {} ({:d}/{:d})'.format(base, i+1, len(data)))
        imgn = ants.image_read(img)
        maskn = ants.image_read(mask) if isinstance(mask, str) else mask
        csf.append(csf_mask(imgn, maskn))
    csf_sum = reduce(add, csf)  # need to use reduce instead of sum b/c data structure
    intersection = np.zeros(csf_sum.shape)
    intersection[csf_sum >= np.floor(len(data) * prob)] = 1
    return intersection