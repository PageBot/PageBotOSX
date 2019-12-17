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
#     variations.py
#

from copy import copy
from pagebot.fonttoolbox.objects.font import getFont, getInstance
from pagebot.style import css
from pagebot.toolbox.units import upt
from pagebotcocoa.contexts.drawbot.drawbotstring import pixelBounds

class Variations:

    @classmethod
    def _newFitWidthString(cls, fs, context, fontSize, w, pixelFit):
        if pixelFit:
            tx, _, tw, _ = pixelBounds(fs)
        else:
            tx, tw = 0, context.b.textSize(fs)[0]
        fspt, wpt, txpt, twpt = upt(fontSize, w, tx, tw)

        # Render the units, to compare for zero division.
        dxpt = twpt - txpt 
        if dxpt:
            return wpt * fspt / dxpt

        # Zero division, cannot calculate.
        return None 

    @classmethod
    def _newFitHeightString(cls, fs, context, fontSize, h, pixelFit):
        if pixelFit:
            _, ty, _, th = pixelBounds(fs)
        else:
            ty, th = 0, context.b.textSize(fs)[1]

        fspt, hpt, typt, thpt = upt(fontSize, h, ty, th)

        # Render the units, to compare for zero division.
        dypt = thpt - typt 
        if dypt:
            return hpt * fspt / dypt

        # Zero division, cannot calculate.
        return None 

    FITTING_TOLERANCE = 3

    @classmethod
    def fitString(cls, t, context, e=None, style=None, w=None, h=None,
            useXTRA=True, pixelFit=True):
        """Answers the DrawBotString instance from valid attributes in style.
        Set all values after testing their existence, so they can inherit from
        previous style formats in the string. If the target width w and height
        are defined, and if there is a [wdth] or [XTRA] axis in the current
        Variable Font, then values are iterated to make the best location /
        instance for the rectangle fit. In case the fontSize is set and the
        width w is set, then just use the [wdth] or [XTRA] to make a horizontal
        fit, keeping the size. If the axes run to extreme, the string is return
        without changing width. In case a font path was supplied, then try
        to get a Font instance for that path, as we need to test it for
        existing axes as Variable Font.

        FIXME: Fitting does not work anymore.
        TODO: Move to base.

        >>> from pagebot import getContext
        >>> from pagebot.toolbox.color import blackColor
        >>> context = getContext('DrawBot')
        >>> from pagebot.fonttoolbox.objects.font import findFont
        >>> font = findFont('RobotoDelta-VF')
        >>> #font = findFont('Fit-Variable_1') # DJR-Fit needs to be installed.
        >>> style = dict(font=font, textFill=blackColor, textStroke=noColor)

        >>> 'wdth' in font.axes.keys() or 'XTRA' in font.axes.keys() # One of them is there
        True

        """

        """
        >>> s = DrawBotString.newString('Hello', context, style=style, w=pt(300))
        >>> s.bounds() # Rounded width
        (297, 195)
        >>> s = DrawBotString.fitString('Hello', context, style=style, w=pt(400), h=pt(220))
        >>> int(round(s.bounds()[2]-s.bounds()[0])) # Rounded pixel width
        399
        >>> int(round(s.bounds()[3]-s.bounds()[1])) # Rounded pixel height
        220
        >>> #s.bounds()

        """
        style = copy(style)

        # In case the used already supplied a VF location, use it.
        location = copy(css('', e, style, default={})) 
        font = css('font', e, style)

        # Assuming it's a path, get the Font instance.
        if isinstance(font, str): 
            # Make sure we gave a real Font instance.
            font = getFont(font) 
        style['font'] = font

        # Get the flag if fit locations should be rounded (less cached
        # instance) or accurate.
        roundVariableFitLocation = style.get('roundVariableFitLocation', True)

        # In case font is not a variable font, or not [wdth] or [XTRA] present,
        # then using normal string fit is the best we can do.
        if not 'wdth' in font.axes and not 'XTRA' in font.axes:
            return cls.newString(t, context, e=e, style=style, w=w, h=h, pixelFit=pixelFit)

        # Decide which axis to use for width adjustments and get the axis
        # values.
        if not useXTRA or not 'XTRA' in font.axes:
            # Try to force usage of [XTRA] if it exists, otherwise use[wdth]
            axisTag = 'wdth'
        else:
            axisTag = 'XTRA'
        minValue, defaultValue, maxValue = font.axes[axisTag]

        if h is not None:
            # Fitting in heigt, calculate/iterate for the fitting font size.
            bs = cls.newString(t, context, e=e, style=style, h=h, pixelFit=pixelFit)
            style['fontSize'] = bs.fittingFontSize
        else:
            # Assuming there is a fontSize set, we'll use that as vertical
            # requirement.
            bs = cls.newString(t, context, e=e, style=style, pixelFit=pixelFit)

        # Now we have a formatted string with a given fontSize, guess to fit on
        # the width.

        # Get pixel bounds of the string
        tx, _, tw, _ = bs.bounds() 

        # Pixel width of the current string.
        tw = tw - tx 

        # Testing if something changed, for extreme of axes.
        prevW = None 
        axisValue = defaultValue


        # Limit the maximum amount of iterations as safeguard.
        for n in range(100): 
            # Too wide, try iterate smaller in ratio of wdth / XTRA axis
            # values.
            if tw > w: 
                # Clip wide range to current.
                maxValue = axisValue 
                # Guess the new axisvalue from the ratio of tw / w
                axisValue = (axisValue - minValue)/2 + minValue
                if roundVariableFitLocation:
                    axisValue = int(round(axisValue))
                loc = copy(location)
                loc[axisTag] = axisValue
                loc['opsz'] = upt(style['fontSize'])
                style['font'] = getInstance(font, loc)
                bs = cls.newString(t, context, e=e, style=style, pixelFit=pixelFit)

                # Get pixel bounds of the string.
                tx, ty, tw, th = bs.bounds() 

                # Total width for the current.
                tw = tw - tx 

                # Did not change, probably not able to get more condensed.
                if prevW == tw: 
                    break
                prevW = tw

            # Too condensed, try to make wider.
            elif tw < w - cls.FITTING_TOLERANCE: 
                # Clip narrow range to current
                minValue = axisValue 
                axisValue = (maxValue - axisValue)/2 + axisValue
                if roundVariableFitLocation:
                    axisValue = int(round(axisValue))
                loc = copy(location)
                loc[axisTag] = axisValue
                loc['opsz'] = upt(style['fontSize'])
                style['font'] = getInstance(font, loc)
                bs = cls.newString(t, context, e=e, style=style, pixelFit=pixelFit)

                # Get pixel bounds of the string.
                tx, ty, tw, th = bs.bounds() 

                # Total width for the current.
                tw = tw - tx 

                # Did not change, probably not able to get more condensed.
                if prevW == tw: 
                    break

                prevW = tw


            # We found a fitting VF-location within tolerance. Back out.
            else: 
                break
        return bs

    """
    # FIXME: Disabled string fitting here. Use fitString(...) instead.
    if False and w is not None:
        # A target width is already defined, calculate again with the
        # fontSize ratio correction. We use the enclosing pixel bounds
        # instead of the context.textSide(newT) here, because it is more
        # consistent for tracked text. context.textSize will add space to
        # the right of the string.
        attrs = copy(attrs)
        attrs['textFill'] = attrs.get('fill')
        attrs['textStroke'] = attrs.get('stroke')
        attrs['textStrokeWidth'] = attrs.get('strokeWidth')

        fittingFontSize = cls._newFitWidthString(newT, context, attrs.get('fontSize', DEFAULT_FONT_SIZE), w, pixelFit)
        if fittingFontSize is not None: # Checked on zero division
            # Repair the attrs to style, so it can be reused for new string
            attrs['fontSize'] = fittingFontSize
            newS = cls.newString(t, context, style=attrs)
            # Test the width we got by linear interpolation. Scale back if still too large.
            # Iterate until it really fits.
            while newS.size[0] > w and attrs['fontSize']:
                attrs['fontSize'] -= 0.1 # Incremental decrease the size until it fits
                newS = cls.newString(t, context, style=attrs)
        else:
            newS = cls(newT, context, attrs) # Cannot fit, answer untouched.
            isFitting = False
    elif False and h is not None:
        # A target height is already defined, calculate again with the
        # fontSize ratio correction. We use the enclosing pixel bounds
        # instead of the context.textSide(newT) here, because it is
        # more consistent for tracked text. context.textSize will add space
        # to the right of the string.
        attrs = copy(attrs)
        attrs['fontSize'] = fittingFontSize
        attrs['textFill'] = attrs.get('fill')
        attrs['textStroke'] = attrs.get('stroke')
        attrs['textStrokeWidth'] = attrs.get('strokeWidth')

        fittingFontSize = cls._newFitHeightString(newT, context, attrs.get('fontSize', DEFAULT_FONT_SIZE), h, pixelFit)

        if fittingFontSize is not None:
            # Repair the attrs to style, so it can be reused for new string
            newS = cls.newString(t, context, style=attrs)
            didFit = True
        else:
            newS = cls(newT, context, attrs) # Cannot fit, answer untouched.
            isFitting = False
    else:
    """

