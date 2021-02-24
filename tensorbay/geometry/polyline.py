#!/usr/bin/env python3
#
# Copyright 2021 Graviti. Licensed under MIT License.
#

"""This file defines class Polyline2D"""

import math
from typing import Any, Dict, Iterator, List, Sequence, Tuple, Type, TypeVar

import numpy as np

from ..utility import common_loads
from .polygon import PointList2D
from .vector import Vector2D


class Polyline2D(PointList2D[Vector2D]):
    """this class defines the concept of Polyline2D based on class PointList2D"""

    _ElementType = Vector2D
    _P = TypeVar("_P", bound="Polyline2D")

    @classmethod
    def loads(cls: Type[_P], contents: List[Dict[str, float]]) -> _P:
        """Load a Polyline2D from a list of dict containing coordinates of 2D vectors
            within the 2D polyline.

        :param contents: A list of dict containing coordinates of 2D vectors within the 2D polyline
        [
            {
                "x": ...
                "y": ...
            },
            ...
        ]
        :return: The loaded Polyline2D
        """
        return common_loads(cls, contents)

    @staticmethod
    def _distance(point1: Sequence[float], point2: Sequence[float]) -> float:
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    @staticmethod
    def _get_polyline_info(polyline: Sequence[Sequence[float]]) -> List[Dict[str, Any]]:
        points = np.array(polyline, dtype=np.float32)
        vector = [points[i] - points[i - 1] for i in range(1, len(points))]
        length = [Polyline2D._distance(v, [0, 0]) for v in vector]
        distance = np.cumsum(length)
        time = distance / distance[-1]
        info: List[Dict[str, Any]] = []

        for index, v in enumerate(vector):  # pylint: disable=invalid-name
            info.append(
                {
                    "vector": v,
                    "last_time": time[index - 1] if index else 0,
                    "time": time[index],
                    "point": points[index],
                    "index": index,
                }
            )
        return info

    @staticmethod
    def _insert_point(info1: Dict[str, Any], info2: Dict[str, Any]) -> Dict[str, Any]:
        """Insert one point in info1 into the info2.

        :param info1: segment info of the insert point
        :param info2: the inserted segment info
        :return: a dictionary containing info of the inserted point
        """
        ratio = (info1["time"] - info2["last_time"]) / (info2["time"] - info2["last_time"])
        insert_point = info2["point"] + info2["vector"] * ratio
        return {"index": info2["index"] + 1, "point": insert_point}

    @staticmethod
    def _insert_points(
        polyline_info1: Iterator[Dict[str, Any]],
        polyline_info2: Iterator[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Calculate insert points in polyline1 and polyline2.

        :param polyline_info1: segment info in polyline1
        :param polyline_info2: segment info in polyline2
        :returns:
            insert points in polyline1
            insert points in polyline2
        """
        insert_points1: List[Dict[str, Any]] = []
        insert_points2: List[Dict[str, Any]] = []
        info1 = next(polyline_info1)
        info2 = next(polyline_info2)

        try:
            while True:
                if info1["time"] < info2["time"]:
                    insert_points2.append(Polyline2D._insert_point(info1, info2))
                    info1 = next(polyline_info1)
                    continue

                if info1["time"] > info2["time"]:
                    insert_points1.append(
                        Polyline2D._insert_point(  # pylint: disable=arguments-out-of-order
                            info2, info1
                        )
                    )
                    info2 = next(polyline_info2)
                    continue

                if info1["time"] == info2["time"]:
                    info1 = next(polyline_info1)
                    info2 = next(polyline_info2)
        except StopIteration:
            pass
        return insert_points1, insert_points2

    @staticmethod
    def _max_distance_in_point_pairs(polyline1: np.ndarray, polyline2: np.ndarray) -> float:
        """Calculate the maximum distance between point pairs in two polylines.

        :param polyline1: the first inserted polyline
        :param polyline2: the second inserted polyline, containing the same number of
            points as the first one
        :return: the maximum distance between point pairs in two polylines
        """
        assert len(polyline1) == len(polyline2)

        max_distance = -1.0
        for point1, point2 in zip(polyline1, polyline2):
            distance = Polyline2D._distance(point1, point2)
            if distance > max_distance:
                max_distance = distance
        return max_distance

    @staticmethod
    def uniform_frechet_distance(
        polyline1: Sequence[Sequence[float]],
        polyline2: Sequence[Sequence[float]],
    ) -> float:
        """Compute the maximum distance between two curves if walk on a constant speed on a curve.

        :param polyline1: the first polyline consisting of multiple points
        :param polyline2: the second polyline consisting of multiple points
        :return: the computed distance between the two polylines
        """
        polyline_info1 = Polyline2D._get_polyline_info(polyline1)
        polyline_info2 = Polyline2D._get_polyline_info(polyline2)
        line2_reverse = list(reversed(polyline2))
        polyline_info2_reverse = Polyline2D._get_polyline_info(line2_reverse)

        # forward
        insert_points1, insert_points2 = Polyline2D._insert_points(
            iter(polyline_info1), iter(polyline_info2)
        )
        line1 = polyline1
        line2 = polyline2
        for point in reversed(insert_points1):
            line1 = np.insert(line1, point["index"], point["point"], axis=0)
        for point in reversed(insert_points2):
            line2 = np.insert(line2, point["index"], point["point"], axis=0)
        distance_forward = Polyline2D._max_distance_in_point_pairs(line1, line2)

        # reverse
        insert_points1, insert_points2 = Polyline2D._insert_points(
            iter(polyline_info1), iter(polyline_info2_reverse)
        )
        for point in reversed(insert_points1):
            polyline1 = np.insert(polyline1, point["index"], point["point"], axis=0)
        for point in reversed(insert_points2):
            line2_reverse = np.insert(line2_reverse, point["index"], point["point"], axis=0)
        distance_reverse = Polyline2D._max_distance_in_point_pairs(polyline1, line2_reverse)

        return min(distance_forward, distance_reverse)

    @staticmethod
    def similarity(
        polyline1: Sequence[Sequence[float]],
        polyline2: Sequence[Sequence[float]],
    ) -> float:
        """Calculate the similarity between two polylines, range from 0 to 1.

        :param polyline1: the first polyline consisting of multiple points
        :param polyline2: the second polyline consisting of multiple points
        :return: the similarity between the two polylines. The bigger, the more similar.
        """
        min_distance = Polyline2D.uniform_frechet_distance(polyline1, polyline2)
        max_distance = -1.0
        for point1 in polyline1:
            for point2 in polyline2:
                distance = Polyline2D._distance(point1, point2)
                if distance > max_distance:
                    max_distance = distance
        return 1 - min_distance / max_distance
