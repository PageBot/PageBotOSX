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
        CTLineGetGlyphRuns, CTRunGetAttributes, CTRunGetGlyphCount,
        CTRunGetGlyphs)
from AppKit import NSFont

import drawBot
from drawBot import Variable

from pagebot.constants import *
#from pagebot.contexts.basecontext.bezierpath import BezierPath
from pagebot.contexts.basecontext.babelstring import BabelString
from pagebot.contexts.basecontext.babeltext import BabelText
from pagebot.contexts.basecontext.basecontext import BaseContext
from pagebot.toolbox.color import color, noColor
from pagebot.toolbox.units import pt, upt, point2D
from pagebot.toolbox.transformer import path2Name, path2Dir
from drawBot import Variable
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

    #   V A R I A B L E

    def Variable(self, variables, workSpace):
        """Offers interactive global value manipulation in DrawBot. Should be
        ignored in other contexts.

        Variable is a DrawBot context global, used to make simple UI with
        controls on input parameters."""
        Variable(variables, workSpace)

    #   D R A W I N G

    def bluntCornerRect(self, x, y, w, h, offset=5):
        """Draw a rectangle in the canvas. This method is using the Bézier path
        to draw on.

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
        """Draw a rectangle in the canvas. This method is using the Bézier path
        as path to draw on.

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

    def textLines(self, bs, w=None, h=None):
        """Answers the list of BabelLines. Key is y position of
        the line.

        >>> from pagebot.toolbox.units import mm, pt, em
        >>> from pagebot.toolbox.lorumipsum import lorumipsum
        >>> from pagebot import getContext
        >>> from pagebot.fonttoolbox.objects.font import findFont
        >>> context = getContext('DrawBot')
        >>> font = findFont('PageBot-Regular')
        >>> style = dict(font=font, fontSize=pt(12), leading=em(1))
        >>> bs = context.newString(lorumipsum(False), style)
        >>> textLines = context.textLines(bs, w=300)
        >>> textLines[:2]
        [<BabelLine #0 y=8pt $Lorem ipsu...$>, <BabelLine #1 y=20pt $sapien tem...$>]
        >>> textLines[-1]
        <BabelLine #94 y=1136pt $magna ulla...$>
        >>> textLines[0].bs
        $Lorem ipsu...$
        >>> textLines[0].bs.runs
        [<BabelRun "Lorem ipsu...">]
        """
        if w is None:
            if bs.e is None:
                w = 500
            else:
                w = bs.e.w # Take the width of the references element.
        if h is None:
            h = XXH # Infinite length if not defined

        fs = self.fromBabelString(bs) # Answers a DrawBot.FormattedString
        wpt, hpt = upt(w, h)
        attrString = fs.getNSObject()
        setter = CTFramesetterCreateWithAttributedString(attrString)
        path = CGPathCreateMutable()
        CGPathAddRect(path, None, CGRectMake(0, 0, wpt, hpt))
        ctBox = CTFramesetterCreateFrame(setter, (0, 0), path, None)
        ctLines = CTFrameGetLines(ctBox)
        origins = CTFrameGetLineOrigins(ctBox, (0, len(ctLines)), None)

        textLines = []

        # Make origin at top line, not at bottom line, as OSX does.
        offsetY = origins[-1].y - origins[0].y

        for index, ctLine in enumerate(ctLines):
            bs = self.newString()
            origin = origins[index]
            babelLine = BabelLine(bs, x=origin.x, y=XXH-origin.y, index=index)
            textLines.append(babelLine)

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
                    xAlign={0:LEFT, 1:RIGHT, 2:CENTER}.get(paragraph.alignment()),
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
                # Hack for now to find the string in repr-string if self._ctLine.
                s = ''
                for index, part in enumerate(str(ctRun).split('"')[1].replace('\\n', '').split('\\u')):
                    if index == 0:
                        s += part
                    elif len(part) >= 4:
                        s += chr(int(part[0:4], 16))
                bs.add(s, style)

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
        >>> tw, th = context.textSize(bs) # Same as bs.textSize
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
            # Instead of using e.g. bs.tracking, we need to process the
            # styles of all runs, not just the last one.
            style = run.style
            # DrawBot-OSX, setting the hyphenation is global, before a FormattedString is created.
            self.b.hyphenation(style.get('hyphenation', False))
            font = findFont(style.get('font', DEFAULT_FONT))
            if font is None:
                fontPath = DEFAULT_FONT
            else:
                fontPath = font.path
            fontSize = style.get('fontSize', DEFAULT_FONT_SIZE)
            leading = style.get('leading', 0) or DEFAULT_LEADING
            fsStyle = dict(
                font=fontPath,
                fontSize=upt(fontSize),
                lineHeight=upt(leading, base=fontSize),
                align=style.get('xAlign', LEFT),
                tracking=upt(style.get('tracking', 0), base=fontSize),
                strokeWidth=upt(style.get('strokeWidth')),
                baselineShift=upt(style.get('baselineShift'), base=fontSize),
                language=style.get('language', DEFAULT_LANGUAGE),
                indent=upt(style.get('indent', 0), base=fontSize),
                tailIndent=upt(style.get('tailIndent', 0), base=fontSize),
                firstLineIndent=upt(style.get('firstLineIndent', 0), base=fontSize),
                paragraphTopSpacing=upt(style.get('paragraphBottomSpacing', 0), base=fontSize),
                paragraphBottomSpacing=upt(style.get('paragraphBottomSpacing', 0), base=fontSize),
                underline={True:'single', False:None}.get(style.get('underline', False)),
            )
            if 'textFill' in style:
                textFill = style['textFill']
                if textFill is not None:
                    textFill = color(textFill)
                fsStyle['fill'] = textFill.rgba
            if 'textStroke' in style:
                textStroke = style['textStroke']
                if textStroke is not None:
                    textStroke = color(textStroke)
                fsStyle['stroke'] = textStroke.rgba
            if 'openTypeFeatures' in style:
                fsStyle['openTypeFeatures'] = style['openTypeFeatures']
            if 'fontVariations' in style:
                fsStyle['fontVariantions'] = style['fontVariations']
            if 'tabs' in style:
                tabs = [] # Render the tab values to points.
                for tx, alignment in style.get('tabs', []):
                    tabs.append((upt(tx, base=fontSize), alignment))
                fsStyle['tabs'] = tabs

            # In case there is an error in these parameters, DrawBot ignors all.
            #print('FS-style attributes:', run.s, fontPath,
            #    upt(fontSize), upt(leading, base=fontSize),
            #    textColor.rgba, align)
            fs.append(run.s, **fsStyle)
        return fs

    def text(self, bs, p):
        """Draws the s text string at position p.

        >>> from pagebot.contexts import getContext
        >>> from pagebot.toolbox.units import pt, em
        >>> from pagebot.document import Document
        >>> from pagebot.elements import *
        >>> context = getContext('DrawBot')
        >>> style = dict(font='PageBot-Regular', fontSize=pt(100), leading=em(1))
        >>> bs = BabelString('Hkpx'+chr(10)+'Hkpx', style, context=context)
        >>> context.text(bs, (100, 100))

        """
        assert isinstance(bs, (str, BabelString)),\
            'DrawBotContext.text needs str or BabelString: %s' % (bs.__class__.__name__)
        fs = self.fromBabelString(bs)
        self.b.text(fs, point2D(upt(p)))

    def XXXtextBox(self, bs, r=None, clipPath=None, align=None):
        """Draws the bs BabelString in rectangle r.

        """

        """
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
        >>> tb = context.textBox(bs, r=(100, 450, 200, 300))
        """
        assert isinstance(bs, BabelString)

        tb = None

        fs = self.fromBabelString(bs)
        if clipPath is not None:
            box = clipPath.bp
            tb = self.b.textBox(fs, clipPath.bp)
        elif isinstance(r, (tuple, list)):
            # Renders rectangle units to value tuple.
            xpt, ypt, wpt, hpt = upt(r)
            box = (xpt, ypt, wpt, hpt)
            tb = self.b.textBox(fs, box, align=None)
        else:
            msg = '%s.textBox has no box or clipPath defined' % self.__class__.__name__
            raise ValueError(msg)

        return tb

    def textOverflow(self, bs, box, align=None):
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
        756
        """
        if isinstance(bs, str):
            return self.b.textOverflow(bs, box, align=align) # Plain string

        # Assume here it's a BabelString, convert to DrawBot.FormattedString
        # and let that render by DrawBot in the given frame.
        overflow = self.b.textOverflow(s.s, box, align=align)
        #bs = self.newString('')
        #bs.s = overflow
        return overflow

    def textBoxBaselines(self, txt, box, align=None):
        return self.b.textBoxBaselines(txt, box, align=align)

    def textSize(self, bs, w=None, h=None):
        """Answers the width and height of the formatted string with an
        optional given w or h.

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
        >>> tw, th = context.textSize(bs) # Answering point units.
        >>> tw.rounded, th.rounded
        (210pt, 100pt)
        >>> bs.fontSize *= 0.5 # Same as bs.runs[0].style['fontSize'] *= 0.5 to scale by 50%
        >>> tw, th = context.textSize(bs) # Render to FormattedString for new size.
        >>> tw.rounded, th.rounded
        (105pt, 50pt)
        >>>
        """
        if w is None: # If not defined, try to the use the width of referenced element.
            if bs.e is not None:
                w = bs.e.w
        if h is None:
            if bs.e is not None:
                h = bs.e.h
        fs = self.fromBabelString(bs)
        return pt(self.b.textSize(fs, width=w, height=h, align=LEFT))

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