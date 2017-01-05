#!/usr/local/bin/python
"""

mpi_loop

Abstract paralellized loop. Used to apply arbitrary inputs to arbitrary functions
- Uses Static Process Management


Developers
----------
- Dr. S. Andrews

History
-------
1.0 - Initial class creation

"""

__version__ = '$Revision: $'

"""
To Do:

"""
import numpy as np
from mpi4py import MPI
def pll_loop(x, func, shape=None, comm=None, *args, **kwargs):
    """
    Uses MPI to evaluate `func' for each value of x and returns a dictionary of the results
    - Uses Static Process Management (SPM)

    Args:
        x(list): Inputs to the function, can be a list of values, lists or dictionarys.
        func(function): The function to evaluate.

    Keyword Args:
        comm(mpi4py communicator): If none, uses the whole set of MPI processprs
            else it should be a valid MPI group to use.

    Return:
         (dict): Dictionary of the function outputs with the same indicies as x.

    """
    # print('Entering the MPI loop')
    if comm is None:
        try:
            comm = MPI.COMM_WORLD
        except:
            raise(ImportError("Could not import MPI for py"))
        # end
    else:
        pass
    # end
    nproc = comm.Get_size()
    myrank = comm.Get_rank()
    Barrier = comm.barrier
    Send = comm.Send
    Recv = comm.Recv
    Bcast = comm.bcast

    myxval = range(myrank, len(x), nproc)
    out_data = {}

    # The actuall paralell loop
    send_buf = np.empty((shape, len(myxval)))
    for j, i in enumerate(myxval):
        print('evaluating variable {:d} on rank {:d}'.format(i, myrank))
        send_buf[:,j] = func(x[i], *args, **kwargs)
    #end
    
    # Send and receive the data
    if myrank != 0:
        print('sending from rank {:d} to rank {:d}'.format(myrank, 0))        
        Send(send_buf, dest=0, tag = 1)
    else:
        for j, i in enumerate(myxval):
            out_data[i] = send_buf[:,j]
        #end
    # end
    import time
    time.sleep(2)
    Barrier()
    if myrank == 0:
        p_results = {}
        for proc in xrange(1, nproc):
            proc_xval = range(myrank, len(x), nproc)
            rec_buff = np.empty((shape, len(proc_xval)))
            print('recieving from rank {:d} on rank {:d}'.format(proc, myrank))
            
            try:
                Recv(rec_buff, source=proc, tag=1)
                for j, i in enumerate(proc_xval):
                    out_data[i] = rec_buff[:,j]
                # end
                #p_results.append(Recv(source=proc, tag=1))
            except MPI.Exception as inst:
                print("rank %d failed recieving from proc %d"%(myrank, proc))
                print(type(inst))
                
                raise inst
        #end
    #end


    # Organize the data
    if myrank == 0:
        # for proc in xrange(nproc-1):
        #     for i in p_results[proc].keys():
        #         out_data[i] = p_results[proc][i]
        #     #end
        # #end
        print('broadcasting from rank {:d} to rank {:d}'.format(0, myrank))    
        out_data = Bcast(out_data, root=0)
#        print(out_data)
    #end
    Barrier()    
    
    return out_data
#end

import time
def expensive_func(x, *args, **kwargs):
    """
    A function to evaluate to test the paralell abilities
    """
    fact = x
    for i in xrange(x-1):
        fact *= (x-(i+1))
    #end
    time.sleep(1)
    return fact

def complex_io(x, p = {}, *args, **kwargs):
    """
    A function to test the IO capabilities of the function
    """
    var1 = x[0]
    var2 = x[1]

    kw1 = p['kw1']

    # print "var1 ", var1
    # print "var2 ", var2
    # print "kw1 ", kw1

    out = {}
    out['out1'] = str(var1*var2)
    out['out2'] = var1 + var2
    out['out3'] = var1*1.0 / var2
#    time.sleep(10)
    return out

if __name__ == "__main__":
    from mpi4py import MPI

    # Test 1
    # ------
    # > Test the speedup obtained from the paralell function

    import time
    x = range(2,300, 1)
    to = time.time()
    y = pll_loop(x, expensive_func)

    if MPI.COMM_WORLD.Get_rank() == 0:
        print("Time taken ", time.time()-to)
    #end

    # Test 2
    # ------
    # > Test the ability to handle complex io

    x = [[1,2],[3,4],[5,6],[7,8]]
    param = {'kw1' : 'potatoe'}
    y = pll_loop(x, complex_io, p = param)

    if MPI.COMM_WORLD.Get_rank() == 0:
        for key in y:
            dct = y[key]
            print('out1 ', dct['out1'], ' out2 ', dct['out2'], ' out3 ', dct['out3'])
        #end
    # #end