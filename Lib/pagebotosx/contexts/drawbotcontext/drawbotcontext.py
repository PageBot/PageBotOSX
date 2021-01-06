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
from drawBot.context.baseContext import BezierPath

from pagebot.constants import (DEFAULT_FILETYPE, DEFAULT_FONT, LEFT, RIGHT,
        CENTER, FILETYPE_PDF, FILETYPE_SVG, FILETYPE_PNG, FILETYPE_JPG,
        FILETYPE_GIF, FILETYPE_MOV, SCALE_TYPE_FITWH, SCALE_TYPE_FITW,
        SCALE_TYPE_FITH, DEFAULT_FALLBACK_FONT_PATH, ORIGIN, EXPORT)
from pagebot.contexts.basecontext.babelstring import BabelString
from pagebot.contexts.basecontext.babelrun import BabelLineInfo, BabelRunInfo
from pagebot.contexts.basecontext.basecontext import BaseContext
#from pagebot.contexts.basecontext.basebezierpath import BaseBezierPath
from pagebot.toolbox.color import color #, noColor
from pagebot.toolbox.units import pt, upt, point2D, units
from pagebot.toolbox.transformer import path2Name, path2Dir
from pagebot.fonttoolbox.objects.font import findFont

# Identifier to make builder hook name. Views will try to call e.build_html()
drawBotBuilder = drawBot
drawBotBuilder.PB_ID = 'drawBot'

class DrawBotContext(BaseContext):
    """DrawBotContext adapts DrawBot functionality to PageBot."""
    # TODO: switch entirely to our own Bézier path format.

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
        >>> context = DrawBotContext()
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

        >>> context = DrawBotContext()
        >>> context.newDrawing()
        """
        self.b.newDrawing()

    def endDrawing(self, doc=None):
        """
        >>> context = DrawBotContext()
        >>> context.endDrawing()
        """
        self.b.endDrawing()


    # Saving / export.

    def saveDrawing(self, path, multiPage=None):
        """Save the current image as path, rendering depending on the
        extension. In case the path starts with "_export", optionally creates
        directories if they don't exist yet.

        >>> context = DrawBotContext()
        >>> context.saveImage('_export/PageBotContext-saveDrawing.pdf')
        """
        #if not multiPage:
        #    multiPage = True

        self.checkExportPath(path)

        if path.lower().endswith('.mov'):
            self.b.saveImage(path)
        else:
            self.b.saveImage(path, multipage=multiPage)

    saveImage = saveDrawing

    def export(self, fileName, folderName=None, extension=None):
        """Saves file to filename with default folder name and extension."""
        if not folderName:
            folderName = EXPORT
        if not extension:
            extension = 'pdf'

        path = '%s/%s.%s' % (folderName, fileName, extension)
        self.saveImage(path)

    def getDrawing(self):
        """Returns a PDF document of the current state.


        FIXME: should return a drawing object, need separate function for PDF.
        """
        return self.b.pdfImage()

    def setStyles(self, styles):
        pass

    # Magic variables.

    def _get_width(self):
        return self.b.width()

    def _get_height(self):
        return self.b.height()

    def sizes(self, paperSize=None):
        return self.b.sizes(paperSize=paperSize)

    def pageCount(self):
        return self.b.pageCount()

    # Public callbacks.

    def setSize(self, width, height=None):
        # Same as setSize?
        return self.b.size(width, height=height)

    def newPage(self, w=None, h=None, doc=None, **kwargs):
        """Creates a new drawbot page.

        >>> from pagebot.toolbox.units import px
        >>> from pagebot import getContext
        >>> context = getContext()
        >>> context.newPage(pt(100), pt(100))
        >>> context.newPage(100, 100)
        """
        if doc is not None:
            w = w or doc.w
            h = h or doc.h
        wpt, hpt = upt(w, h)
        self.b.newPage(wpt, hpt)

    # Graphic state.

    def save(self):
        self.b.save()

    def restore(self):
        self.b.restore()

    #   T E X T

    def getTextLines(self, bs, w=None, h=None):
        """Answers the list of BabelLineInfo instances, after rendering it by
        self. By default, w render the full height of the text, so other
        functions (self.overfill)

        >>> from pagebot.toolbox.units import mm, pt, em
        >>> from pagebot.toolbox.loremipsum import loremIpsum
        >>> from pagebot.fonttoolbox.objects.font import findFont
        >>> context = DrawBotContext()
        >>> style = dict(font='PageBot-Regular', fontSize=pt(16), leading=em(1))
        >>> bs = context.newString(loremIpsum(), style, w=pt(500))
        >>> bs.tw, bs.th
        (497.89pt, 1216pt)
        >>> lines = bs.lines # Equivalent of context.getTextLines(bs.cs, bs.w)
        >>> line = lines[2]
        >>> #43 <= line.y.pt <= 44
        >>> #line.y.pt
        #1173
        >>> line = lines[-1]
        >>> #1211 <= line.y.pt <= 1212
        >>> #line.y.pt
        #5
        """
        w = w or bs.tw
        h = h or bs.th
        assert w
        assert h
        textLines = []
        wpt, hpt = upt(w, h)

        # bs.x and bs.y don't exist yet.
        box = (0, 0, w, h)

        '''
        baselines = self.b.textBoxBaselines(bs.cs, box)
        # We can also get the baseline coordinates from textBoxBaslines, do we
        # really need to deconstruct CoreText runs?

        for x, y in baselines:
            #lineInfo = BabelLineInfo(x, y, None, self)
            #textLines.append(lineInfo)
        '''

        # Get the FormattedString bs.cs. Let the context create it,
        # if it does not exist.
        attrString = bs.cs.getNSObject()
        setter = CTFramesetterCreateWithAttributedString(attrString)
        path = CGPathCreateMutable()
        CGPathAddRect(path, None, CGRectMake(0, 0, wpt, hpt))
        ctBox = CTFramesetterCreateFrame(setter, (0, 0), path, None)
        ctLines = CTFrameGetLines(ctBox)
        origins = CTFrameGetLineOrigins(ctBox, (0, len(ctLines)), None)

        if origins:
            # Make origin at top line, not at bottom line, as OSX does.

            for index, ctLine in enumerate(ctLines):
                origin = origins[index]
                x = pt(origin.x)
                y = pt(h - origin.y)
                #y = pt(origin.y)

                #if y > h:
                #    break

                lineInfo = BabelLineInfo(x, y, ctLine, self)
                textLines.append(lineInfo)

                for ctRun in CTLineGetGlyphRuns(ctLine):
                    style = self.getStyleFromRun(ctRun)
                    # Reconstruct the CTLine runs back into a styled BabelString.
                    # Note that this string can only be used as reference (e.g. to
                    # determine the fontSize(s) in the first line or to find the
                    # pattern of markers. The reconstructed string cannot be
                    # used for display, as it is missing important style
                    # parameters, such as OT-feature settings. Hack for now to
                    # find the string in repr-string if self._ctLine.
                    # for uCode in CTRunGetGlyphs(ctRun, (0, CTRunGetGlyphCount(ctRun)), None):
                    #    s += glyphOrder[uCode]
                    s = ''
                    splitString = str(ctRun).split('"')[1].replace('\\n', '').split('\\u')
                    for index, part in enumerate(splitString):
                        if index == 0:
                            s += part
                        elif len(part) >= 4:
                            s += chr(int(part[0:4], 16))

                    babelRunInfo = BabelRunInfo(s, style, context=self, cRun=ctRun)
                    lineInfo.runs.append(babelRunInfo)

        return textLines

    def getStyleFromRun(self, ctRun):
        """Reverse-engineers typographic elements from a CoreText Run."""
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
        attributes = CTRunGetAttributes(ctRun)
        c = attributes['NSColor']
        textFill = color(r=c.redComponent(),
                        g=c.greenComponent(),
                        b=c.blueComponent(),
                        a=c.alphaComponent())
        fontName = attributes['NSFont'].fontDescriptor()['NSFontNameAttribute']
        font = findFont(fontName) or findFont(DEFAULT_FONT)
        paragraph = attributes['NSParagraphStyle']

        absLeading = pt(paragraph.maximumLineHeight())
        fontSize = pt(attributes['NSFont'].pointSize())
        leading = absLeading / fontSize
        baselineShift = pt(attributes['NSBaselineOffset'])
        language = attributes['NSLanguage']
        xTextAlign = {0: LEFT, 1: RIGHT, 2: CENTER}.get(paragraph.alignment())
        firstLineIndent = pt(paragraph.firstLineHeadIndent())
        indent = pt(paragraph.headIndent())
        tailIndent = pt(paragraph.tailIndent())
        paragraphBottomSpacing = pt(paragraph.paragraphSpacing())
        paragraphTopSpacing = pt(paragraph.paragraphSpacingBefore())
        #glyphOrder = font.ttFont.getGlyphOrder()

        style = dict(
            font=font,
            fontSize=fontSize,
            leading=leading,
            baselineShift=baselineShift,
            language=language,
            textFill=textFill,
            xTextAlign = xTextAlign,
            firstLineIndent=firstLineIndent,
            indent=indent,
            tailIndent=tailIndent,
            paragraphBottomSpacing=paragraphBottomSpacing,
            paragraphTopSpacing=paragraphTopSpacing,
        )

        return style

    def fromBabelString(self, bs):
        """Convert the BabelString into a DrawBot FormattedString

        >>> from pagebot.toolbox.units import pt, em
        >>> from pagebot.document import Document
        >>> from pagebot.elements import *
        >>> context = DrawBotContext()
        >>> style = dict(font='PageBot-Regular', fontSize=pt(100), leading=em(1))
        >>> from pagebot.contexts.basecontext.babelstring import BabelString
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

    def text(self, s, p, align=None):
        """
        >>> context = DrawBotContext()
        >>> s = 'test'
        >>> p = (0, 0)
        >>> context.text(s, p)
        >>> bs = context.newString(s)
        >>> context.text(bs, p)
        """

        if isinstance(s, str):
            s = self.newString(s)
        assert isinstance(s, BabelString)

        if isinstance(p, BezierPath):
            self.textPath(s, p, align=align)
        else:
            self.b.text(s.cs, p, align=align)

    def textBox(self, s, box):
        """
        >>> context = DrawBotContext()
        >>> s = 'test'
        >>> box = (0, 0, 100, 100)
        >>> context.textBox(s, box)
        >>> bs = context.newString(s)
        >>> context.textBox(bs, box)
        """

        if isinstance(s, str):
            s = self.newString(s)
        assert isinstance(s, BabelString)
        self.b.textBox(s.cs, box, align=None)

    def textPath(self, s, p, align=None):
        """
        >>> from pagebot.fonttoolbox.objects.font import findFont
        >>> context = DrawBotContext()
        >>> f = findFont('Roboto-Regular')
        >>> g = f['H']
        >>> s = 'test'
        >>> path = context.getGlyphPath(g)
        >>> context.textPath(s, path)
        """
        if isinstance(s, str):
            s = self.newString(s)
        assert isinstance(s, BabelString)
        p.text(s.cs) # font='', fontSize='')
        self.b.fill(0)
        self.b.textBox(s.cs, p)

    def textSize(self, bs, w=None, h=None, align=None, ascDesc=False):
        """Answers the width and height of the native @fs formatted string with
        an optional given w or h.

        >>> from pagebot.document import Document
        >>> from pagebot.elements import *
        >>> from pagebot.toolbox.units import em
        >>> context = DrawBotContext()
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
        #assert isinstance(bs, BabelString)
        assert bs.context == self

        if w is not None:
            w = upt(w)
            h = None
        elif h is not None:
            w = None
            h = upt(h)
        else:
            w = bs.w
            #h = bs.h

        if not ascDesc:
            return units(self.b.textSize(bs.cs, width=w, height=h, align=align or LEFT))
        else:
            # FIXME: runs into recursion error in case of multiple lines, for
            # now setting Flat counterpart to ascDesc=False.
            # textSize -> bs.lines -> getTextLines -> testSize
            textHeight = 0
            for line in bs.lines:
                lineHeight = 0
                for run in  line.runs:

                    size = run.style['fontSize']
                    font = run.style['font']
                    upem = font.upem
                    runHeight = size * (font.info.typoAscender - font.info.typoDescender) / upem
                    lineHeight = max(lineHeight, runHeight)
                textHeight += lineHeight

            textWidth, _ = units(self.b.textSize(bs.cs, width=w, height=h, align=align or LEFT))
            return (textWidth, textHeight)



    #   P A T H
    #
    #   Function that work on the current running path stored in self._bezierpath
    #

    def newPath(self):
        """
        >>> context = DrawBotContext()
        >>> path = context.newPath()
        """
        # TODO: use our own Bézier path.
        self._bezierpath = self.b.BezierPath()
        #self._bezierpath = BaseBezierPath()
        return self.bezierpath

    # Glyphs.

    def getGlyphPath(self, glyph, p=None, path=None):
        """Answers the DrawBot path. Allow optional position offset and path,
        in case we do recursive component drawing.

        >>> from pagebot.fonttoolbox.objects.font import findFont
        >>> context = DrawBotContext()
        >>> f = findFont('Roboto-Regular')
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
            # TODO: quadTo()

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
                # Recursively for components.
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
        """
        >>> from pagebot.fonttoolbox.objects.font import findFont
        >>> context = DrawBotContext()
        >>> f = findFont('Roboto-Regular')
        >>> g = f['H']
        >>> path = context.getGlyphPath(g)
        >>> path = context.getFlattenedPath(path)
        """
        return self.bezierPathByFlatteningPath(path=path)

    def getFlattenedContours(self, path=None):
        """Answers the flattened Bézier path as  a contour list [contour,
        contour, ...] where contours are lists of point2D() points.

        >>> from pagebot.fonttoolbox.objects.font import findFont
        >>> context = DrawBotContext()
        >>> f = findFont('Roboto-Regular')
        >>> g = f['H']
        >>> path = context.getGlyphPath(g)
        >>> path = context.getFlattenedContours(path)
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

    def onBlack(self, p, path=None):
        """Answers if the single point (x, y) is on black.

        >>> from pagebot.fonttoolbox.objects.font import findFont
        >>> context = DrawBotContext()
        >>> f = findFont('Roboto-Regular')
        >>> g = f['H']
        >>> path = context.getGlyphPath(g)
        >>> p = (0, 0)
        >>> context.onBlack(p, path=path)
        False
        >>> # TODO: find out coordinate that is inside 'H'.
        >>> #context.onBlack((120, 10), path=path)
        """
        if path is None:
            path = self.bezierpath
        p = point2D(p)
        return path._path.containsPoint_(p)


    # Path drawing behavior.

    def strokeWidth(self, w=0.5):
        """Set the current stroke width.

        >>> from pagebot.toolbox.units import pt, mm
        >>> context = DrawBotContext()
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
        >>> context = DrawBotContext()
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

    #   I M A G E

    def image(self, path=None, p=None, alpha=1, pageNumber=None,
            w=None, h=None, scaleType=None, clipPath=None):
        """Draws the image. If w or h is defined, scale the image to fit."""
        if p is None:
            p = ORIGIN

        iw, ih = self.imageSize(path)
        assert iw, ih

        if not w and not h:
            w = iw
            h = ih
            sx = sy = 1
        elif scaleType == SCALE_TYPE_FITWH:
            sx = upt(w / iw)
            sy = upt(h / ih)
        elif scaleType == SCALE_TYPE_FITW:
            sx = sy = upt(w / iw)
        elif scaleType == SCALE_TYPE_FITH:
            sx = sy = upt(h / ih)
        else:
            # scaleType in (None, SCALE_TYPE_PROPORTIONAL):
            assert w, h
            sx = sy = min(pt(w / iw), upt(h / ih))

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
        >>> context = DrawBotContext()
        >>> path = getResourcesPath() + '/images/peppertom.png'
        >>> imo = context.getImageObject(path)

        """
        return self.b.ImageObject(path=path)

    def path2ScaledImagePath(self, path, w, h, index=None, exportExtension=None):
        """Answers the path to the scaled image.

        >>> context = DrawBotContext()
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
        >>> context = DrawBotContext()
        >>> path = getResourcesPath() + '/images/peppertom.png'
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

        >>> context = DrawBotContext()
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
        >>> context = DrawBotContext()
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

        >>> context = DrawBotContext()
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
        >>> context = DrawBotContext()
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

        >>> context = DrawBotContext()
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
