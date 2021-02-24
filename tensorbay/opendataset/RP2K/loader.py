#!/usr/bin/env python3
#
# Copytright 2021 Graviti. Licensed under MIT License.
#
# pylint: disable=invalid-name

"""This file defines the RP2K Dataloader"""

import os

from ...dataset import Data, Dataset
from ...label import Classification
from .._utility import glob

DATASET_NAME = "RP2K"


def RP2K(path: str) -> Dataset:
    """
    Load the RP2K to TensorBay
    :param path: the root path of dataset
    The file structure of RP2K looks like:
    <path>
        all/
            test/
                <catagory>/
                    <image_name>.jpg
                    ...
                ...
            train/
                <catagory>/
                    <image_name>.jpg
                    ...
                ...
    """
    root_path = os.path.join(os.path.abspath(os.path.expanduser(path)), "all")
    dataset = Dataset(DATASET_NAME)
    dataset.load_catalog(os.path.join(os.path.dirname(__file__), "catalog.json"))

    for segment_name in ("train", "test"):
        segment = dataset.create_segment(segment_name)
        segment_path = os.path.join(root_path, segment_name)
        catagories = os.listdir(segment_path)
        catagories.sort()
        for catagory in catagories:
            if not os.path.isdir(catagory):
                continue
            image_paths = glob(os.path.join(segment_path, catagory, "*.jpg"))
            for image_path in image_paths:
                data = Data(image_path)
                data.labels.classification = Classification(catagory)
                segment.append(data)

    return dataset
