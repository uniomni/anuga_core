"""Least squares smooting and interpolation.

   measure the speed of least squares.

   ________________________
   General comments
   
   The max_points_per_cell does effect the time spent solving a
   problem.  The best value to use is probably dependent on the number
   of triangles.  Maybe develop a simple imperical algorithm, based on
   test results.
   
   Duncan Gray
   Geoscience Australia, 2004.
"""


import os
import sys
import time
from random import seed, random
import profile , pstats
import tempfile
from Scientific.IO.NetCDF import NetCDFFile
from Numeric import array

from anuga.fit_interpolate.interpolate import Interpolate
from anuga.fit_interpolate.fit import Fit
from anuga.pmesh.mesh import Mesh
from anuga.geospatial_data.geospatial_data import Geospatial_data
from anuga.shallow_water import Domain
from anuga.fit_interpolate.fit import Fit, fit_to_mesh
from anuga.fit_interpolate.interpolate import benchmark_interpolate
from anuga.shallow_water.data_manager import Write_sww, export_grid

def mem_usage():
    '''
    returns the rss.

  RSS  The total amount of physical memory used by  the  task,  in  kilo-
            bytes,  is  shown  here.  For ELF processes used library pages are
            counted here, for a.out processes not.
            
    Only works on nix systems.
    '''
    import string
    p=os.popen('ps uwp %s'%os.getpid()) 
    lines=p.readlines()
    #print "lines", lines
    status=p.close() 
    if status or len(lines)!=2 or sys.platform == 'win32': 
        return None 
    return int(string.split(lines[1])[4]) 




class Benchmarksww2dem:

    """

    Note(DSG-DSG): If you are interested in benchmarking fitting, before
    and after blocking O:\1\dgray\before_blocking_subsandpit is before blocking

    """

    def __init__(self):
        pass

    def trial(self,
              vert_rows,
              vert_columns,
              output_quantities=['elevation'],
              save=False,
              verbose=False,
              run_profile=False):
  
        import time
        
        sww_file_name = self._build_sww(vert_rows, vert_columns, save=save)
        
        #Initial time and memory
        t0 = time.time()
        #m0 = None on windows
        m0 = mem_usage()
        #print "m0", m0

        fileout = export_grid(sww_file_name, quantities=output_quantities)
        
        time_taken_sec = (time.time()-t0)
        m1 = mem_usage()
        #print "m1", m1
        if m0 is None or m1 is None:
            memory_used = None
        else:
            memory_used = (m1 - m0)
        #print 'That took %.2f seconds' %time_taken_sec
        return time_taken_sec, memory_used, m0, m1

    def _build_sww(self, vert_rows, vert_columns, save):
        """
        Build an sww file we can read. 
        verts_rows and vert_columns have to be greater that 1
        """
        m = Mesh()
        m.build_grid(vert_rows, vert_columns)
        if save is True:
            m.export_mesh_file("aaaa.tsh")
        mesh_dict =  m.Mesh2IOTriangulationDict()
        
        sww_fileName = tempfile.mktemp(".sww" )
        # sww_fileName = "aa.sww" 
        elevation = array(range(len(mesh_dict["vertices"])))
        stage = elevation
        ymomentum = elevation
        xmomentum = elevation
        
        # NetCDF file definition
        fid = NetCDFFile(sww_fileName, 'w')
        sww = Write_sww()
        sww.header(fid, 0,
                   len(mesh_dict['triangles']),
                   len(mesh_dict["vertices"]))
        sww.triangulation(fid,
                   mesh_dict["vertices"], mesh_dict['triangles'],
                          elevation)
        
        for time_step in range(10):
            sww.quantities(fid, 
                           time=time_step,
                           stage=stage,
                           xmomentum=xmomentum,
                           ymomentum=ymomentum)     
        #Close
        fid.close()
        return sww_fileName
    
#-------------------------------------------------------------
if __name__ == "__main__":
    b = Benchmarksww2dem() 
    delimiter = ','

    ofile = 'lbm_resultsII.csv'
    run_profile = False #True
    size_list = [[4,5],[50,40]]

    quantitiy_list = [['elevation'],
                      ['elevation','xmomentum'],
                      ['elevation','xmomentum','ymomentum']]
    
    fd = open(ofile,'a')
    # write the title line
    fd.write("size" + delimiter +
             "num_of_quantities" + delimiter +
             "is_profiling" + delimiter +
             "mem - diff"  + delimiter +
             "mem - initial"  + delimiter +
             "mem - final"  + delimiter +
             "time"  "\n")



    for size in size_list:
        for quantitiy in quantitiy_list:
            #sys.gettotalrefcount()
            #sys.getobjects() 
            time, mem, m0, m1 = b.trial(size[0]
                                        ,size[1]
                                        ,output_quantities=quantitiy
                                        ,run_profile=run_profile
                                        )
            print "time",time
            print "mem", mem
            #sys.gettotalrefcount() 
            fd.write(str(size[0]*size[1]) + delimiter +
                     str(len(quantitiy)) + delimiter +
                     str(run_profile) + delimiter +
                     str(mem)  + delimiter +
                     str(m0)  + delimiter +
                     str(m1)  + delimiter +
                     str(time) + delimiter + "\n")
fd.close()                         
