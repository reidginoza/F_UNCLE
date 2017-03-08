"""

To run all tests, issue "nosetests" in the root directory, ie ../..

To run this file, issue "python test_Experiments.py" in this directory.

Authors
-------

- Stephen Andrews (SA)
- Andrew M. Fraiser (AMF)

Revisions
---------

0 -> Initial class creation (06-06-2016)

ToDo
----

None

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# =========================
# Python Standard Libraries
# =========================

import copy
import unittest
import sys
import os

# =========================
# Python Packages
# =========================
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brentq

# =========================
# Custom Packages
# =========================

from ...Utils.Simulation import Simulation
from ...Models.Isentrope import EOSBump, EOSModel, Isentrope, Spline
from ...Models.Ptw import Ptw
from ..GunModel import Gun, GunExperiment
from ..Stick import Stick, StickExperiment
from ..Sphere import Sphere

class TestGun(unittest.TestCase):
    """Test of the Gun experiment
    """

    def test_instantiation(self):
        """Tests that the model is properly instantiated
        """
        eos = EOSBump()
        gun = Gun()

        self.assertIsInstance(gun, Gun)
    # end

    def test_shoot_model_eos(self):
        """Performs a test shot using default settings a model EOS
        """

        p_fun = lambda v: 2.56e9 / v**3

        eos = EOSModel(p_fun)
        gun = Gun()

        time, (vel, pos, labels), data = gun({'eos': eos})

        n_time = gun.get_option('n_t')

        self.assertEqual(len(time), n_time)
        self.assertEqual(len(pos), n_time)
        self.assertEqual(len(vel), n_time)
        self.assertIsInstance(data, dict)
        self.assertIsInstance(data['mean_fn'], Spline)

    @unittest.skip('skipped plotting routine')
    def test_shot_plot(self):
        """tests the plotting function
        """

        init_prior = np.vectorize(lambda v: 2.56e9 / v**3)

        # Create the model and *true* EOS
        eos = EOSModel(init_prior)

        gun = Gun()

        data0 = gun({'eos': eos})
        old_dof = eos.get_c()
        old_dof[0] *= 1.02
        eos.update_dof(old_dof)
        data1 = gun({'eos': eos})

        gun.plot(level=3, data=[data0, data1])

        gun.plot(level=1, data=[data0, data1])

        plt.show()
# end


class TestStick(unittest.TestCase):
    """Test of the Stick experiment
    """
    def setUp(self):
        """Common setup options for the models
        """
        init_prior = np.vectorize(lambda v: 2.56e9 / v**3)

        self.true_eos = EOSBump()
        self.model_eos = EOSModel(init_prior)

    def test_instatntiation(self):
        """Tests basic instantiation
        """

        stick = Stick()

    def test_call(self):
        """Tests that the default settings run and the outputs are structured
           correctly
        """
        stick = Stick()

        n_data = stick.get_option('n_x')

        data = stick({'eos': self.true_eos})

        # Check data was output correctly
        self.assertEqual(len(data), 3)

        indep = data[0]
        dep = data[1]
        smry = data[2]

        # Check the independent data
        self.assertEqual(len(indep), n_data)

        # Check the dependent data
        self.assertEqual(len(dep), 2)
        self.assertEqual(len(dep[0]), n_data)

        # Check the summary data
        self.assertTrue('vel_CJ' in smry)
        self.assertTrue('vol_CJ' in smry)
        self.assertTrue('pres_CJ' in smry)
        self.assertTrue('Rayl_fn' in smry)        
        self.assertIsInstance(smry['vel_CJ'], float)
        self.assertIsInstance(smry['vol_CJ'], float)
        self.assertIsInstance(smry['pres_CJ'], float)
        self.assertTrue(hasattr(smry['Rayl_fn'], '__call__'))

    @unittest.skip('skipped plotting routine')
    def test_eos_step(self):
        """Tests that the stick model is sensitive to changes in EOS
        """
        stick = Stick()

        n_data = stick.get_option('n_x')

        data1 = stick({'eos': self.model_eos})
        stick.plot({'eos': self.model_eos})
        i = np.argmin(np.fabs(self.model_eos.get_t() - data1[2][1]))
        i -= 2

        plt.figure()
        ax1 = plt.gca()
        for i in range(self.model_eos.shape()):
            initial_dof = self.model_eos.get_dof()

            delta = 0.02
            delta *= initial_dof[i]

            new_dof = copy.deepcopy(initial_dof)
            new_dof[i] += delta

            new_model = self.model_eos.update_dof(new_dof)

            data2 = stick({'eos': new_model})
            # stick.plot()
            plt.plot((data1[1][0] - data2[1][0]) / delta)

        plt.show()
    
    def test_compare(self):
        """Tests the comparison function
        """

        sim_stick = Stick()
        true_stick = StickExperiment(model=self.true_eos)

        n_true = sim_stick.get_option('n_x')
        true_data = true_stick()

        n_sim = 10
        sim_stick.set_option('n_x', n_sim)

        sim_data = sim_stick({'eos': self.model_eos})

        self.assertEqual(len(true_data[0]), n_true)
        self.assertEqual(len(sim_data[0]), n_sim)

        epsilon = sim_stick.compare(sim_data, true_data)

        self.assertEqual(len(epsilon), n_true)

    def test_shape(self):
        """Tests the shape function
        """

        stick = Stick()
        self.assertEqual(stick.shape(), stick.get_option('n_x'))

    def test_sigma(self):
        """Tests the variance function
        """

        stick = Stick()

        dim = stick.shape()
        var = stick.get_sigma({'eos': self.model_eos})
        self.assertEqual(var.shape, (dim, dim))

@unittest.skip('skipped Sphere, not updated')
class TestSphere(unittest.TestCase):
    def setUp(self):
        init_prior = np.vectorize(lambda v: 2.56e9 / v**3)

        self.eos = EOSModel(init_prior, Spline_sigma=0.05, spline_max=2.0)
        self.strength = Ptw()
        self.sim = Sphere()

    def test_print(self):
        print(self.sim)

    def test_call(self):
        data = self.sim({'eos': self.eos, 'strength': self.strength})
        #self.sim.plot(data)
        #plt.show()

class TestGunExperiment(unittest.TestCase):

    def test_instantiation(self):
        """
        """
        
        model = EOSBump()

        exp = GunExperiment(model=model,
                            mass_he=1.0)


        self.assertIsInstance(exp, GunExperiment)

class TestStickExperiment(unittest.TestCase):

    def test_instantiation(self):
        """
        """

        model = EOSBump()

        exp = StickExperiment(model=model,
                              mass_he=1.0)


        self.assertIsInstance(exp, StickExperiment)
        
if __name__ == '__main__':
    unittest.main(verbosity=4)
