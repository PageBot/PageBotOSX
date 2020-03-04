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
#     pattern.py
#

class FoundPattern:
    """Searches for regex patterns inside a TextLine."""

    def __init__(self, s, x, ix, y=None, w=None, h=None, line=None, run=None):
        # Found string.
        self.s = s
        self.x = x
        self.ix = ix
        self.y = y
        self.w = w
        self.h = h
        # TextLine instance that this was found in.
        self.line = line
        # List of this string.
        self.run = run

    def __repr__(self):
        return '[Found "%s" @ %d,%d]' % (self.s, self.x, self.y)

    #   F I N D

def findPattern(textLines, pattern):
    """Answers the point locations where this pattern occurs in the Formatted
    String."""
    # List of FoundPattern instances.
    foundPatterns = []

    for lineIndex, textLine in enumerate(textLines):
        for foundPattern in textLine.findPattern(pattern):
            foundPattern.y = textLine.y
            foundPattern.z = 0
            foundPatterns.append(foundPattern)
    return foundPatterns


