#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
intensity_normalization.exec.preprocess.py

preprocess.py a set of MR images according to a simple scheme,
that is:
    1) N4 bias field correction
    2) resample to 1mm x 1mm x 1mm
    3) reorient images to RAI
this process requires brain masks for all images

Author: Jacob Reinhold (jacob.reinhold@jhu.edu)

Created on: May 21, 2018
"""

import argparse
import logging
import sys
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=FutureWarning)
    from intensity_normalization.utilities.preprocess import preprocess


def arg_parser():
    parser = argparse.ArgumentParser(description='Do some basic preprocessing on a set of nifti MR images of the brain. '
                                                 '(i.e., resampling, reorientation, and bias field correction)')
    parser.add_argument('-i', '--img-dir', type=str, required=True,
                        help='path to directory with images to be processed '
                             '(should all be T1w contrast)')
    parser.add_argument('-m', '--mask-dir', type=str, required=True,
                        help='directory to output the corresponding img files')
    parser.add_argument('-o', '--out-dir', type=str, required=True,
                        help='output directory for preprocessed files')
    parser.add_argument('-r', '--resolution', nargs=3, type=int, default=(1,1,1),
                        help='resolution for resampled images')
    parser.add_argument('--orientation', type=str, default='RAI',
                        help='orientation of preprocessed images')
    parser.add_argument('--n4-opts', type=dict, default=None,
                        help='n4 options, see ants.n4_bias_field_correction')
    parser.add_argument('-v', '--verbosity', action="count", default=0,
                        help="increase output verbosity (e.g., -vv is more than -v)")
    return parser


def main():
    args = arg_parser().parse_args()
    if args.verbosity == 1:
        level = logging.getLevelName('INFO')
    elif args.verbosity >= 2:
        level = logging.getLevelName('DEBUG')
    else:
        level = logging.getLevelName('WARNING')
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=level)
    logger = logging.getLogger(__name__)
    try:
        preprocess(args.img_dir, args.mask_dir, args.out_dir, args.resolution, args.orientation, args.n4_opts)
        return 0
    except Exception as e:
        logger.exception(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())