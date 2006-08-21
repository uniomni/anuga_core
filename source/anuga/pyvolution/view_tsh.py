"""
Script to view tsh file using faster vpython graphics
"""
import sys
from os import sep, path
sys.path.append('..'+sep+'pyvolution')


from shallow_water import Domain
from pmesh2domain import pmesh_to_domain_instance
from pyvolution.util import file_function
from utilities.polygon import Polygon_function, read_polygon
from Numeric import zeros, Float, maximum, minimum
from realtime_visualisation_new import *

#-------
# Domain


#-------------------------------------------------------------
if __name__ == "__main__":
    """
    View a mesh and data points with attributes.
    """
    import os, sys
    usage = "usage: %s mesh_input.tsh scale_z"%os.path.basename(sys.argv[0])

    #print len(sys.argv)
    #print sys.argv

    if len(sys.argv) < 2:
        print usage
    else:
        mesh_file = sys.argv[1]

        scale_z = 1.0
        if len(sys.argv) > 2:
            scale_z = float(sys.argv[2])



    print 'Creating domain from', mesh_file
    domain = pmesh_to_domain_instance(mesh_file, Domain)
    print "Number of triangles = ", len(domain)

    visualiser =  Visualiser(domain, scale_z = scale_z)
    visualiser.update_quantity('stage')
