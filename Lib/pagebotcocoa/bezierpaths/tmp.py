
'''
def moveTo(self, point):
    """
    Move to a point `x`, `y`.
    """
    super(BezierPath, self).moveTo(point)

def lineTo(self, point):
    """
    Line to a point `x`, `y`.
    """
    super(BezierPath, self).lineTo(point)

def curveTo(self, *points):
    """
    Draw a cubic Bézier with an arbitrary number of control points.

    The last point specified is on-curve, all others are off-curve
    (control) points.
    """
    super(BezierPath, self).curveTo(*points)

def qCurveTo(self, *points):
    """
    Draw a whole string of quadratic curve segments.

    The last point specified is on-curve, all others are off-curve
    (control) points.
    """
    super(BezierPath, self).qCurveTo(*points)

def addComponent(self, glyphName, transformation):
    """
    Add a sub glyph. The 'transformation' argument must be a 6-tuple
    containing an affine transformation, or a Transform object from the
    fontTools.misc.transform module. More precisely: it should be a
    sequence containing 6 numbers.

    A `glyphSet` is required during initialization of the BezierPath object.
    """
    super(BezierPath, self).addComponent(glyphName, transformation)
'''
