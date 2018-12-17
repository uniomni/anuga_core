"""Bilinear and piecewise constant interpolation.

* Interpolate from a regular numpy array to arbitrary points.
* NaN's are taken care of sensibly.
* Algorithm works both for cartesian (x, y) and geographic (lon, lat)
  coordinates.
* Guarantees interpolated values within extrema of grid points, i.e.
  no overshoot.

See docstring for details on usage and the mathematical derivation.

To test, run the accompanying script test_interpolate2d.py

Author: Ole Nielsen 2011

"""
__author__ = 'Ole Nielsen <ole.moller.nielsen@gmail.com>'
__revision__ = '$Format:%H$'
__date__ = '01/11/2011'
__license__ = 'GPL v3'
__copyright__ = 'Copyright 2012, Australia Indonesia Facility for '
__copyright__ += 'Disaster Reduction'

import numpy
from anuga.anuga_exceptions import ANUGAError, BoundsError



def interpolate2d(x, y, Z, points, mode='linear', bounds_error=True):
    """Fundamental 2D interpolation routine

    Input
        x: 1D array of x-coordinates of the mesh on which to interpolate
        y: 1D array of y-coordinates of the mesh on which to interpolate
        Z: 2D array of values for each x, y pair
        points: Nx2 array of coordinates where interpolated values are sought
        mode: Determines the interpolation order. Options are
            * 'constant' - piecewise constant nearest neighbour interpolation
            * 'linear' - bilinear interpolation using the four
                         nearest neighbours (default)
        bounds_error: Boolean flag. If True (default) a BoundsError exception
            will be raised when interpolated values are requested
            outside the domain of the input data or a nan is found in the Z
            data file. If False, nan is returned for those values

    Output
        1D array of length N (same length as points) with interpolated values

    Notes
        Input coordinates x and y are assumed to be monotonically increasing,
        but need not be equidistantly spaced.

        Z is assumed to have dimension M x N, where M = len(x) and N = len(y).
        In other words it is assumed that the x values follow the first
        (vertical) axis downwards and y values the second (horizontal) axis
        from left to right.

        If this routine is to be used for interpolation of raster grids where
        data is typically organised with longitudes (x) going from left to
        right and latitudes (y) from left to right then user
        interpolate_raster in this module

    Derivation

        Bilinear interpolation is based on the standard 1D linear interpolation
        formula:

        Given points (x0, y0) and (x1, y1) and a value of x where
        x0 <= x <= x1, the linearly interpolated value y at x is given as

        alpha*(y1-y0) + y0

        or

        alpha*y1 + (1-alpha)*y0                (1)

        where alpha = (x-x0)/(x1-x0)           (1a)


        2D bilinear interpolation aims at obtaining an interpolated value z at
        a point (x,y) which lies inside a square formed by points (x0, y0),
        (x1, y0), (x0, y1) and (x1, y1) for which values z00, z10, z01 and
        z11 are known.

        This is obtained by applying equation (1) twice  in the
        x-direction to obtain interpolated points q0 and q1 for (x, y0) and
        (x, y1), respectively.

        q0 = alpha*z10 + (1-alpha)*z00         (2)

        and

        q1 = alpha*z11 + (1-alpha)*z01         (3)


        Then using equation (1) in the y-direction on the results from (2)
        and (3)

        z = beta*q1 + (1-beta)*q0              (4)

        where beta = (y-y0)/(y1-y0)            (4a)


        Substituting (2) and (3) into (4) yields

        z = alpha*beta*z11 + beta*z01 - alpha*beta*z01 +
            alpha*z10 + z00 - alpha*z00 - alpha*beta*z10 - beta*z00 +
            alpha*beta*z00
          = alpha*beta*(z11 - z01 - z10 + z00) +
            alpha*(z10 - z00) + beta*(z01 - z00) + z00

        which can be further simplified to

        z = alpha*beta*(z11 - dx - dy - z00) + alpha*dx + beta*dy + z00  (5)

        where
        dx = z10 - z00
        dy = z01 - z00

        Equation (5) is what is implemented in the function interpolate2d.


        Piecewise constant interpolation can be implemented using the same
        coefficients (1a) and (4a) that are used for bilinear interpolation
        as they are a measure of the relative distance to the left and lower
        neigbours. A value of 0 will pick the left or lower bound whereas a
        value of 1 will pick the right or higher bound. Hence z can be
        assigned to its nearest neigbour as follows

            | z00   alpha < 0.5 and beta < 0.5    # lower left corner
            |
            | z10   alpha >= 0.5 and beta < 0.5   # lower right corner
        z = |
            | z01   alpha < 0.5 and beta >= 0.5   # upper left corner
            |
            | z11   alpha >= 0.5 and beta >= 0.5  # upper right corner

    """

    # Check inputs and provide xi, eta as x and y coordinates from
    # points vector
    x, y, Z, xi, eta = check_inputs(x, y, Z, points, mode, bounds_error)

    # Identify elements that are outside interpolation domain or NaN
    oldset = numpy.seterr(invalid='ignore')  # Suppress comparison with nan warning
    outside = (xi < x[0]) + (eta < y[0]) + (xi > x[-1]) + (eta > y[-1])
    outside += numpy.isnan(xi) + numpy.isnan(eta)
    numpy.seterr(**oldset)  # Restore warnings
    
    # Restrict interpolation points to those that are inside the grid
    inside = numpy.logical_not(outside)  # Invert boolean array to find elements inside
    xi = xi[inside]
    eta = eta[inside]

    # Find upper neighbours for each interpolation point
    # ('left' means first occurrence)
    idx = numpy.searchsorted(x, xi, side='left')
    idy = numpy.searchsorted(y, eta, side='left')

    # Get the four neighbours for each interpolation point
    x0 = x[idx - 1]  # Left
    x1 = x[idx]      # Right
    y0 = y[idy - 1]  # Lower
    y1 = y[idy]      # Upper

    # And the corresponding four grid values
    z00 = Z[idx - 1, idy - 1]
    z01 = Z[idx - 1, idy]
    z10 = Z[idx, idy - 1]
    z11 = Z[idx, idy]

    # Coefficients for weighting between lower and upper bounds
    oldset = numpy.seterr(invalid='ignore')  # Suppress zero division warning
    alpha = (xi - x0) / (x1 - x0)
    beta = (eta - y0) / (y1 - y0)
    numpy.seterr(**oldset)  # Restore warnings

    if mode == 'linear':
        # Bilinear interpolation formula as per equation (5) above
        dx = z10 - z00
        dy = z01 - z00
        z = z00 + alpha * dx + beta * dy + alpha * beta * (z11 - dx - dy - z00)
    else:
        # Piecewise constant (as verified in input_check)

        # Set up masks for the quadrants
        left = alpha < 0.5
        right = numpy.logical_not(left)
        lower = beta < 0.5
        upper = numpy.logical_not(lower)

        lower_left = lower * left
        lower_right = lower * right
        upper_left = upper * left

        # Initialise result array with all elements set to upper right
        z = z11

        # Then set the other quadrants
        z[lower_left] = z00[lower_left]
        z[lower_right] = z10[lower_right]
        z[upper_left] = z01[upper_left]

    # Populate result with interpolated values for points inside domain
    # and NaN for values outside
    r = numpy.zeros(len(points))
    r[inside] = z
    r[outside] = numpy.nan

    # Return interpolated points
    return r

def interpolate_raster(x, y, z, points, mode='linear', bounds_error=False):
    """2D interpolation of raster data
    It is assumed that data is organised in matrix z as latitudes from
    bottom up along the first dimension and longitudes from west to east
    along the second dimension.
    Further it is assumed that x is the vector of longitudes and y the
    vector of latitudes.
    See interpolate2d for details of the interpolation routine
    :param x: 1D array of x-coordinates of the mesh on which to interpolate
    :type x: numpy.ndarray
    :param y: 1D array of y-coordinates of the mesh on which to interpolate
    :type y: numpy.ndarray
    :param z: 2D array of values for each x, y pair
    :type z: numpy.ndarry
    :param points: Nx2 array of coordinates where interpolated values are
        sought
    :type points: numpy.narray
    :param mode: Determines the interpolation order.
        Options are:
            * 'constant' - piecewise constant nearest neighbour interpolation
            * 'linear' - bilinear interpolation using the four
              nearest neighbours (default)
    :type mode: str
    :param bounds_error: If True (default) a BoundsError exception
          will be raised when interpolated values are requested
          outside the domain of the input data. If False, nan
          is returned for those values
    :type bounds_error: bool
    :returns: 1D array with same length as points with interpolated values
    :raises: Exception, BoundsError (see note about bounds_error)
    """

    # Flip matrix z up-down to interpret latitudes ordered from south to north
    z = numpy.flipud(z)

    # Transpose z to have y coordinates along the first axis and x coordinates
    # along the second axis
    # noinspection PyUnresolvedReferences
    z = z.transpose()

    # Call underlying interpolation routine and return
    res = interpolate2d(x, y, z, points, mode=mode, bounds_error=bounds_error)
    return res

#------------------------
# Auxiliary functionality
#------------------------
def check_inputs(x, y, Z, points, mode, bounds_error):
    """Check inputs for interpolate2d function
    """

    msg = ('Only mode "linear" and "constant" are implemented. '
           'I got "%s"' % mode)
    if mode not in ['linear', 'constant']:
        raise ANUGAError(msg)

    x = numpy.array(x)

    try:
        y = numpy.array(y)
    except Exception, e:
        msg = ('Input vector y could not be converted to numpy array: '
               '%s' % str(e))
        raise Exception(msg)

    msg = ('Input vector x must be monotonically increasing. I got '
           'min(x) == %.15f, but x[0] == %.15f' % (min(x), x[0]))
    if not min(x) == x[0]:
        raise ANUGAError(msg)

    msg = ('Input vector y must be monotoneously increasing. '
           'I got min(y) == %.15f, but y[0] == %.15f' % (min(y), y[0]))
    if not min(y) == y[0]:
        raise ANUGAError(msg)

    msg = ('Input vector x must be monotoneously increasing. I got '
           'max(x) == %.15f, but x[-1] == %.15f' % (max(x), x[-1]))
    if not max(x) == x[-1]:
        raise ANUGAError(msg)

    msg = ('Input vector y must be monotoneously increasing. I got '
           'max(y) == %.15f, but y[-1] == %.15f' % (max(y), y[-1]))
    if not max(y) == y[-1]:
        raise ANUGAError(msg)

    try:
        Z = numpy.array(Z)
        m, n = Z.shape
    except Exception, e:
        msg = 'Z must be a 2D numpy array: %s' % str(e)
        raise Exception(msg)

    Nx = len(x)
    Ny = len(y)

    msg =  ('Input array Z must have dimensions %i x %i corresponding to the '
            'lengths of the input coordinates x and y. However, '
            'Z has dimensions %i x %i.' % (Nx, Ny, m, n))
    if not (Nx == m and Ny == n):
        raise ANUGAError(msg)

    # Get interpolation points
    points = numpy.array(points)
    xi = points[:, 0]
    eta = points[:, 1]

    if bounds_error:
        xi0 = numpy.nanmin(xi)
        xi1 = numpy.nanmax(xi)
        eta0 = numpy.nanmin(eta)
        eta1 = numpy.nanmax(eta)

        msg = ('Interpolation point xi=%f was less than the smallest '
               'value in domain (x=%f) and bounds_error was requested. '
               'Consider using unstructured fitting using pts file'
               % (xi0, x[0]))
        if xi0 < x[0]:
            raise BoundsError(msg)

        msg = ('Interpolation point xi=%f was greater than the largest '
               'value in domain (x=%f) and bounds_error was requested. '
               'Consider using unstructured fitting using pts file'
               % (xi1, x[-1]))
        if xi1 > x[-1]:
            raise BoundsError(msg)

        msg = ('Interpolation point eta=%f was less than the smallest '
               'value in domain (y=%f) and bounds_error was requested. '
               'Consider using unstructured fitting using pts file'
               % (eta0, y[0]))
        if eta0 < y[0]:
            raise BoundsError(msg)

        msg = ('Interpolation point eta=%f was greater than the largest '
               'value in domain (y=%f) and bounds_error was requested. '
               'Consider using unstructured fitting using pts file'
               % (eta1, y[-1]))
        if eta1 > y[-1]:
            raise BoundsError(msg)
        

            

    return x, y, Z, xi, eta
