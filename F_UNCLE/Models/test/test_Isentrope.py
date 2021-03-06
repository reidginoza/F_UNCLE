#!/usr/bin/pyton
"""

test_Isentrope

Collection of tests for Isentrope objects

Authors
-------

- Stephen Andrews (SA)
- Andrew M. Fraser (AMF)

Revisions
---------

0 -> Initial class creation (03-16-2016)

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
import math
import sys
import os

# =========================
# Python Packages
# =========================
import numpy as np
import numpy.testing as npt
import matplotlib.pyplot as plt
from scipy.interpolate import InterpolatedUnivariateSpline as IU_Spline
# For scipy.interpolate.InterpolatedUnivariateSpline. See:
# https://github.com/scipy/scipy/blob/v0.14.0/scipy/interpolate/fitpack2.py


# =========================
# Custom Packages
# =========================
from ...Utils.PhysicsModel import GaussianModel
from ..Isentrope import EOSModel, EOSBump, Isentrope


class TestIsentrope(unittest.TestCase):
    """Test of the isentrope object
    """
    def test_standard_instantiation(self):
        """Test basic use of isentrope
        """
        model = Isentrope()

        self.assertEqual(model.get_option('spline_N'), 50)
        self.assertEqual(model.get_option('spline_min'), 0.1)
        self.assertEqual(model.get_option('spline_max'), 1.0)
        self.assertEqual(model.get_option('spline_end'), 4)
    # end

    def test_custom_instantiation(self):
        """Test instantiated with non default values
        """
        model = Isentrope(name="Francis", spline_N=55,
                          spline_sigma=0.0)

        self.assertEqual(model.name, "Francis")
        self.assertEqual(model.get_option('spline_N'), 55)


# end

class TestEosModel(unittest.TestCase):
    """Test the spline EOS functions
    """
    def setUp(self):
        """Create test EOS function
        """

        p_fun = lambda v: 2.56e9 / v**3

        self.p_fun = p_fun

    def test_standard_instantiation(self):
        """Test normal instantiation of the EOS
        """

        eos = EOSModel(self.p_fun)

        print(eos)

        self.assertEqual(eos.get_option('spline_sigma'), 5e-3)
    # end

    def test_bad_instantiation(self):
        """Test improper instantiation
        """

        with self.assertRaises(TypeError):
            EOSModel(2.5)
        # end

    # end
    def test_eos_bounds_plot_vol(self):
        """Plots the extrapolated behaviour
        """

        eos = EOSModel(self.p_fun)

        test_vol = np.linspace(0.01, 1.0, 200)

        fig = plt.figure()
        ax1 = fig.gca()
        ax1.plot(test_vol, eos(test_vol))

        for i in range(5):
            old_dof = eos.get_dof()
            old_dof[i] *= 1.02
            new_eos = eos.update_dof(old_dof)
            ax1.plot(test_vol, new_eos(test_vol))
        # end

        ax1.set_xlabel('Specific volume / cm3 g-1')
        ax1.set_ylabel('Pressure / Pa')
        fig.savefig('vol_eos_bounds_test.pdf')

    def test_eos_bounds_plot_dens(self):
        """Plots the extrapolated behaviour for density basis
        """

        eos = EOSModel(lambda rho: 2.56E9 * rho **3,
                       basis='density',
                       spline_min=1.0,
                       spline_max=10.0)

        old_dof = eos.get_dof()
        old_dof[1] *= 1.02
        new_eos = eos.update_dof(old_dof)
        test_dens = np.linspace(0.1, 10.0, 200)

        fig = plt.figure()
        ax1 = fig.gca()
        ax1.plot(test_dens, eos(test_dens))

        for i in range(5):
            old_dof = eos.get_dof()
            old_dof[i] *= 1.02
            new_eos = eos.update_dof(old_dof)
            ax1.plot(test_dens, new_eos(test_dens))
        # end

        ax1.set_xlabel('Density / g cm-3')
        ax1.set_ylabel('Pressure / Pa')
        fig.savefig('dens_eos_bounds_test.pdf')


    def test_custom_instantiation(self):
        """Tests instantiation with non default values
        """
        eos = EOSModel(self.p_fun, name="Ajax", spline_N=65,
                       spline_sigma=2.5e-3)

        self.assertEqual(eos.name, "Ajax")
        self.assertEqual(eos.get_option('spline_N'), 65)
        self.assertEqual(eos.get_option('spline_sigma'), 2.5e-3)

    def test_linear_knot_spacing(self):
        """Tests alternate knot spacing
        """

        eos = EOSModel(self.p_fun, spacing='lin', spline_N=10)

        with self.assertRaises(KeyError):
            eos = EOSModel(self.p_fun, spacing='bad_spacing')
        # end


    def test_spline_get_t(self):
        """Test spline interaction method, get knots
        """

        # generate an EOS spline
        eos = EOSModel(self.p_fun)

        # get t
        t_list = eos.get_t()

        # check it is a numpy array

        self.assertIsInstance(t_list, np.ndarray)

        # check it is long enough
        self.assertEqual(
            eos.get_option('spline_N') + eos.get_option('spline_end'),
            len(t_list)
        )

        # check is spans the v min and v max limits
        self.assertEqual(eos.get_option('spline_min'), t_list.min())
        self.assertEqual(eos.get_option('spline_max'), t_list.max())

    def test_density_basis_get_dof(self):
        """Tests getting the coefficients when a density EOS is used
        """

        eos = EOSModel(lambda rho: 2.56E9 * rho **3,
                       basis='density',
                       spline_min=1.0,
                       spline_max=10.0)

        c_list = eos.get_dof()

        self.assertEqual(c_list[0], eos._eval_args[1][0])
        self.assertEqual(c_list[1], eos._eval_args[1][1])
        self.assertEqual(c_list[2], eos._eval_args[1][2])
        self.assertEqual(c_list[3], eos._eval_args[1][3])
        self.assertEqual(c_list[4], eos._eval_args[1][4])
        self.assertEqual(0.0, eos._eval_args[1][-1])
        self.assertEqual(0.0, eos._eval_args[1][-2])
        self.assertEqual(0.0, eos._eval_args[1][-3])
        self.assertEqual(0.0, eos._eval_args[1][-4])

    def test_density_basis_update_dof(self):
        """Tests getting the coefficients when a density EOS is used
        """

        eos = EOSModel(lambda rho: 2.56E9 * rho **3,
                       basis='density',
                       spline_min=1.0,
                       spline_max=10.0)

        c_list = eos.get_dof()
        c_list[0] *= 1.02
        first_dof = copy.copy(c_list[0])

        new_eos = eos.update_dof(c_list)

        self.assertEqual(first_dof, new_eos._eval_args[1][0])
        self.assertEqual(c_list[1], new_eos._eval_args[1][1])
        self.assertEqual(c_list[2], new_eos._eval_args[1][2])
        self.assertEqual(c_list[3], new_eos._eval_args[1][3])
        self.assertEqual(c_list[4], new_eos._eval_args[1][4])
        self.assertEqual(0.0, new_eos._eval_args[1][-1])
        self.assertEqual(0.0, new_eos._eval_args[1][-2])
        self.assertEqual(0.0, new_eos._eval_args[1][-3])
        self.assertEqual(0.0, new_eos._eval_args[1][-4])

    def test_spline_get_c(self):
        """Test spline interaction method, get coefficients
        """
        # generate an EOS spline
        eos = EOSModel(self.p_fun)

        # get c
        c_list = eos.get_c()

        self.assertEqual(eos.get_option('spline_N'), len(c_list))

        self.assertEqual(c_list[0], eos._eval_args[1][0])
        self.assertEqual(c_list[1], eos._eval_args[1][1])
        self.assertEqual(c_list[2], eos._eval_args[1][2])
        self.assertEqual(c_list[3], eos._eval_args[1][3])
        self.assertEqual(c_list[-1], eos._eval_args[1][-5])
        self.assertEqual(0.0, eos._eval_args[1][-1])
        self.assertEqual(0.0, eos._eval_args[1][-2])
        self.assertEqual(0.0, eos._eval_args[1][-3])
        self.assertEqual(0.0, eos._eval_args[1][-4])

    def test_spline_new_c(self):
        """Test spline interaction method, set new coefficients
        """

        eos = EOSModel(self.p_fun)

        # get c
        c_list = eos.get_dof()

        # add 0.1 to all c
        # get a new spline with updated c
        new_eos = eos.update_dof(c_list + 0.1)

        # check it matches
        npt.assert_array_equal(new_eos.get_dof(), c_list + 0.1)
        npt.assert_array_equal(c_list, eos.get_dof())

        self.assertEqual(c_list[0] + 0.1, new_eos._eval_args[1][0])
        self.assertEqual(c_list[1] + 0.1, new_eos._eval_args[1][1])
        self.assertEqual(c_list[2] + 0.1, new_eos._eval_args[1][2])
        self.assertEqual(c_list[3]+ 0.1, new_eos._eval_args[1][3])
        self.assertEqual(c_list[-1] + 0.1, new_eos._eval_args[1][-5])
        self.assertEqual(0.0, new_eos._eval_args[1][-1])
        self.assertEqual(0.0, new_eos._eval_args[1][-2])
        self.assertEqual(0.0, new_eos._eval_args[1][-3])
        self.assertEqual(0.0, new_eos._eval_args[1][-4])


    def test_eos_get_sigma(self):
        """ Tests that the co-variance matrix is generated correctly
        """

        eos = EOSModel(self.p_fun)

        sigma_eos = eos.get_sigma()

        n_spline = eos.get_option('spline_N')
        spline_var = eos.get_option('spline_sigma')

        self.assertEqual(sigma_eos.shape, (n_spline, n_spline))
        npt.assert_array_equal(np.diag(sigma_eos),
                               (eos.get_c() * spline_var)**2)

    def test_vol_cj(self):
        """Test the CJ state when using volume
        """

        eos = EOSModel(
            lambda v: 2.56E9 / v**3,
            spline_min=0.1,
            spline_max=1.0,
            basis='volume')

        vel_cj, vol_cj, p_cj, r_line = eos._get_cj_point(1.84**-1)

        self.assertIsInstance(vel_cj, float)
        self.assertGreater(vel_cj, 0.0)

        self.assertIsInstance(vol_cj, float)
        self.assertGreater(vol_cj, 0.0)

        self.assertIsInstance(p_cj, float)
        self.assertGreater(p_cj, 0.0)

    def test_density_cj(self):
        """Test the CJ state when using density
        """

        eos = EOSModel(
            lambda r: 2.56E9 * r**3,
            spline_min=1.0,
            spline_max=10.0,
            basis='density')
        # import pdb
        # pdb.set_trace()
        vel_cj, vol_cj, p_cj, r_line = eos._get_cj_point(1.84**-1)

        self.assertIsInstance(vel_cj, float)
        self.assertGreater(vel_cj, 0.0)

        self.assertIsInstance(vol_cj, float)
        self.assertGreater(vol_cj, 0.0)

        self.assertIsInstance(p_cj, float)
        self.assertGreater(p_cj, 0.0)

class TestBumpEOS(unittest.TestCase):
    """Test of the bump EOS
    """
    def test_instantiation(self):
        """Tests that the object is properly instantiated
        """
        bump_eos = EOSBump()

        self.assertEqual(bump_eos.get_option('const_C'), 2.56e9)
        self.assertEqual(bump_eos.get_option('bumps')[0][0], 0.4)
        self.assertEqual(bump_eos.get_option('bumps')[0][1], 0.1)
        self.assertEqual(bump_eos.get_option('bumps')[0][2], 0.25)

    def test_custom_instatntiation(self):
        """Test non default instantiation
        """
        bump_eos = EOSBump(const_C=6e-3,
                           bumps=[(0.25, 0.07, 0.3),
                                  (0.35, 0.08, 0.4),
                                  ])

        bump_eos(0.25)

        self.assertEqual(bump_eos.get_option('const_C'), 6e-3)
        self.assertEqual(bump_eos.get_option('bumps')[0][0], 0.25)
        self.assertEqual(bump_eos.get_option('bumps')[0][1], 0.07)
        self.assertEqual(bump_eos.get_option('bumps')[0][2], 0.3)
        self.assertEqual(bump_eos.get_option('bumps')[1][0], 0.35)
        self.assertEqual(bump_eos.get_option('bumps')[1][1], 0.08)
        self.assertEqual(bump_eos.get_option('bumps')[1][2], 0.4)

    def test_bad_instatntiation(self):
        """Test improper instantiation
        """
        pass

    def test_call(self):
        """Test that the bump EOS can be called
        """
        bump_eos = EOSBump()

        vol = np.logspace(np.log10(.1), np.log10(1), 50)

        pressure = bump_eos(vol)

        self.assertIsInstance(pressure, np.ndarray)
        self.assertEqual(50, len(pressure))

    def test_derivative(self):
        """Test the derivative function
        """
        bump_eos = EOSBump()

        vol = np.logspace(np.log10(.1), np.log10(1), 50)

        pressure = bump_eos.derivative()(vol)

        self.assertIsInstance(pressure, np.ndarray)
        self.assertEqual(50, len(pressure))

    def test_bad_derivative(self):
        """Tests that derivative errors are caught
        """
        bump_eos = EOSBump()

        vol = np.logspace(np.log10(.1), np.log10(1), 50)

        with self.assertRaises(IOError):
            pressure = bump_eos.derivative(order=2)(vol)
        # end

        p_fun = lambda v: 2.56e9 / v**3


class TestPlot(unittest.TestCase):
    def setUp(self):
        p_fun = lambda v: 2.56e9 / v**3

        self.indep = np.linspace(0.2, 1.0, 200)
        self.model1 = EOSModel(p_fun)

        dof = self.model1.get_dof()
        self.model2 = self.model1.update_dof(dof * 0.95)
    # end

    def test_plot(self):
        """Test of basic plotting
        """

        self.model1.plot()

        plt.figure()
        ax1 = plt.gca()
        self.model1.plot(axes=ax1, style='-r')

        with self.assertRaises(TypeError):
            self.model1.plot(axes='invalid axis object')
        # end

    # @unittest.skip('no')
    def test_diff(self):
        """Test diff plotting
        """

        self.model1.plot_diff([self.model1, self.model2])

        ax1 = plt.figure().gca()
        self.model1.plot_diff([self.model1, self.model2], axes=ax1)

    def test_basis(self):
        self.model1.plot_basis()

if __name__ == '__main__':
    unittest.main(verbosity=4)
