#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# -----------------------------------------------------------------------------
#
#     P A G E B O T
#
#     Copyright (c) 2016+ Buro Petr van Blokland + Claudia Mens
#     www.pagebot.io
#     Licensed under MIT conditions
#
#     Supporting DrawBot, www.drawbot.com
#     Supporting Flat, xxyxyz.org/flat
# -----------------------------------------------------------------------------
#
#     transform.py
#

from fontTools.misc.transform import Transform

def transformationAtCenter(matrix, centerPoint):
    """Helper function for rotate(), scale() and skew() to apply a
    transformation with a specified center point.

        >>> transformationAtCenter((2, 0, 0, 2, 0, 0), (0, 0))
        (2, 0, 0, 2, 0, 0)
        >>> transformationAtCenter((2, 0, 0, 2, 0, 0), (100, 200))
        (2, 0, 0, 2, -100, -200)
        >>> transformationAtCenter((-2, 0, 0, 2, 0, 0), (100, 200))
        (-2, 0, 0, 2, 300, -200)
        >>> t = Transform(*transformationAtCenter((0, 1, 1, 0, 0, 0), (100, 200)))
        >>> t.transformPoint((100, 200))
        (100, 200)
        >>> t.transformPoint((0, 0))
        (-100, 100)
    """
    if centerPoint == (0, 0):
        return matrix

    t = Transform()
    cx, cy = centerPoint
    t = t.translate(cx, cy)
    t = t.transform(matrix)
    t = t.translate(-cx, -cy)
    return tuple(t)


