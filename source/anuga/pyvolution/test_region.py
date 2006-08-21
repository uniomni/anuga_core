#!/usr/bin/env python

import unittest
from math import sqrt

from domain import *
from region import *
#from config import epsilon
from Numeric import allclose #, array, ones, Float


def add_x_y(x, y):
    return x+y

def give_me_23(x, y):
    return 23.0

class Test_Region(unittest.TestCase):
    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_region_tags(self):
        """
        get values based on triangle lists.
        """
        from mesh_factory import rectangular
        from shallow_water import Domain
        from Numeric import zeros, Float

        #Create basic mesh
        points, vertices, boundary = rectangular(1, 3)

        #Create shallow water domain
        domain = Domain(points, vertices, boundary)
        domain.build_tagged_elements_dictionary({'bottom':[0,1],
                                                 'top':[4,5],
                                                 'all':[0,1,2,3,4,5]})


        #Set friction
        manning = 0.07
        domain.set_quantity('friction', manning)

        a = Set_region('bottom', 'friction', 0.09)
        b = Set_region('top', 'friction', 1.0)
        domain.set_region([a, b])
        #print domain.quantities['friction'].get_values()
        assert allclose(domain.quantities['friction'].get_values(),\
                        [[ 0.09,  0.09,  0.09],
                         [ 0.09,  0.09,  0.09],
                         [ 0.07,  0.07,  0.07],
                         [ 0.07,  0.07,  0.07],
                         [ 1.0,  1.0,  1.0],
                         [ 1.0,  1.0,  1.0]])

        #c = Add_Value_To_region('all', 'friction', 10.0)
        domain.set_region(Add_value_to_region('all', 'friction', 10.0))
        #print domain.quantities['friction'].get_values()
        assert allclose(domain.quantities['friction'].get_values(),
                        [[ 10.09, 10.09, 10.09],
                         [ 10.09, 10.09, 10.09],
                         [ 10.07, 10.07, 10.07],
                         [ 10.07, 10.07, 10.07],
                         [ 11.0,  11.0,  11.0],
                         [ 11.0,  11.0,  11.0]])

        # trying a function
        domain.set_region(Set_region('top', 'friction', add_x_y))
        #print domain.quantities['friction'].get_values()
        assert allclose(domain.quantities['friction'].get_values(),
                        [[ 10.09, 10.09, 10.09],
                         [ 10.09, 10.09, 10.09],
                         [ 10.07, 10.07, 10.07],
                         [ 10.07, 10.07, 10.07],
                         [ 5./3,  2.0,  2./3],
                         [ 1.0,  2./3,  2.0]])

        domain.set_quantity('elevation', 10.0)
        domain.set_quantity('stage', 10.0)
        domain.set_region(Add_value_to_region('top', 'stage', 1.0,initial_quantity='elevation'))
        #print domain.quantities['stage'].get_values()
        assert allclose(domain.quantities['stage'].get_values(),
                        [[ 10., 10., 10.],
                         [ 10., 10., 10.],
                         [ 10., 10., 10.],
                         [ 10., 10., 10.],
                         [ 11.0,  11.0,  11.0],
                         [ 11.0,  11.0,  11.0]])

        
        domain.set_quantity('elevation', 10.0)
        domain.set_quantity('stage', give_me_23)
        #this works as well, (is cleaner, but doesn't work for regions)
        #domain.set_quantity('stage',
        #                    domain.quantities['stage'].vertex_values+ \
        #                    domain.quantities['elevation'].vertex_values)
        domain.set_region(Add_quantities('top', 'elevation','stage'))
        #print domain.quantities['stage'].get_values()
        assert allclose(domain.quantities['elevation'].get_values(),
                        [[ 10., 10., 10.],
                         [ 10., 10., 10.],
                         [ 10., 10., 10.],
                         [ 10., 10., 10.],
                         [ 33.,  33.0,  33.],
                         [ 33.0,  33.,  33.]])
        
    def test_unique_vertices(self):
        """
        get values based on triangle lists.
        """
        from mesh_factory import rectangular
        from shallow_water import Domain
        from Numeric import zeros, Float

        #Create basic mesh
        points, vertices, boundary = rectangular(1, 3)

        #Create shallow water domain
        domain = Domain(points, vertices, boundary)
        domain.build_tagged_elements_dictionary({'bottom':[0,1],
                                                 'top':[4,5],
                                                 'all':[0,1,2,3,4,5]})

        #Set friction
        manning = 0.07
        domain.set_quantity('friction', manning)

        a = Set_region('bottom', 'friction', 0.09, location = 'unique vertices')
        domain.set_region(a)
        #print domain.quantities['friction'].get_values()
        assert allclose(domain.quantities['friction'].get_values(),\
                        [[ 0.09,  0.09,  0.09],
                         [ 0.09,  0.09,  0.09],
                         [ 0.09,  0.07,  0.09],
                         [ 0.07,  0.09,  0.07],
                         [ 0.07,  0.07,  0.07],
                         [ 0.07,  0.07,  0.07]])


    def test_unique_verticesII(self):
        """
        get values based on triangle lists.
        """
        from mesh_factory import rectangular
        from shallow_water import Domain
        from Numeric import zeros, Float

        #Create basic mesh
        points, vertices, boundary = rectangular(1, 3)

        #Create shallow water domain
        domain = Domain(points, vertices, boundary)
        domain.build_tagged_elements_dictionary({'bottom':[0,1],
                                                 'top':[4,5],
                                                 'all':[0,1,2,3,4,5]})

        #Set friction
        manning = 0.07
        domain.set_quantity('friction', manning)

        domain.set_region(Add_value_to_region('bottom', 'friction', 1.0,initial_quantity='friction', location = 'unique vertices'))

        #print domain.quantities['friction'].get_values()
        assert allclose(domain.quantities['friction'].get_values(),\
                        [[ 1.07,  1.07,  1.07],
                         [ 1.07,  1.07,  1.07],
                         [ 1.07,  0.07,  1.07],
                         [ 0.07,  1.07,  0.07],
                         [ 0.07,  0.07,  0.07],
                         [ 0.07,  0.07,  0.07]])
#-------------------------------------------------------------
if __name__ == "__main__":
    suite = unittest.makeSuite(Test_Region,'test')
    runner = unittest.TextTestRunner()
    runner.run(suite)
