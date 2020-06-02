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
from CoreText import (CTFontDescriptorCreateWithNameAndSize, CGPathAddRect,
        CTFramesetterCreateWithAttributedString, CGPathCreateMutable,
        CTFramesetterCreateFrame, CTFrameGetLines, CTFrameGetLineOrigins,
        CTFontDescriptorCopyAttribute, kCTFontURLAttribute, CGRectMake,
        CTLineGetGlyphRuns, CTRunGetAttributes)
from AppKit import NSFont

import drawBot
from drawBot import Variable

from pagebot.constants import (DEFAULT_FILETYPE, DEFAULT_FONT, DEFAULT_FONT_SIZE,
        DEFAULT_LANGUAGE, DEFAULT_WIDTH, LEFT, RIGHT, CENTER, FILETYPE_PDF,
        FILETYPE_SVG, FILETYPE_PNG, FILETYPE_JPG, FILETYPE_GIF, FILETYPE_MOV,
        SCALE_TYPE_FITWH, SCALE_TYPE_FITW, SCALE_TYPE_FITH,
        DEFAULT_FALLBACK_FONT_PATH, ORIGIN)

# TODO: switch to our own Bézier path format.
#from pagebot.contexts.basecontext.bezierpath import BezierPath
from pagebot.contexts.basecontext.babelstring import BabelString, BabelLineInfo, BabelRunInfo
from pagebot.contexts.basecontext.basecontext import BaseContext
from pagebot.toolbox.color import color, noColor
from pagebot.toolbox.units import pt, upt, point2D, em, units
from pagebot.toolbox.transformer import path2Name, path2Dir
from pagebot.fonttoolbox.objects.font import findFont

# Identifier to make builder hook name. Views will try to call e.build_html()
drawBotBuilder = drawBot
drawBotBuilder.PB_ID = 'drawBot'

class DrawBotContext(BaseContext):
    """DrawBotContext adapts DrawBot functionality to PageBot."""

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
        # calls, similar to function calls in DrawBot scripts.  Builder for
        # this canvas:
        self.b = drawBotBuilder
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
        >>> context.saveImage('_export/PageBotContext-saveDrawing.pdf')

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

    #   T E X T

    def getTextSize(self, bs, w=None, h=None, align=None):
        """Answers the width and height of a BabelString with an
        optional given w or h.
        bs.cs is supposed to contain a DrawBot.FormattedString.
        """
        assert bs.context == self
        if w is not None:
            w = upt(w)
            h = None
        elif h is not None:
            w = None
            h = upt(h0)
        return units(self.b.textSize(bs.cs, width=w, height=h, align=align or LEFT))

    def getTextLines(self, bs, w=None, h=None):
        """Answers the list of BabelLineInfo instances, after rendering it by
        self. By default, w render the full height of the text, so other
        functions (self.overfill)

        >>> from pagebot.toolbox.units import mm, pt, em
        >>> from pagebot.toolbox.loremipsum import loremipsum
        >>> from pagebot import getContext
        >>> from pagebot.fonttoolbox.objects.font import findFont
        >>> context = getContext('DrawBot')
        >>> style = dict(font='PageBot-Regular', fontSize=pt(16), leading=em(1))
        >>> bs = context.newString(loremipsum(), style, w=pt(500))
        >>> bs.tw, bs.th
        (497.89pt, 1216pt)
        >>> lines = bs.lines # Equivalent of context.getTextLines(bs.cs, bs.w)
        >>> lines[2]
        <BabelLineInfo y=43pt>
        >>> lines[-1]
        <BabelLineInfo y=651pt>
        """
        # FIXME: isn't it better to determine lines in BabelRuns?
        # Petr: Then we have to detect all hyphenation ourselves, and going
        # through OSX is much faster. If the context knows how to do a function
        # then let it. Finally it will do the type setting too, unless we are
        # drawing line by line.
        if w is None:
            w = 1000
        if h is None:
            h = 10000


        textLines = []
        wpt, hpt = upt(w, h)
        # Get the FormattedString bs.cs. Let the context create it,
        # if it does not exist.
        attrString = bs.cs.getNSObject()
        setter = CTFramesetterCreateWithAttributedString(attrString)
        path = CGPathCreateMutable()
        CGPathAddRect(path, None, CGRectMake(0, 0, wpt, hpt))
        ctBox = CTFramesetterCreateFrame(setter, (0, 0), path, None)
        ctLines = CTFrameGetLines(ctBox)
        origins = CTFrameGetLineOrigins(ctBox, (0, len(ctLines)), None)

        if origins: # Only if there is content
            # Make origin at top line, not at bottom line, as OSX does.
            offsetY = origins[-1].y - origins[0].y

            for index, ctLine in enumerate(ctLines):
                origin = origins[index]
                x = pt(origin.x)
                y = pt(h-origin.y)

                if y > h:
                    break

                lineInfo = BabelLineInfo(x, y, ctLine, self)
                textLines.append(lineInfo)

                for ctRun in CTLineGetGlyphRuns(ctLine):
                    attributes = CTRunGetAttributes(ctRun)
                    c = attributes['NSColor']
                    fontName = attributes['NSFont'].fontDescriptor()['NSFontNameAttribute']
                    font = findFont(fontName) or findFont(DEFAULT_FONT)
                    paragraph = attributes['NSParagraphStyle']
                    #glyphOrder = font.ttFont.getGlyphOrder()
                    style = dict(
                        font=font,
                        fontSize=pt(attributes['NSFont'].pointSize()),
                        leading=pt(paragraph.lineHeightMultiple()),
                        baselineShift=pt(attributes['NSBaselineOffset']),
                        language=attributes['NSLanguage'],
                        textFill=color(r=c.redComponent(), g=c.greenComponent(),
                            b=c.blueComponent(), a=c.alphaComponent()),
                        xTextAlign={0:LEFT, 1:RIGHT, 2:CENTER}.get(paragraph.alignment()),
                        firstLineIndent=pt(paragraph.firstLineHeadIndent()),
                        indent=pt(paragraph.headIndent()),
                        tailIndent=pt(paragraph.tailIndent()),
                        paragraphBottomSpacing=pt(paragraph.paragraphSpacing()),
                        paragraphTopSpacing=pt(paragraph.paragraphSpacingBefore()),
                        # https://developer.apple.com/documentation/uikit/nsparagraphstyle
                        # paragraph.maximumLineHeight()
                        # paragraph.minimumLineHeight()
                        # paragraph.lineSpacing()
                        # paragraph.tabStops()
                        # paragraph.defaultTabInterval()
                        # paragraph.textBlocks()
                        # paragraph.textLists()
                        # paragraph.lineBreakMode()
                        # paragraph.hyphenationFactor()
                        # paragraph.tighteningFactorForTruncation()
                        # paragraph.allewsDefaultTighteningForTruncation()
                        # paragraph.headerLevel()
                    )
                    #for uCode in CTRunGetGlyphs(ctRun, (0, CTRunGetGlyphCount(ctRun)), None):
                    #    s += glyphOrder[uCode]
                    # Reconstruct the CTLine runs back into a styled BabelString.
                    # Not that this string can only be used as reference (e.g. to determine the
                    # fontSize(s) in the first line or to find the pattern of markers.
                    # The reconstructed string cannot be used for display, as it is missing
                    # important style parameters, such as OT-feature settings.
                    # Hack for now to find the string in repr-string if self._ctLine.
                    s = ''
                    for index, part in enumerate(str(ctRun).split('"')[1].replace('\\n', '').split('\\u')):
                        if index == 0:
                            s += part
                        elif len(part) >= 4:
                            s += chr(int(part[0:4], 16))
                    lineInfo.runs.append(BabelRunInfo(s, style, context=self, cRun=ctRun))

        return textLines

    def fromBabelString(self, bs):
        """Convert the BabelString into a DrawBot FormattedString

        >>> from pagebot.contexts import getContext
        >>> from pagebot.toolbox.units import pt, em
        >>> from pagebot.document import Document
        >>> from pagebot.elements import *
        >>> context = getContext('DrawBot')
        >>> style = dict(font='PageBot-Regular', fontSize=pt(100), leading=em(1))
        >>> bs = BabelString('Hkpx', style, context=context)
        >>> bs.textStrokeWidth = pt(4)
        >>> bs.textStroke = (1, 0, 0)
        >>> tw, th = bs.textSize
        >>> tw, th
        (209.7pt, 100pt)
        >>> fs = context.fromBabelString(bs) # DrawBot.FormattedString
        >>> fs, fs.__class__.__name__
        (Hkpx, 'FormattedString')
        >>> style = dict(font='PageBot-Regular', fontSize=pt(30), leading=em(1))
        >>> bs = context.newString('Hkpx'+chr(10)+'Hkpx', style)
        >>> bs.textStrokeWidth = pt(4)
        >>> bs.textStroke = (1, 0, 0)
        >>> doc = Document(w=tw+50, h=th+100, context=context)
        >>> e = newText(bs, x=20, y=120, parent=doc[1])
        >>> doc.export('_export/DrawBotContext-fromBabelString.pdf')
        """
        fs = self.b.FormattedString()

        for run in bs.runs:
            fsStyle, hyphenation = run.getFSStyle()

            # TODO: take care of hyphenation in BabelStrings or during draw.
            #self.b.hyphenation(hyphenation)
            fs.append(run.s, **fsStyle)
        return fs

    def text(self, bs, p, align=None):
        self.b.text(bs.cs, p, align=align)

    def textBox(self, bs, box):
        self.b.textBox(bs.cs, box, align=None)

    def textSize(self, bs, w=None, h=None):
        """Answers the width and height of the native @fs formatted string
        with an optional given w or h.

        >>> from pagebot.document import Document
        >>> from pagebot.contexts import getContext
        >>> from pagebot.elements import *
        >>> context = getContext('DrawBot')
        >>> # Make the string, we can adapt the document/page size to it.
        >>> style = dict(font='PageBot-Regular', leading=em(1), fontSize=pt(100))
        >>> bs = context.newString('Hkpx', style)
        >>> tw, th = context.textSize(bs) # Same as bs.textSize, Show size of the text box, with baseline.
        >>> (tw, th) == bs.textSize
        True
        >>> m = 50
        >>> doc = Document(w=tw+2*m, h=th+m, context=context)
        >>> page = doc[1]
        >>> tw, th, bs.fontSize, bs.ascender, bs.descender
        (209.7pt, 100pt, 100pt, 74.8pt, -25.2pt)
        >>> e = newText(bs, x=m, y=m, parent=page)
        >>> e = newRect(x=m, y=m+bs.descender, w=tw, h=th, fill=None, stroke=(0, 0, 1), strokeWidth=0.5, parent=page)
        >>> e = newLine(x=m, y=m, w=tw, h=0, fill=None, stroke=(0, 0, 1), strokeWidth=0.5, parent=page)
        >>> e = newLine(x=m, y=m+bs.xHeight, w=tw, h=0, fill=None, stroke=(0, 0, 1), strokeWidth=0.5, parent=page)
        >>> e = newLine(x=m, y=m+bs.capHeight, w=tw, h=0, fill=None, stroke=(0, 0, 1), strokeWidth=0.5, parent=page)
        >>> doc.export('_export/DrawBotContext-textSize.pdf')

        >>> bs = context.newString('Hkpx', style)
        >>> tw, th = context.textSize(bs, w=bs.w, h=bs.h) # Answering point units. Same as bs.textSize
        >>> tw.rounded, th.rounded
        (210pt, 100pt)
        >>> bs.fontSize *= 0.5 # Same as bs.runs[0].style['fontSize'] *= 0.5 to scale by 50%
        >>> tw, th = context.textSize(bs, w=bs.w, h=bs.h) # Render to FormattedString for new size.
        >>> tw.rounded, th.rounded
        (105pt, 50pt)
        >>>
        """
        assert isinstance(bs, BabelString)

        if w is not None:
            return pt(self.b.textSize(bs.cs, width=w, align=LEFT))

        if h is not None:
            return pt(self.b.textSize(bs.cs, height=h, align=LEFT))

        return pt(self.b.textSize(bs.cs, align=LEFT))

    #   P A T H
    #
    #   Function that work on the current running path stored in self._bezierpath
    #

    def newPath(self):
        # TODO: use our own Bézier path.
        self._bezierpath = self.b.BezierPath()
        #self._bezierpath = BezierPath()
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
        """Use the Bézier path flatten function. Answers None if the flattened
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
        >>> from pagebot.fonttoolbox.objects.font import findFont
        >>> from pagebot import getContext
        >>> context = getContext('DrawBot')
        >>> # Does not exist.
        >>> findFont('Aaa.ttf') is None
        True
        >>> font = findFont('Amstelvar-Roman-VF')
        >>> os.path.exists(font.path)
        True
        >>> context.fontPath2FontName(font.path)
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
            strokeWidth=0, fontSize=None, xTextAlign=CENTER):
        """Draw the font[glyphName] at the defined position with the defined
        fontSize."""
        font = glyph.font

        if fontSize is None:
            fontSize = font.info.unitsPerEm
        s = fontSize/font.info.unitsPerEm

        if xTextAlign == CENTER:
            x -= (glyph.width or 0)/2*s
        elif xTextAlign == RIGHT:
            x -= glyph.width*s

        self.save()
        self.fill(fill)
        self.stroke(stroke, w=strokeWidth)
        self.translate(x, y)
        self.scale(s)
        self.drawGlyphPath(glyph)
        self.restore()

    #   I M A G E

    def image(self, path=None, p=None, alpha=1, pageNumber=None,
            w=None, h=None, scaleType=None, clipPath=None):
        """Draws the image. If w or h is defined, scale the image to fit."""
        if p is None:
            p = ORIGIN

        iw, ih = self.imageSize(path or imo.path)

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
        with self.b.savedState():
            if clipPath is not None:
                self.b.clipPath(clipPath)
            self.scale(sx, sy)
            self.translate(xpt/sx, ypt/sy)
            self.b.image(path, (0, 0), alpha=alpha, pageNumber=pageNumber)
        self.restore()
        # For debugging, show the clipPath as opaque rectangle.
        #if clipPath is not None:
        #    self.b.fill(0, 1, 0, 0.4)
        #    self.b.drawPath(clipPath)

    def getImageObject(self, path=None):
        """Answers an ImageObject that knows about filters. For names
        and parameters of filters see:

        * http://www.drawbot.com/content/image/imageObject.html

        >>> from pagebot.filepaths import getResourcesPath
        >>> from pagebot import getContext
        >>> context = getContext('DrawBot')
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

        >>> from pagebot.filepaths import getResourcesPath
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

    #  User interface.

    def group(self, x=None, y=None, w=None, h=None, **kwargs):
        #return Group((upt(x) or 0, upt(y) or 0, upt(w) or 0, upt(h) or 0))
        pass

    def button(self, title=None, x=None, y=None, w=None, h=None, style=None,
            callback=None, **kwargs):
        """Create a Vanilla button"""
        #return Button((upt(x) or 0, upt(y) or 0, upt(w) or 0, upt(h) or 0),
        #title or 'Button', callback=callback)

    # TODO
    # Future experiment, making UI / Vanilla layout for apps by PageBot
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

    def canvas(self, x=None, y=None, w=None, h=None):
        """Answer an instance of the DrawBot drawing canvas."""
        #return drawBot.ui.drawView.DrawView((upt(x or 0), upt(y or 0), upt(w or 0), upt(h or 0)))

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

    def Variable(self, variables, workSpace):
        """Offers interactive global value manipulation in DrawBot. Should be
        ignored in other contexts.

        Variable is a DrawBot context global, used to make simple UI with
        controls on input parameters."""
        Variable(variables, workSpace)

if __name__ == '__main__':
    import doctest
    import sys
    sys.exit(doctest.testmod()[0])
