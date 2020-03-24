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
#     drawbotcontext.py
#

import os
from CoreText import (CTFontDescriptorCreateWithNameAndSize,
        CTFontDescriptorCopyAttribute, kCTFontURLAttribute)
from AppKit import NSFont
import drawBot
from pagebot.constants import *
from pagebot.contexts.basecontext.babelstring import BabelString
from pagebot.contexts.basecontext.basecontext import BaseContext
from pagebot.toolbox.color import color, noColor
from pagebot.toolbox.units import pt, upt, point2D
from pagebot.toolbox.transformer import path2Name, path2Dir
from drawBot import Variable
from pagebotosx.contexts.drawbotcontext.drawbotstring import DrawBotString as stringClass

# Identifier to make builder hook name. Views will try to call e.build_html()
drawBotBuilder = drawBot
drawBotBuilder.PB_ID = 'drawBot'

class DrawBotContext(BaseContext):
    """DrawBotContext adapts DrawBot functionality to PageBot."""

    STRING_CLASS = stringClass
    EXPORT_TYPES = (FILETYPE_PDF, FILETYPE_SVG, FILETYPE_PNG, FILETYPE_JPG,
            FILETYPE_GIF, FILETYPE_MOV)

    '''
    /_scaled will be ignored with default .gitignore settings.  If the
    docs/images/_scaled folder need to be committed to a Git repository, remove
    _scaled from .gitignore.
    '''
    SCALED_PATH = '_scaled' # /scaled with upload on Git. /_scaled will be ignored.

    def __init__(self):
        """Constructor of DrawBotContext if drawBot import exists.

        >>> drawBotBuilder is not None
        True
        >>> drawBotBuilder is not None and drawBotBuilder.PB_ID == 'drawBot'
        True
        >>> from pagebot import getContext
        >>> context = getContext('DrawBot')
        >>> context.name
        'DrawBotContext'
        """
        super().__init__()
        # The context builder "cls.b" is drawBot which executes actual drawing
        # calls, similar to function calls in DrawBot scripts.
        self.b = drawBotBuilder #  Builder for this canvas.
        self.name = self.__class__.__name__
        # Holds the extension as soon as the export file path is defined.
        self.fileType = DEFAULT_FILETYPE

    # Drawing.

    def newDrawing(self, w=None, h=None, doc=None):
        """Clear output canvas, start new export file. DrawBot function.

        >>> from pagebot import getContext
        >>> context = getContext('DrawBot')
        >>> context.newDrawing()
        """
        self.b.newDrawing()

    def endDrawing(self, doc=None):
        self.b.endDrawing()

    def saveDrawing(self, path, multiPage=None):
        """Select non-standard DrawBot export builders here. Save the current
        image as path, rendering depending on the extension of the path file.
        In case the path starts with "_export", create its directories.

        >>> from pagebot import getContext
        >>> context = getContext('DrawBot')
        >>> context.saveImage('_export/MyFile.pdf')

        """
        self.checkExportPath(path)

        if path.lower().endswith('.mov'):
            self.b.saveImage(path)
        else:
            self.b.saveImage(path, multipage=multiPage)

    saveImage = saveDrawing

    def getDrawing(self):
        """Returns a PDF document of the current state."""
        return self.b.pdfImage()

    def setStyles(self, styles):
        pass

    #   V A R I A B L E

    def Variable(self, variables, workSpace):
        """Offers interactive global value manipulation in DrawBot. Should be
        ignored in other contexts.

        Variable is a DrawBot context global, used to make simple UI with
        controls on input parameters."""
        Variable(variables, workSpace)

    #   D R A W I N G

    def bluntCornerRect(self, x, y, w, h, offset=5):
        """Draw a rectangle in the canvas. This method is using the core
        BezierPath as path to draw on. For a more rich environment use
        BasePath(context) instead.

        TODO: move to elements.

        >>> from pagebot import getContext
        >>> context = getContext('DrawBot')
        >>> context.bluntCornerRect(pt(0), pt(0), pt(100), pt(100))
        >>> context.bluntCornerRect(0, 0, 100, 100)
        """

        xPt, yPt, wPt, hPt, offsetPt = upt(x, y, w, h, offset)
        path = self.newPath() #
        path.moveTo((xPt+offsetPt, yPt))
        path.lineTo((xPt+wPt-offsetPt, yPt))
        path.lineTo((xPt+wPt, yPt+offsetPt))
        path.lineTo((xPt+wPt, yPt+hPt-offsetPt))
        path.lineTo((xPt+w-offsetPt, y+hPt))
        path.lineTo((xPt+offsetPt, y+hPt))
        path.lineTo((xPt, yPt+h-offsetPt))
        path.lineTo((xPt, yPt+offsetPt))
        self.closePath()
        self.drawPath(path)

    def roundedRect(self, x, y, w, h, offset=25):
        """Draw a rectangle in the canvas. This method is using the core BezierPath
        as path to draw on. For a more rich environment use BasePath(context)
        instead.

        TODO: move to elements.

        >>> from pagebot import getContext
        >>> context = getContext('DrawBot')
        >>> context.roundedRect(pt(0), pt(0), pt(100), pt(100))
        >>> context.roundedRect(0, 0, 100, 100)
        """
        xPt, yPt, wPt, hPt, offsetPt = upt(x, y, w, h, offset)
        path = self.newPath()
        path.moveTo((xPt+offsetPt, yPt))
        path.lineTo((xPt+wPt-offsetPt, yPt))
        path.curveTo((xPt+wPt, yPt), (xPt+wPt, yPt), (xPt+wPt, yPt+offsetPt))
        path.lineTo((xPt+wPt, yPt+hPt-offsetPt))
        path.curveTo((xPt+wPt, yPt+hPt), (xPt+wPt, yPt+hPt), (xPt+wPt-offsetPt, yPt+hPt))
        path.lineTo((xPt+offsetPt, yPt+hPt))
        path.curveTo((xPt, yPt+hPt), (xPt, yPt+hPt), (xPt, yPt+hPt-offsetPt))
        path.lineTo((xPt, yPt+offsetPt))
        path.curveTo((xPt, yPt), (xPt, yPt), (xPt+offsetPt, yPt))
        self.closePath()
        self.drawPath(path)

    #   T E X T
    #

    def text(self, s, p):
        """Draws the s text string at position p.

        `S` Can be a str, BabelString, or DrawBot FormattedString.

        NOTE: signature differs from DrawBot.
        """
        if isinstance(s, BabelString):
            # BabelString with a FormattedString inside.
            s = s.s
            position = point2D(upt(p))
        else:
            if not isinstance(s, str):
                # Otherwise converts to string if it is not already.
                s = str(s)
            # Regular string, use global font and size.
            position = point2D(upt(p))
            self.b.fontSize(self._fontSize)
            self.font(self._font)

        # Render point units to value tuple
        self.b.text(s, position)

    def textBox(self, s, r=None, clipPath=None, align=None):
        """Draws the s text string in rectangle r.

        `S` Can be a str, BabelString, or DrawBot FormattedString.

        NOTE: signature differs from DrawBot.

        >>> from pagebot.toolbox.units import pt
        >>> from pagebot import getContext
        >>> context = getContext('DrawBot')
        >>> context.newPage(420, 420)
        >>> txt = '''The 25-storey Jumeirah Beach Hotel, with its distinctive\
design in the shape of a wave, has become one of the most successful\
hotels in the world. Located on Jumeirah Beach, this well-known hotel\
offers a wonderful holiday experience and a variety of pleasurable\
activities. The many restaurants, bars and cafés, daily live\
entertainment and sports facilities will keep you entertained, whilst\
children will have a great time at the Sinbad’s Kids’ Club or Wild Wadi\
WaterparkTM which is freely accessible through a private gate.'''
        >>> bs = context.newString(txt)
        >>> context.fontSize(14)
        >>> tb = context.textBox(txt, r=(100, 450, 200, 300))
        >>> tb = context.textBox(bs, r=(100, 450, 200, 300))
        """
        tb = None

        if hasattr(s, 's'):
            # Assumes it's a BabelString with a FormattedString inside.
            s = s.s
        else:
            if not isinstance(s, str):
                # Otherwise converts to string if it is not already.
                s = str(s)

        if clipPath is not None:
            box = clipPath.bp
            tb = self.b.textBox(s, clipPath.bp)
        elif isinstance(r, (tuple, list)):
            # Renders rectangle units to value tuple.
            xpt, ypt, wpt, hpt = upt(r)
            box = (xpt, ypt, wpt, hpt)
            tb = self.b.textBox(s, box, align=None)
        else:
            msg = '%s.textBox has no box or clipPath defined' % self.__class__.__name__
            raise ValueError(msg)

        return tb

    def textOverflow(self, s, box, align=None):
        """Answers the overflow text if flowing it in the box. In case a plain
        string is given then the current font / fontSize / ... settings of the
        builder are used.

        `S` Can be a str, BabelString, or DrawBot FormattedString.

        >>> from pagebot import getContext
        >>> context = getContext('DrawBot')
        >>> context.newDrawing()
        >>> context.newPage(420, 420)
        >>> context.font('PageBot-Regular')
        >>> context.fontSize(12)
        >>> box = 0, 0, 300, 20
        >>> s = 'AAA ' * 200
        >>> len(s)
        800
        >>> # Plain string overflow.
        >>> of = context.textOverflow(s, box)
        >>> len(of)
        756
        >>> # Styled DrawBotString overflow.
        >>> style = dict(font='PageBot-Bold', fontSize=14)
        >>> bs = context.newString('AAA ' * 200, style=style)
        >>> of = context.textOverflow(bs, box)
        >>> len(of)
        764
        """
        if isinstance(s, str):
            return self.b.textOverflow(s, box, align=align) # Plain string

        # Assume here it's a DrawBotString with a FormattedString inside
        overflow = self.b.textOverflow(s.s, box, align=align)
        #bs = self.newString('')
        #bs.s = overflow
        return overflow

    def textBoxBaselines(self, txt, box, align=None):
        return self.b.textBoxBaselines(txt, box, align=align)

    def textSize(self, bs, w=None, h=None, align=None):
        """Answers the width and height of the formatted string with an
        optional given w or h."""
        return self.b.textSize(bs.s, width=w, height=h, align=align)

    def hyphenation(self, onOff):
        self.b.hyphenation(onOff)

    def language(self, language):
        self.b.language(language)

    #   P A T H
    #
    #   Function that work on the current running path stored in self._bezierpath
    #

    def newPath(self):
        self._bezierpath = self.b.BezierPath()
        return self.bezierpath

    def drawGlyphPath(self, glyph):
        """Converts the cubic commands to a drawable path."""
        path = self.getGlyphPath(glyph)
        self.drawPath(path)

    def getGlyphPath(self, glyph, p=None, path=None):
        """Answers the DrawBot path. Allow optional position offset and path,
        in case we do recursive component drawing.

        >>> from pagebot.fonttoolbox.objects.font import findFont
        >>> from pagebot import getContext
        >>> context = getContext('DrawBot')
        >>> f = findFont('Roboto-Regular')
        >>> print(f)
        <Font Roboto-Regular>
        >>> g = f['H']
        >>> path = context.getGlyphPath(g)
        """
        if path is None:
            path = self.newPath()

        if p is None:
            px = py = 0
        else:
            px = p[0]
            py = p[1]

        for command, t in glyph.cubic:
            if command == 'moveTo':
                path.moveTo((px+t[0], py+t[1]))
            elif command == 'lineTo':
                path.lineTo((px+t[0], py+t[1]))
            elif command == 'curveTo':
                path.curveTo((px+t[0][0], py+t[0][1]),
                        (px+t[1][0], py+t[1][1]), (px+t[2][0], py+t[2][1]))
            elif command == 'closePath':
                path.closePath()
            elif command == 'component':
                (x, y), componentGlyph = t
                self.getGlyphPath(componentGlyph, (px+x, py+y), path)

        return path

    def bezierPathByFlatteningPath(self, path=None):
        """Use the NSBezierPath flatten function. Answers None if the flattened
        path could not be made.
        """
        if path is None:
            path = self.bezierpath

        if hasattr(path, 'path'):
            # In case it is a BasePath.
            path = path.path

        return path._path.bezierPathByFlatteningPath()

    def getFlattenedPath(self, path=None):
        return self.bezierPathByFlatteningPath(path=path)

    def getFlattenedContours(self, path=None):
        """Answers the flattened Bézier path as  a contour list [contour,
        contour, ...] where contours are lists of point2D() points.

        """
        contour = []
        flattenedContours = [contour]

        # Use / create self._bezierpath if path is None.
        flatPath = self.bezierPathByFlatteningPath(path)

        if flatPath is not None:
            for index in range(flatPath.elementCount()):
                # NSBezierPath size + index call.
                p = flatPath.elementAtIndex_associatedPoints_(index)[1]

                if p:
                    # Make point2D() tuples, no need to add point type, all
                    # onCurve.
                    contour.append((p[0].x, p[0].y))
                else:
                    contour = []
                    flattenedContours.append(contour)

        return flattenedContours

    # Path drawing behavior.

    def strokeWidth(self, w):
        """Set the current stroke width.

        >>> from pagebot.toolbox.units import pt, mm
        >>> from pagebot import getContext
        >>> context = getContext()
        >>> context.newDrawing()
        >>> context.newPage(420, 420)
        >>> context.setStrokeWidth(pt(0.5))
        >>> context.setStrokeWidth(mm(0.5))
        """
        wpt = upt(w)
        self.b.strokeWidth(wpt)

    setStrokeWidth = strokeWidth

    def miterLimit(self, value):
        self.b.miterLimit(value)

    def lineJoin(self, value):
        self.b.lineJoin(value)

    def lineCap(self, value):
        """Possible values are butt, square and round."""
        assert value in ('butt', 'square', 'round')
        self.b.lineCap(value)

    def lineDash(self, value):
        """LineDash is None or a list of dash lengths."""
        if value is None:
            self.b.lineDash(None)
        else:
            self.b.lineDash(*value)

    #   F O N T S

    def fontPath2FontName(self, fontPath):
        """Answers the font name of the font related to fontPath. This is done
        by installing it (again). Answers None if the font cannot be installed
        or if the path does not exists.

        >>> import os
        >>> from pagebot.fonttoolbox.fontpaths import TEST_FONTS_PATH
        >>> from pagebot import getContext
        >>> context = getContext('DrawBot')
        >>> # Does not exist.
        >>> context.fontPath2FontName('Aaa.ttf') is None
        True
        >>> path = TEST_FONTS_PATH + '/fontbureau/Amstelvar-Roman-VF.ttf'
        >>> os.path.exists(path)
        True
        >>> context.fontPath2FontName(path)
        'Amstelvar-Roman'
        """
        if os.path.exists(fontPath):
            return self.b.font(fontPath)
        return None

    def fontName2FontPath(self, fontName):
        """Answers the unchanged path, if it exists as file. Answers the path
        that is source of the given font name. Answers None if the font cannot
        be found."""
        # If the font cannot be found by name, then test if the file exists as
        # path and answer it.
        if os.path.exists(fontName):
            return fontName

        # Otherwise try OSX for the conversion.
        nsFont = NSFont.fontWithName_size_(fontName, 25)

        if nsFont is not None:
            fontRef = CTFontDescriptorCreateWithNameAndSize(nsFont.fontName(), nsFont.pointSize())
            url = CTFontDescriptorCopyAttribute(fontRef, kCTFontURLAttribute)
            return url.path()
        return None

    #   G L Y P H

    def drawGlyph(self, glyph, x, y, fill=noColor, stroke=noColor,
            strokeWidth=0, fontSize=None, xAlign=CENTER):
        """Draw the font[glyphName] at the defined position with the defined
        fontSize."""
        font = glyph.font

        if fontSize is None:
            fontSize = font.info.unitsPerEm
        s = fontSize/font.info.unitsPerEm

        if xAlign == CENTER:
            x -= (glyph.width or 0)/2*s
        elif xAlign == RIGHT:
            x -= glyph.width*s

        self.save()
        self.fill(fill)
        self.stroke(stroke, w=strokeWidth)
        self.translate(x, y)
        self.scale(s)
        self.drawGlyphPath(glyph)
        self.restore()

    #   I M A G E

    def image(self, path, p=None, alpha=1, pageNumber=None, w=None, h=None,
            scaleType=None):
        """Draws the image. If w or h is defined, scale the image to fit."""
        if p is None:
            p = ORIGIN

        iw, ih = self.imageSize(path)

        if not w and not h:
            w = iw
            h = ih
            sx = sy = 1
        elif scaleType == SCALE_TYPE_FITWH:
            sx = upt(w/iw)
            sy = upt(h/ih)
        elif scaleType == SCALE_TYPE_FITW:
            sx = sy = upt(w/iw)
        elif scaleType == SCALE_TYPE_FITH:
            sx = sy = upt(h/ih)
        else:
            # scaleType in (None, SCALE_TYPE_PROPORTIONAL):
            sx = sy = min(pt(w/iw), upt(h/ih))

        # Else both w and h are defined, scale disproportionally.
        xpt, ypt, = point2D(p)
        self.save()
        self.scale(sx, sy)
        self.translate(xpt/sx, ypt/sy)
        self.b.image(path, (0, 0), alpha=alpha, pageNumber=pageNumber)
        self.restore()

    def ImageObject(self, path=None):
        """Answers an ImageObject that knows about filters. For names
        and parameters of filters see:

        * http://www.drawbot.com/content/image/imageObject.html

        >>> from pagebot import getResourcesPath
        >>> from pagebot import getContext
        >>> context = getContext()
        >>> path = getResourcesPath() + '/images/peppertom_lowres_398x530.png'
        >>> imo = context.getImageObject(path)

        """
        return self.b.ImageObject(path=path)

    def path2ScaledImagePath(self, path, w, h, index=None, exportExtension=None):
        """Answers the path to the scaled image.

        >>> from pagebot import getContext
        >>> context = getContext('DrawBot')
        >>> context.path2ScaledImagePath('/xxx/yyy/zzz/This.Is.An.Image.jpg', 110, 120)
        ('/xxx/yyy/zzz/_scaled/', 'This.Is.An.Image.110x120.0.jpg')

        >>> path, fileName = context.path2ScaledImagePath('/xxx/yyy/zzz/This.Is.An.Image.jpg', 110, 120)
        >>> path in ('/xxx/yyy/zzz/scaled/', '/xxx/yyy/zzz/_scaled/')
        True
        >>> fileName
        'This.Is.An.Image.110x120.0.jpg'
        """
        # /_scaled will be ignored with default .gitignore settings.
        # If docs/images/_scaled need to be committed into Git repo,
        # then remove _scaled from .gitignore.
        cachePath = '%s/%s/' % (path2Dir(path), self.SCALED_PATH)
        fileNameParts = path2Name(path).split('.')

        # If undefined, take the original extension for exporting the cache.
        if not exportExtension:
            exportExtension = fileNameParts[-1].lower()
        cachedFileName = '%s.%dx%d.%d.%s' % ('.'.join(fileNameParts[:-1]), w, h, index or 0, exportExtension)
        return cachePath, cachedFileName

    def scaleImage(self, path, w, h, index=None, showImageLoresMarker=False,
            exportExtension=None, force=False):
        """Scales the image at the path into a new cached image file. Ignore if
        the cache file is already there.

        First create the new file name, depending on the resolution of the
        scaled image.  Note that in DrawBot this scaling and saving should be
        done before any real document/page drawing started, since this proces
        is using DrawBot canvas pages to execute.

        In case the source contains indexed pages, use index to select the
        page. If omitted, the default index is 0 (in DrawBot this also works on
        non-PDF files).

        >>> from pagebot import getResourcesPath
        >>> from pagebot import getContext
        >>> context = getContext('DrawBot')
        >>> path = getResourcesPath() + '/images/peppertom_lowres_398x530.png'
        >>> scaledImagePath = context.scaleImage(path, 300, 400)
        >>> os.path.exists(scaledImagePath)
        True
        >>> scaledImagePath = context.scaleImage(path, 3, 4) # Reall small
        >>> os.path.exists(scaledImagePath)
        True
        """
        # If default _scaled directory does not exist, then create it.
        cachePath, fileName = self.path2ScaledImagePath(path, w, h, index, exportExtension)
        if not os.path.exists(cachePath):
            os.makedirs(cachePath)
        cachedFilePath = cachePath + fileName

        if force or not os.path.exists(cachedFilePath):
            # Clean the drawing stack.
            self.newDrawing()
            self.newPage(w=w, h=h)
            self.image(path, (0, 0), w=w, h=h, pageNumber=index or 0)
            if showImageLoresMarker:
                bs = self.newString('LO-RES',
                        style=dict(font=DEFAULT_FALLBACK_FONT_PATH,
                            fontSize=pt(64), fill=color(0, 1, 1),
                            textFill=color(1, 0, 0)))
                tw, th = bs.size
                self.text(bs, (w/2-tw/2, h/2-th/4))
            self.saveImage(cachedFilePath)

            # Clean the drawing stack again.
            self.newDrawing()
        return cachedFilePath

    def imagePixelColor(self, path, p=None):
        if p is None:
            p = ORIGIN
        ppt = point2D(upt(p))
        return self.b.imagePixelColor(path, ppt)

    def numberOfImages(self, path):
        """Answers the number of images in the file referenced by path."""
        return self.b.numberOfPages(path)

    def translate(self, tx, ty):
        self.b.translate(tx, ty)

    def scale(self, sx=1, sy=None, center=(0, 0)):
        if sy is None:
            sy = sx
        self.b.scale(sx, sy, center=center)

    # System fonts listing, installation, font properties.

    def installedFonts(self, patterns=None):
        """Answers the list of all fonts (name or path) that are installed on
        the OS.

        >>> from pagebot import getContext
        >>> context = getContext()
        >>> installed = context.installedFonts()
        >>> len(installed) > 0
        True
        """
        # In case it is a string, convert to a list.
        if isinstance(patterns, str):
            patterns = [patterns]

        fontNames = []

        for fontName in self.b.installedFonts():
            if not patterns:
                # If no pattern then answer all.
                fontNames.append(fontName)
            else:
                for pattern in patterns:
                    if pattern in fontName:
                        fontNames.append(fontName)
                        break
        return fontNames

    def installFont(self, fontOrName):
        """Install the font in the context. fontOrName can be a Font instance
        (in which case the path is used) or a full font path.

        >>> from pagebot.fonttoolbox.objects.font import findFont
        >>> from pagebot import getContext
        >>> context = getContext()
        >>> installed = context.installedFonts()
        >>> len(installed) > 0
        True
        >>> font = findFont('Roboto-Regular')
        >>> context.installFont(font)
        'Roboto-Regular'
        """
        if hasattr(fontOrName, 'path'):
            fontOrName.info.installedName = self.b.installFont(fontOrName.path)
            return fontOrName.info.installedName
        return self.b.installFont(fontOrName)

    def uninstallFont(self, fontOrName):
        if hasattr(fontOrName, 'path'):
            fontOrName = fontOrName.path
        return self.b.uninstallFont(fontOrName)

    def fontContainsCharacters(self, characters):
        return self.b.fontContainsCharacters(characters)

    def fontContainsGlyph(self, glyphName):
        return self.b.fontContainsGlyph(glyphName)

    def fontFilePath(self):
        return self.b.fontFilePath()

    def listFontGlyphNames(self):
        return self.b.listFontGlyphNames()

    def fontAscender(self):
        return self.b.fontAscender()

    def fontDescender(self):
        return self.b.fontDescender()

    def fontXHeight(self):
        return self.b.fontXHeight()

    def fontCapHeight(self):
        return self.b.fontCapHeight()

    def fontLeading(self):
        return self.b.fontLeading()

    def fontLineHeight(self):
        return self.b.fontLineHeight()

    # Features.

    def openTypeFeatures(self, features):
        """Enables OpenType features and returns the current openType features
        settings. If no arguments are given `openTypeFeatures()` will just
        return the current openType features settings.

        In DrawBot:

            size(1000, 200)
            # create an empty formatted string object
            t = FormattedString()
            # set a font
            t.font("ACaslonPro-Regular")
            # set a font size
            t.fontSize(60)
            # add some text
            t += "0123456789 Hello"
            # enable some open type features
            t.openTypeFeatures(smcp=True, lnum=True)
            # add some text
            t += " 0123456789 Hello"
            # draw the formatted string
            text(t, (10, 80))


        NOTE: signature differs from DrawBot:

        ``def openTypeFeatures(self, *args, **features):``

        >>> from pagebot import getContext
        >>> context = getContext()
        >>> context.newDrawing()
        >>> context.newPage(420, 420)
        >>> context.openTypeFeatures(dict(smcp=True, zero=True))
        """
        self.b.openTypeFeatures(**features)

    def listOpenTypeFeatures(self, fontName=None):
        """Answers the list of opentype features available in the named
        font."""
        return self.b.listOpenTypeFeatures(fontName)

    def fontVariations(self, *args, **axes):
        return self.b.fontVariations(*args, **axes)

    def listFontVariations(self, fontName=None):
        return self.b.listFontVariations(fontName=fontName)

    # TODO
    # Future experiment, making UI/Vanilla layout for apps by PageBot
    # Needs some additional conceptual thinking.

    #   U I  components based on Vanilla API
    def window(self, title=None, x=None, y=None, w=None, h=None, style=None,
        minW=None, maxW=None, minH=None, maxH=None, closable=None, **kwargs):
        """Create and opening a window, using Vanilla.
        """
        """
        FIXME
        >>> from pagebot import getContext
        >>> context = getContext('DrawBot')
        >>> from pagebot.toolbox.units import pt, mm
        >>> window = context.window('My Window', 50, 50, pt(200), mm(50))
        >>> window.open()
        """

        '''
        if x is None:
            x = DEFAULT_WINX
        if y is None:
            y = DEFAULT_WINY
        if w is None:
            w = DEFAULT_WINW
        if h is None:
            h = DEFAULT_WINH
        posSize = upt(x), upt(y), upt(w), upt(h)
        if minW is None and minH is None:
            minSize = None
        else:
            minSize = minW or w, minH or h
        if maxW is None and maxH is None:
            maxSize = None
        else:
            maxSize = maxW or w, maxH or h
        if closable is None:
            closable = True

        return Window(posSize, title=title or 'Untitled',
            minSize=minSize, maxSize=maxSize, closable=closable)
        '''

    def group(self, x=None, y=None, w=None, h=None, **kwargs):
        #return Group((upt(x) or 0, upt(y) or 0, upt(w) or 0, upt(h) or 0))
        pass

    def button(self, title=None, x=None, y=None, w=None, h=None, style=None,
            callback=None, **kwargs):
        """Create a Vanilla button"""
        #return Button((upt(x) or 0, upt(y) or 0, upt(w) or 0, upt(h) or 0),
        #title or 'Button', callback=callback)

    def canvas(self, x=None, y=None, w=None, h=None):
        """Answer an instance of the DrawBot drawing canvas."""
        #return drawBot.ui.drawView.DrawView((upt(x or 0), upt(y or 0), upt(w or 0), upt(h or 0)))

    #   S C R E E N

    def screenSize(self):
        """Answers the current screen size in DrawBot. Otherwise default is to
        do nothing. PageBot function.

        >>> from pagebot import getContext
        >>> context = getContext()
        >>> size = context.screenSize()
        >>> size[0] > 100 and size[1] > 100
        True
        """
        return pt(self.b.sizes().get('screen', None))

if __name__ == '__main__':
    import doctest
    import sys
    sys.exit(doctest.testmod()[0])
