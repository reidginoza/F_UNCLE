#/usr/bin/pyton
"""

pyGunModel

Toy computational experiment to

Authors
-------

- Stephen Andrews (SA)
- Andrew M. Fraiser (AMF)

Revisions
---------

0 -> Initial class creation (03-16-2016)

ToDo
----

None


"""

# =========================
# Python Standard Libraries
# =========================

import sys
import os
import pdb
import copy
import unittest

# =========================
# Python Packages
# =========================
import numpy as np

from scipy.interpolate import InterpolatedUnivariateSpline as IU_Spline
# For scipy.interpolate.InterpolatedUnivariateSpline. See:
# https://github.com/scipy/scipy/blob/v0.14.0/scipy/interpolate/fitpack2.
# from scipy.integrate import quad 
from scipy.integrate import odeint

# =========================
# Custom Packages
# =========================
sys.path.append(os.path.abspath('./../../'))
from F_UNCLE.Experiments.Experiment import Experiment
from F_UNCLE.Models.Isentrope import EOSBump, EOSModel, Isentrope


# =========================
# Main Code
# =========================
class Gun(Experiment):
    """A toy physics model representing a gun type experiment

    Attributes:
        const(dict): A dictionary of conversion factors

    """
    def __init__(self, eos, name='Gun Toy Computational Experiment', *args, **kwargs):
        """Instantiate the Experiment object

        Args:
            eos(Isentrope): The equation of state model used in the toy computational experiment

        Keyword Args:
            name(str): A name. (Default = 'Gun Toy Computational Experiment')

        """

        if isinstance(eos, Isentrope):
            self.eos = eos
        else:
            raise TypeError('{:} Equation of state model must be an Isentrope object'\
                            .format(self.get_inform(2)))
        # end

        def_opts = {
            'x_i': [float, 0.4, 0.0, None, 'cm',
                    'Initial position of projectile'],
            'x_f': [float, 4.0, 0.0, None, 'cm',
                    'Final/muzzle position of projectile'],
            'm': [float, 100.0, 0.0, None, 'g',
                  'Mass of projectile'],
            'mass_he': [float, 1.0, 0.0, None, 'g',
                        'The initial mass of high explosives used to drive\
                        the projectile'],
            'area': [float, 1e-4, 0.0, None, 'm**2',
                     'Projectile cross section'],
            'sigma': [float, 1.0e-0, 0.0, None, '??',
                    'Variance attributed to v measurements'],
            't_min': [float, 5.0e-6, 0.0, None, 'sec',
                      'Range of times for t2v spline'],
            't_max': [float, 110.0e-6, 0.0, None, 'sec',
                      'Range of times for t2v spline'],
            'n_t': [int, 500, 0, None, '',
                    'Number of times for t2v spline']
        }

        self.const = {'newton2dyne':1e5,
                      'cm2km':1.0e5}

        Experiment.__init__(self, name=name, def_opts=def_opts, *args, **kwargs)


    def _on_str(self, *args, **kwargs):
        """Print method of the gun model

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Return:
            (str): A string representing the object
        """

        out_str = '\n'
        out_str += 'Equation of State Model\n'
        out_str += '-----------------------\n'
        out_str += str(self.eos)

        return out_str

    def _get_force(self, posn):
        """Calculates the force on the prjectile

        The force is the pressure of the HE gas acting on the projectile.
        The pressure is given by the EOS model

        Args:
            posn(float): The scalar position

        Retun
            (float): The force in dynes

        """
        area = self.get_option('area')
        mass_he = self.get_option('mass_he')

        return self.eos(posn * area / mass_he) * area  * self.const['newton2dyne']

    # def _e(self, x):
    #     """Integrates the force up to position x

    #     Args:
    #         x(float): Scalar position

    #     Return:
    #         (float): The intergral of the foce over the distance to x

    #     """

    #     x_i = self.get_option('x_i')
    #     x_f = self.get_option('x_f')

    #     rv, err = quad(self._f, x_i, min(x,x_f))

    #     if np.isnan(rv):
    #         raise Exception("{:} NaN encountered when intergating energy"\
    #                         .format(self.get_inform(1)))
    #     # end

    #     return rv

    # def _x_dot(self, x):
    #     """Calculate the projectile velocity

    #     Calculates at a single position x, or
    #     if x is an array, calculate the velocity for each element of x

    #     Args:
    #        x(float or np.ndarray): scalar position

    #     Return
    #        (np.ndarray): velocity
    #     """
    #     x_i = self.get_option('x_i')
    #     x_f = self.get_option('x_f')
    #     m = self.get_option('m')

    #     if isinstance(x, np.ndarray):
    #         return np.array([self._x_dot(x_) for x_ in x])
    #     elif isinstance(x, (float,np.float)):
    #         if x <= x_i:
    #             return 0.0
    #         # assert(self._E(x) > =0.0),'E(%s)=%s'%(x,self._E(x))
    #         return np.sqrt(2*self._E(x)/m) # Invert E = (mv^2)/2
    #     else:
    #         raise TypeError('x has type %s'%(type(x),))
    #     # end

    def _shoot(self):
        """ Run a simulation and return the results: t, [x,v]

        Solves the ODE

        .. math::

           F(x,v,t) = \\frac{d}{dt} (x, v)

        Args:
           None

        Return:
            (np.ndarray): time vector
            (list): elements are
                - [0] -> np.ndarray: position
                - [1] -> np.ndarray: velocity
        """
        t_min = self.get_option('t_min')
        t_max = self.get_option('t_max')
        n_t = self.get_option('n_t')
        x_i = self.get_option('x_i')
        x_f = self.get_option('x_f')
        proj_mass = self.get_option('m')

        def diffeq(state, time):
            """vector field for integration

            Args:
               state (list): state variable [position, velocity]
               time (numpy.ndarray): time

            Return:
               (float): velocity
               (float): acceleration

            .. math::

               F((position,velocity),t) = \frac{d}{dt} (position,velocity)

            """

            if time < 0:
                return np.zeros(2)
            if state[0] > x_f: # beyond end of gun barrel, muzzle
                accel = 0.0
            else:
                accel = self._get_force(state[0])/proj_mass # F = MA
            return np.array([state[1], accel])

        time_list = np.linspace(t_min, t_max, n_t)
        xv_states = odeint(
            diffeq,            #
            [x_i, 0],
            time_list,
            atol=1e-11, # Default 1.49012e-8
            rtol=1e-11, # Default 1.49012e-8
            )
        if not  xv_states.shape == (len(time_list), 2):
            raise ValueError('{} did not solve the differential equation correctly'\
                             .format(self.get_inform(1)))
        #end

        # xv is array of calculated positions and velocities at times in t
        return time_list, xv_states

    def _fit_t2v(self, vel, time):
        """Fits a cubic spline to the velocity-time history

        This allows simulations and experiments to be compared at the
        experimental timestamps

        Args:
           vel(np.ndarray): Velocity history
           time(np.ndarray): Time history

        Return
           (Spline): Spline of vel = f(time)

        """

        pass

    def __call__(self, *args, **kwargs):
        """Performs the simulation / experiment using the internal EOS

        Args:

        Returns:
           (np.ndarray): Time history of the simulation
           (np.ndarray): Position history of the simulation
           (np.ndarray): Velociy history of the simulation
           (Spline): A spline representing the velocity-time history

        """

        time, states = self._shoot()

        vt_spline = self._fit_t2v(states[:, 1], time)


        return time, states[:, 0], states[:, 1], vt_spline

class TestGun(unittest.TestCase):
    """Tets of the Gun experiment
    """

    def test_instantiation(self):
        """Tests that the model is properly instantiated
        """
        eos = EOSBump()
        gun = Gun(eos)

        self.assertIsInstance(gun, Gun)
        print gun
    # end

    def test_shoot_exp_eos(self):
        """Performs a test shot using default settings
        """

        eos = EOSBump()
        gun = Gun(eos)

        time, pos, vel, spline = gun()

        n_time = gun.get_option('n_t')

        self.assertEqual(len(time), n_time)
        self.assertEqual(len(pos), n_time)
        self.assertEqual(len(vel), n_time)

    def test_shoot_model_eos(self):
        """Performs a test shot using default settings a model eos    
        """
        p_fun = lambda v: 2.56e9 / v**3
        
        eos = EOSModel(p_fun)
        gun = Gun(eos)

        print gun
        
        time, pos, vel, spline = gun()

        n_time = gun.get_option('n_t')

        self.assertEqual(len(time), n_time)
        self.assertEqual(len(pos), n_time)
        self.assertEqual(len(vel), n_time)
        
    @unittest.skip('skipped plotting routine')
    def test_shot_plot(self):
        """
        """
        import matplotlib.pyplot as plt
        
        eos = EOSBump()
        gun = Gun(eos)

        time, pos, vel, spline = gun()

        n_time = gun.get_option('n_t')

        fig = plt.figure()
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        
        
        ax1.plot(time, vel)
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Velocity')        

        eos_vect = lambda v_spec: eos(v_spec)
        eos_vect = np.vectorize(eos_vect)

        v_spec_list = np.linspace(0.25, 0.65, 30)
        ax2.plot(v_spec_list, eos_vect(v_spec_list))
        plt.show()
# end

if __name__ == '__main__':
    unittest.main(verbosity=4)