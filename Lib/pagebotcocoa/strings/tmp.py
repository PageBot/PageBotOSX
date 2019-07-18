
'''
def getTextLines(txt, box):
    """Answers a list of (x,y) positions of all line starts in the box. This
    function may become part of standard DrawBot in the near future."""
    x, y, w, h = box
    attrString = txt.getNSObject()
    setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
    path = Quartz.CGPathCreateMutable()
    Quartz.CGPathAddRect(path, None, Quartz.CGRectMake(x, y, w, h))
    box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)
    ctLines = CoreText.CTFrameGetLines(box)
    return ctLines

def getBaselines(txt, box):
    """Answers a list of (x,y) positions of all line starts in the box. This
    function may become part of standard DrawBot in the near future."""
    x, y, w, h = box
    attrString = txt.getNSObject()
    setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
    path = Quartz.CGPathCreateMutable()
    Quartz.CGPathAddRect(path, None, Quartz.CGRectMake(x, y, w, h))
    box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)
    ctLines = CoreText.CTFrameGetLines(box)
    #print(ctLines)
    origins = CoreText.CTFrameGetLineOrigins(box, (0, len(ctLines)), None)
    #print(origins)
    return [(x + o.x, y + o.y) for o in origins]

def getTextPositionSearch(bs, w, h, search, xTextAlign=LEFT, hyphenation=True):
    from AppKit import NSLocationInRange
    bc = BaseContext()
    path = CoreText.CGPathCreateMutable()
    CoreText.CGPathAddRect(path, None, CoreText.CGRectMake(0, 0, w, h))

    attrString = bc.attributedString(bs, align=xTextAlign)
    if hyphenation and bc._state.hyphenation:
        attrString = bc.hyphenateAttributedString(attrString, w)

    txt = attrString.string()
    searchRE = re.compile(search)
    locations = []
    for found in searchRE.finditer(txt):
        locations.append((found.start(), found.end()))

    setter = CTFramesetterCreateWithAttributedString(attrString)
    box = CTFramesetterCreateFrame(setter, (0, 0), path, None)

    ctLines = CTFrameGetLines(box)
    origins = CTFrameGetLineOrigins(box, (0, len(ctLines)), None)

    rectangles = []
    for startLocation, endLocation in locations:
        minx = miny = maxx = maxy = None
        for i, (originX, originY) in enumerate(origins):
            ctLine = ctLines[i]
            bounds = CTLineGetImageBounds(ctLine, None)
            if bounds.size.width == 0:
                continue
            _, ascent, descent, leading = CTLineGetTypographicBounds(ctLine, None, None, None)
            height = ascent + descent
            lineRange = CTLineGetStringRange(ctLine)
            miny = maxy = originY

            if NSLocationInRange(startLocation, lineRange):
                minx, _ = CTLineGetOffsetForStringIndex(ctLine, startLocation, None)

            if NSLocationInRange(endLocation, lineRange):
                maxx, _ = CTLineGetOffsetForStringIndex(ctLine, endLocation, None)
                rectangles.append((ctLine, (minx, miny - descent, maxx - minx, height)))

            if minx and maxx is None:
                rectangles.append((ctLine, (minx, miny - descent, bounds.size.width - minx, height)))
                minx = 0

    return rectangles
'''
