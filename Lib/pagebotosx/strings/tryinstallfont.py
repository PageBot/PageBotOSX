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
#     tryinstallfont.py
#

import logging
from drawBot.drawBotDrawingTools import _drawBotDrawingTool

logger = logging.getLogger(__name__)

def _tryInstallFontFromFontName(fontName):
    # TODO: too much drawBot, need to port.
    try:
        return _drawBotDrawingTool._tryInstallFontFromFontName(fontName)
    except Exception as e:
        logger.error('_tryInstallFontFromFontName: %s', e)

