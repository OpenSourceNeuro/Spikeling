"""Active backend: independent reference, voltage-clamp experiments, real sketch.
Requires numpy, scipy and g++; run with the existing passive regression suite.
"""
import importlib.util
import math
from io import StringIO
from pathlib import Path
import subprocess
import re
import sys
import unittest
import numpy as np
import test_voltage_clamp as base

spec=importlib.util.spec_from_file_location('hh_reference',base.ROOT/'Firmware/tools/vc_hh_reference.py')
ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)


def setUpModule():
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror','-I',str(base.SKETCH),
                    str(base.HERE/'active_cell_driver.cpp'),'-o',str(base.TMP/'active')],
                   check=True,capture_output=True,text=True)
    base.compile_sketch(base.SKETCH,base.TMP/'active_sketch',True)
    for analytic in (False,True):
        args=['g++','-std=c++17','-O2','-fno-builtin-exp','-fno-builtin-expm1',
              '-I',str(base.SKETCH),str(base.HERE/'active_gate_probe.cpp'),
              '-Wl,--wrap=exp','-Wl,--wrap=expm1','-o',str(base.TMP/('gate_analytic' if analytic else 'gate_fast'))]
        if analytic:args+=['-DVC_ANALYTIC_GATES']
        subprocess.run(args,check=True,capture_output=True,text=True)


def active(commands,ideal=True,rs=5,minimum=-20,maximum=20,na=1,k=1,current=0,g=0,ge=0,dt=.1):
    lines=''.join(f'{v} {current} {g} {ge}\n' for v in commands)
    r=subprocess.run([str(base.TMP/'active'),*map(str,(int(ideal),rs,minimum,maximum,na,k,dt))],
                     input=lines,capture_output=True,text=True,check=True)
    return np.loadtxt(StringIO(r.stdout),delimiter=',',ndmin=2)


def sketch(script):
    return subprocess.run([str(base.TMP/'active_sketch')],input=script.encode(),capture_output=True,check=True).stdout


def trace(script):
    data=sketch('!VCM 1\n!VCMD -70\n!VCA 1\n!VCT 1\n'+script)
    lines=[r for r in data.decode().splitlines() if r.startswith('VC2,')]
    return np.array([[float(v) for v in r.split(',')[1:]] for r in lines])


class ActivePhysics(unittest.TestCase):
    def test_removable_singularities_are_finite(self):
        x=active([-40]*20+[-55]*20)
        self.assertTrue(np.isfinite(x).all())
        self.assertTrue(((x[:,7:10]>=0)&(x[:,7:10]<=1)).all())

    def test_ideal_matches_exact_gate_product_integrals(self):
        cmds=np.repeat([-70,-40,-20,0,50,60,-70],60)
        x=active(cmds);state=ref.initial();expected=[]
        for c in cmds:
            state,values=ref.advance(state,float(c));expected.append([*values.values()])
        # Compare explicitly by physical quantity, independent of dict order.
        state=ref.initial();maxerr=0
        for row,c in zip(x,cmds):
            state,y=ref.advance(state,float(c))
            actual=[y[k] for k in ('voltage_mV','clamp_nA','capacitive_nA','leak_nA','sodium_nA','potassium_nA','receptor_nA')]
            maxerr=max(maxerr,float(np.max(np.abs(row[:7]-actual))))
            np.testing.assert_allclose(row[7:10],state[1:],atol=2e-6,rtol=0)
        self.assertLess(maxerr,.001)

    def test_access_matches_independent_coupled_ODE(self):
        for rs in (2,5,20):
            cmds=np.repeat([-70,-20,-70],100)
            x=active(cmds,ideal=False,rs=rs,current=.05)
            p=dict(ref.DEFAULT,rs=rs);state=ref.initial();voltage_error=0;current_error=0
            for row,c in zip(x,cmds):
                state,y=ref.advance(state,float(c),inward=.05,ideal=False,parameters=p)
                voltage_error=max(voltage_error,abs(row[0]-y['voltage_mV']))
                current_error=max(current_error,abs(row[1]-y['clamp_nA']))
            self.assertLess(voltage_error,.05)
            self.assertLess(current_error,.01)

    def test_na_transient_and_delayed_k(self):
        x=active([-70]*100+[-20]*200)[100:]
        peak=np.argmin(x[:,4]);self.assertGreater(peak,0);self.assertLess(peak,40)
        self.assertLess(x[peak,4],-.1)
        self.assertLess(abs(x[-1,4]),abs(x[peak,4])*.1)
        self.assertGreater(x[-1,5],x[0,5]*10)

    def test_isolated_currents_reverse_at_their_own_E(self):
        self.assertLess(active([-20]*30,k=0)[-1,4],0)
        self.assertAlmostEqual(active([50]*30,k=0)[-1,4],0,places=7)
        self.assertGreater(active([60]*30,k=0)[-1,4],0)
        self.assertLess(active([-90]*30,na=0)[-1,5],0)
        self.assertAlmostEqual(active([-77]*30,na=0)[-1,5],0,places=7)
        self.assertGreater(active([-60]*30,na=0)[-1,5],0)

    def test_reserve_scales_only_its_own_current_in_ideal_VC(self):
        cmd=[-20]*200;control=active(cmd)
        a=active(cmd,na=.5);b=active(cmd,k=.25)
        np.testing.assert_allclose(a[:,4],control[:,4]*.5,atol=1e-7)
        np.testing.assert_allclose(a[:,5],control[:,5],atol=1e-7)
        np.testing.assert_allclose(b[:,5],control[:,5]*.25,atol=1e-7)
        np.testing.assert_allclose(b[:,4],control[:,4],atol=1e-7)

    def test_depolarised_holding_inactivates_sodium_and_hyperpolarisation_restores_it(self):
        control=active([-70]*1000+[-20]*200)[-200:]
        inactivated=active([-40]*1000+[-20]*200)[-200:]
        restored=active([-40]*1000+[-70]*1000+[-20]*200)[-200:]
        self.assertLess(abs(inactivated[:,4].min()),abs(control[:,4].min())*.3)
        self.assertGreater(abs(restored[:,4].min()),abs(control[:,4].min())*.99)

    def test_current_balance_includes_every_component(self):
        for ideal in (True,False):
            x=active([-20]*100,ideal=ideal,current=.1,g=.003,ge=-.24)
            np.testing.assert_allclose(x[:,1]+.1,x[:,2]+x[:,3]+x[:,4]+x[:,5]+x[:,6],atol=2e-5)

    def test_compliance_limits_with_active_channels(self):
        x=active([60]*100+[-110]*100,ideal=False,minimum=-.2,maximum=.2)
        self.assertLessEqual(x[:,1].max(),.200001)
        self.assertGreaterEqual(x[:,1].min(),-.200001)
        self.assertGreater(x[:,10].max(),.5)


class ActiveFirmware(unittest.TestCase):
    def test_active_protocol_and_original_cc_outputs(self):
        x=trace('!VCI 1\n!VSTEP -20 1 20\nR250\n')
        self.assertEqual(x.shape,(250,17));self.assertTrue((x[:,8]==0).all())
        self.assertLess(x[:,11].min(),-.1)
        self.assertGreater(x[:,12].max(),.1)
        data=sketch('!VCM 1\n!VCA 1\n!VCI 1\n!VCMD 60\nR2\nS\n!VCM 0\nR1\nS\n')
        states=[r for r in data.decode(errors='ignore').splitlines() if r.startswith('STATE,')]
        for s in states:self.assertEqual(s.split(',')[4:6],['0','0'])

    def test_supported_and_unsupported_drugs_are_distinguished(self):
        a=trace('!PH E 1\n!PH D 0 9.2\n!PH D 1 .5\n!VCI 1\nR20\n')
        self.assertTrue((a[:,8]==0).all())
        b=trace('!PH E 1\n!PH D 2 2.3\nR2\n')
        self.assertTrue((b[:,8].astype(int)&32).all())

    def test_50_percent_blockade_reuses_existing_Hill_doses(self):
        a=trace('!VCI 1\n!VCMD -20\nR50\n')
        b=trace('!PH D 0 9.2\n!PH E 1\n!VCI 1\n!VCMD -20\nR50\n')
        np.testing.assert_allclose(b[:,11],a[:,11]*.5,atol=1e-6)
        np.testing.assert_allclose(b[:,12],a[:,12],atol=1e-6)

    def test_photodiode_noise_and_digital_synapse_still_contribute(self):
        for cmd in ('!NO1 20\n','!PG1 10\nA1 5 2400\n','!SG11 40\nD38 1\n'):
            x=trace('!VCI 1\n'+cmd+'R30\n')
            self.assertGreater(x[:,7].max(),.001)

    def test_conductance_synapse_has_correct_reversal_and_blockade(self):
        def run(v,dose=0):
            return trace(f'!PH M 1\n!PH R 1 1\n!PH D 4 {dose}\n!PH E 1\n'
                         f'!VCI 1\n!VCMD {v}\n!SG11 40\nD38 1\nR5\n')
        self.assertLess(run(-70)[-1,13],0)
        self.assertAlmostEqual(run(0)[-1,13],0,places=6)
        self.assertGreater(run(20)[-1,13],0)
        np.testing.assert_allclose(run(-70,.3)[:,13],run(-70)[:,13]*.5,atol=1e-6)

    def test_gaba_reversal_and_gabazine_share_existing_receptor_state(self):
        def run(v,dose=0):
            return trace(f'!PH M 1\n!PH R 1 2\n!PH D 5 {dose}\n!PH E 1\n'
                         f'!VCI 1\n!VCMD {v}\n!SG11 -40\nD38 1\nR5\n')
        self.assertLess(run(-90)[-1,13],0)
        self.assertAlmostEqual(run(-80)[-1,13],0,places=6)
        self.assertGreater(run(-70)[-1,13],0)
        np.testing.assert_allclose(run(-70,.9)[:,13],run(-70)[:,13]*.5,atol=1e-6)

    def test_nmda_APV_changes_current_without_resampling_release(self):
        def run(nmda,dose=0):
            return trace(f'!PH M 1\n!PH R 1 1\n!PH N {nmda}\n!PH D 6 {dose}\n!PH E 1\n'
                         '!VCI 1\n!VCMD -20\n!SG11 40\nD38 1\nR100\n')
        fast=run(0)[:,13];full=run(1)[:,13];half=run(1,3.7)[:,13]
        self.assertLess((full-fast).min(),-.001)
        np.testing.assert_allclose(half-fast,(full-fast)*.5,atol=2e-6)

    def test_release_rng_draws_once_per_event_not_per_HH_substep(self):
        command='!PH E 1\n!PH L 1 1\n!PH Z 123\n!SG11 40\nD38 1\nR1\nD38 0\nR50\nP\n'
        a=sketch(command).decode(errors='ignore')
        b=sketch('!VCM 1\n!VCA 1\n!VCMD -70\n'+command).decode(errors='ignore')
        self.assertEqual(a[a.rfind('PHARM,'):],b[b.rfind('PHARM,'):])

    def test_active_selection_does_not_reset_charge_or_change_CC_equations(self):
        common='!PC1 15\nR300\n'
        self.assertEqual(sketch(common),sketch('!VCA 1\n'+common))
        a=sketch('!VCM 1\n!VCI 1\n!VCMD -20\nR2\nS\n!VCA 1\nS\n!VCA 0\nS\n')
        states=re.findall(r'STATE,([^,]+),',a.decode(errors='ignore'))
        self.assertEqual(states,['-20','-20','-20'])

    def test_invalid_command_does_not_change_membrane_or_gate_state(self):
        control=trace('!VCI 1\n!VCMD -20\nR20\n')
        rejected=trace('!VCI 1\n!VCMD -20\n!VCA 2\n!VCMD 90\nR20\n')
        np.testing.assert_allclose(np.delete(control,8,axis=1),np.delete(rejected,8,axis=1),atol=1e-7)
        self.assertTrue((rejected[:,8].astype(int)&2).all())


class HardwareAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(base.ROOT/'Firmware/tools'))
        import run_active_vc_tests as tool
        cls.tool=tool
        cls.rows=[dict(zip(tool.FIELDS,r),wall_s=i*.002,phase='baseline')
                  for i,r in enumerate(trace('!VCI 1\n!VSTEP -20 10 20\nR1710\n'))]

    def test_valid_native_recording_passes(self):
        self.assertTrue(self.tool.assess(self.rows,self.tool.CASES[0])['all_passed'])

    def test_fast_cadence_fails_despite_correct_equations(self):
        rows=[dict(r,wall_s=r['wall_s']*.75) for r in self.rows]
        result=self.tool.assess(rows,self.tool.CASES[0])
        self.assertTrue(result['numerical_passed']);self.assertFalse(result['all_passed'])

    def test_reported_deadline_fails_despite_correct_equations(self):
        rows=[dict(r) for r in self.rows];rows[100]['flags']=64
        result=self.tool.assess(rows,self.tool.CASES[0])
        self.assertTrue(result['numerical_passed']);self.assertFalse(result['all_passed'])

    def test_missing_sodium_component_fails(self):
        rows=[dict(r,sodium_nA=0) for r in self.rows]
        self.assertFalse(self.tool.assess(rows,self.tool.CASES[0])['all_passed'])

    def test_sample_gap_is_rejected(self):
        rows=self.rows[:200]+self.rows[201:]
        with self.assertRaises(ValueError):self.tool.assess(rows,self.tool.CASES[0])


class GateOptimisation(unittest.TestCase):
    def count(self,analytic=False,mode='ideal',dt=.1):
        return int(subprocess.check_output([str(base.TMP/('gate_analytic' if analytic else 'gate_fast')),
                       mode,str(dt)],input=b'-20\n'))

    def test_ideal_hot_path_eliminates_all_72_gate_special_functions(self):
        self.assertEqual(self.count(analytic=True),72)
        self.assertEqual(self.count(),0)

    def test_access_hot_path_retains_only_exact_voltage_exponentials(self):
        self.assertEqual(self.count(analytic=True,mode='access'),80)
        self.assertEqual(self.count(mode='access'),8)

    def test_nonstandard_dt_uses_analytic_fallback(self):
        self.assertEqual(self.count(dt=.08),72)
        x=active([-20]*50,dt=.08);state=ref.initial()
        for r in x:
            state,y=ref.advance(state,-20,dt=.08)
            self.assertLess(abs(r[1]-y['clamp_nA']),.003)

    def test_dense_table_interpolation_agrees_with_analytic_rates(self):
        volts=np.r_[-250.,250.,-55.,-40.,np.arange(-250,250,.03125)+.015625]
        data=''.join(f'{v:.8f}\n' for v in volts)
        r=subprocess.run([str(base.TMP/'gate_fast'),'table'],input=data,text=True,capture_output=True,check=True)
        actual=np.loadtxt(StringIO(r.stdout),delimiter=',')
        expected=np.array([[*[a for a,b in ref.rates(v)],
                            *[-math.expm1(-b*.0125) for a,b in ref.rates(v)]] for v in volts])
        self.assertTrue(((actual>=0)&(actual<=1)).all())
        self.assertLess(float(np.max(np.abs(actual[:,:3]-expected[:,:3]))),.00002)
        self.assertLess(float(np.max(np.abs(actual[:,3:]-expected[:,3:]))),.00002)

    def test_off_grid_protocol_matches_independent_current_reference(self):
        cmds=np.repeat([-70.125,-55.125,-39.875,-20.125,.125,49.875,60.125,-69.875],60)
        x=active(cmds);state=ref.initial()
        for r,c in zip(x,cmds):
            state,y=ref.advance(state,float(c))
            self.assertLess(abs(r[1]-y['clamp_nA']),.003)
            np.testing.assert_allclose(r[7:10],state[1:],atol=.00003,rtol=0)

    def test_table_is_reproducible_from_generator(self):
        subprocess.run([sys.executable,str(base.ROOT/'Firmware/tools/generate_vc_gate_table.py'),'--check'],
                       check=True,capture_output=True,text=True)
