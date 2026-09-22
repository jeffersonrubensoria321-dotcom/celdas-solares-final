"""Pruebas independientes de conservación, tendencias y ecuación implícita."""
import unittest
import itertools
import numpy as np
from modelo import *

class PhysicsTests(unittest.TestCase):
    def test_acceptance(self):
        table=validations(dict(DEFAULTS))
        self.assertTrue(table.Veredicto.str.startswith('APROBADO').all())

    def test_spectral_conservation_and_trend(self):
        previous=np.inf
        for eg in np.linspace(.5,3,20):
            s=spectral(eg)
            self.assertAlmostEqual(s['sub']+s['therm']+s['useful'],s['pin'],places=9)
            self.assertLessEqual(s['jl'],previous); previous=s['jl']

    def test_all_switch_combinations(self):
        p=dict(DEFAULTS)
        for flags in itertools.product([False,True],repeat=8):
            r=cascade(p,list(flags))
            self.assertLess(abs(r['residual']),1e-9)
            self.assertTrue(np.isfinite(r['eta']))
            self.assertTrue(0<=r['eta']<=100)

    def test_diode_equation(self):
        for rs,rp in [(0,np.inf),(.4,3000),(3,100)]:
            jl=.0435;j0=1e-12;t=300
            d=diode(jl,j0,t,rs,rp)
            u=d['v']+rs*d['j']
            residual=d['j']-(jl-j0*np.expm1(u/(K_EV*t))-u/rp)
            self.assertLess(np.max(abs(residual)),1e-12)
            self.assertLess(abs(d['j'][-1]),1e-10)
            self.assertTrue(0<d['ff']<1)

    def test_full_physical_cascade(self):
        p=dict(DEFAULTS)
        c=cascade(p)
        self.assertAlmostEqual(c['eta'],c['physical']['eta'],places=8)
        self.assertGreater(cascade(p,[1,1,1,1,0,0,0,0])['eta'],c['eta'])

    def test_thermal_trend(self):
        df=thermal_curve(dict(DEFAULTS))
        self.assertGreater(df.jsc.iloc[-1],df.jsc.iloc[0])
        self.assertLess(df.voc.iloc[-1],df.voc.iloc[0])
        self.assertLess(df.eta.iloc[-1],df.eta.iloc[0])

    def test_edge_parameters(self):
        for eg in [.5,1.12,3.]:
            p=dict(DEFAULTS,eg=eg,tau_us=10.,sf=1e5,sr=1e5,rs=3.,rp=100.)
            d=cascade(p)
            self.assertTrue(np.isfinite(d['eta']))
            self.assertGreaterEqual(d['eta'],0)

if __name__=='__main__': unittest.main()
