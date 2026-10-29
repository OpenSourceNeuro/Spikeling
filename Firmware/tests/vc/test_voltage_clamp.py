"""Real portable C++ solver + actual sketch/serial parser with deterministic IO.

Run from repo root: python -m unittest discover -s Firmware/tests/vc -v
Dependencies: Python, numpy, g++, git (pinned baseline commit available locally).
"""
from pathlib import Path
from io import StringIO
import math
import re
import importlib.util
import struct
import subprocess
import tempfile
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
SKETCH=ROOT/'Firmware/Spikeling_V3'
BASE='927a70abb46f2b189af1bbe4647a7e7a58c9d2a8'
LIB=ROOT/'Firmware/Librairies/Arduino-SerialCommand/src'
BUILD=tempfile.TemporaryDirectory(prefix='spikeling-vc-tests-')
TMP=Path(BUILD.name)


def compile_sketch(directory,output,prototype=False):
    args=['g++','-std=gnu++17','-O2','-ffp-contract=off','-DARDUINO=10819']
    if prototype:args+=['-DVC_PROTOTYPE_TEST']
    args+=['-I',str(HERE/'stubs'),'-I',str(directory),'-I',str(LIB),
           str(HERE/'sketch_driver.cpp'),str(LIB/'SerialCommand.cpp'),'-o',str(output)]
    subprocess.run(args,check=True,capture_output=True,text=True)


def setUpModule():
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror','-I',str(SKETCH),
                    str(HERE/'cell_driver.cpp'),'-o',str(TMP/'cell')],check=True,capture_output=True,text=True)
    compile_sketch(SKETCH,TMP/'sketch',True)
    original=TMP/'baseline';original.mkdir()
    for name in ['Core_functions.h','General_settings.h','Serial_functions.h','Izhikevich_parameters.h','Spikeling_V3.ino']:
        data=subprocess.run(['git','show',f'{BASE}:Firmware/Spikeling_V3/{name}'],cwd=ROOT,check=True,capture_output=True).stdout
        (original/name).write_bytes(data)
    compile_sketch(original,TMP/'original')


def cell(commands,mode=0,cm=20,rm=500,rs=5,el=-70,imin=-20,imax=20,v0=-70,dt=.1,current=0,g=0,ge=0):
    commands=np.asarray(commands)
    current=np.broadcast_to(current,commands.shape)
    lines=''.join(f'{v} {i} {g} {ge}\n' for v,i in zip(commands,current))
    result=subprocess.run([str(TMP/'cell'),*map(str,[mode,cm,rm,rs,el,imin,imax,v0,dt])],input=lines,text=True,capture_output=True,check=True)
    return np.loadtxt(StringIO(result.stdout),delimiter=',',ndmin=2)


def sketch(script,baseline=False):
    return subprocess.run([str(TMP/('original' if baseline else 'sketch'))],input=script.encode(),capture_output=True,check=True).stdout


def diagnostic(script):
    data=sketch('!VCM 1\n!VCMD -70\n!VCT 1\n'+script)
    lines=[line for line in data.decode().splitlines() if line.startswith('VC1,')]
    return np.array([[float(x) for x in line.split(',')[1:]] for line in lines])


class PortablePhysics(unittest.TestCase):
    def test_rc_endpoint_mean_and_charge_across_parameter_ranges(self):
        # Extended precision reference checks the physical interval solution,
        # including slow charging and near-instant settling. The recorded float
        # Vm is the next interval's initial condition, as on the device.
        commands=np.r_[np.repeat(-70.,5),np.repeat(-69.,10),np.repeat(-71.,10)]
        ld=np.longdouble
        for cm in (1,20,100,1000):
            for rm in (10,500,10000):
                for rs in (.1,5,100):
                    for dt in (.0001,.1,1):
                        x=cell(commands,cm=cm,rm=rm,rs=rs,dt=dt,current=.01,imin=-100,imax=100)
                        initial=np.r_[-70.,x[:-1,0].astype(np.float32)].astype(ld)
                        cap=ld(np.float32(cm))/1000
                        gl=1/ld(np.float32(rm));ga=1/ld(np.float32(rs))
                        delta=ld(np.float32(dt));inward=ld(np.float32(.01))
                        eq=(commands.astype(ld)*ga-70*gl+inward)/(gl+ga)
                        z=(gl+ga)*delta/cap
                        endpoint=eq+(initial-eq)*np.exp(-z)
                        mean=eq+(initial-eq)*(-np.expm1(-z))/z
                        np.testing.assert_allclose(x[:,0],endpoint,atol=8e-6,rtol=0)
                        np.testing.assert_allclose(x[:,1],(commands-mean)*ga,atol=2e-6,rtol=0)
                        np.testing.assert_allclose(x[:,2],cap*(endpoint-initial)/delta,atol=2e-6,rtol=0)
                        np.testing.assert_allclose(x[:,3],gl*(mean+70),atol=2e-6,rtol=0)

    def test_passive_rc_matches_analytic(self):
        for rs in [.1,2,5,20,100]:
            x=cell(np.repeat(-60.,100),rs=rs)
            rate=(1/rs+1/500)/.02;eq=(-60/rs-70/500)/(1/rs+1/500)
            expected=eq+(-70-eq)*np.exp(-np.arange(1,101)*.1*rate)
            # Float state is rounded each output tick; allow a few accumulated ULPs.
            np.testing.assert_allclose(x[:,0],expected,atol=3e-5,rtol=0)

    def test_recorded_current_is_interval_mean(self):
        x=cell(np.repeat(-60.,40))
        v0=np.r_[-70,x[:-1,0]];cm=.02;gl=1/500;ga=1/5;eq=(-60*ga-70*gl)/(ga+gl)
        avg=eq+(v0-eq)*(-np.expm1(-.1*(ga+gl)/cm))/(.1*(ga+gl)/cm)
        np.testing.assert_allclose(x[:,1],(-60-avg)/5,atol=2e-6,rtol=0)

    def test_ideal_capacitive_charge(self):
        for dt in [.02,.1,.5]:
            x=cell(np.r_[np.repeat(-70.,10),np.repeat(-20.,10)],mode=1,dt=dt)
            self.assertAlmostEqual(x[:,2].sum()*dt,.02*50,places=6)

    def test_kirchhoff_balance_with_receptor_input(self):
        for mode in [0,1]:
            x=cell(np.r_[np.repeat(-60.,40),np.repeat(-90.,40)],mode=mode,current=.1,g=.005,ge=-.4)
            np.testing.assert_allclose(x[:,1]+.1,x[:,2]+x[:,3]+x[:,4],atol=2e-6)

    def test_external_current_changes_recorded_clamp_current(self):
        x=cell(np.repeat(-70.,100),current=1)
        self.assertAlmostEqual(x[-1,1],-500/505,places=6)
        self.assertAlmostEqual(x[-1,0],-70+500*5/505,places=5)

    def test_receptor_current_reverses(self):
        a=cell([-90],mode=1,g=.01,ge=-.8)
        b=cell([-80],mode=1,g=.01,ge=-.8)
        c=cell([-70],mode=1,g=.01,ge=-.8)
        self.assertLess(a[0,4],0);self.assertAlmostEqual(b[0,4],0,places=7);self.assertGreater(c[0,4],0)

    def test_compliance_both_polarities_and_boundary_crossings(self):
        x=cell(np.r_[np.repeat(60.,400),np.repeat(-110.,400)],imin=-.2,imax=.2)
        self.assertGreater(x[:,5].max(),.99)
        self.assertLessEqual(x[:,1].max(),.200001);self.assertGreaterEqual(x[:,1].min(),-.200001)
        self.assertLess(x[-1,5],.01)

    def test_current_limited_initial_slew(self):
        x=cell(np.repeat(60.,5),imax=.2)
        eq=-70+.2*500
        expected=eq+(-70-eq)*np.exp(-np.arange(1,6)*.1/(500*.02))
        np.testing.assert_allclose(x[:,0],expected,atol=1e-5,rtol=0)

    def test_ideal_mode_has_no_compliance_limit(self):
        x=cell([80],mode=1,imax=.2)
        self.assertGreater(x[0,1],20);self.assertEqual(x[0,5],0)

    def test_no_artificial_voltage_clip(self):
        x=cell(np.repeat(80.,200),rs=100,current=5)
        self.assertGreater(x[-1,0],100)


class ModelClock(unittest.TestCase):
    def clocks(self, script):
        return [[int(x) for x in row] for row in re.findall(rb'CLOCK,(\d+),(\d+),(\d+),(\d+)',sketch(script))]

    def test_startup_does_not_accrue_calibration_time(self):
        wall,last,period,tick=self.clocks('K\n')[0]
        self.assertGreater(wall,0)  # The host stub models the real boot calibration delays.
        self.assertEqual(last,wall)

    def test_vc_entry_discards_old_cc_schedule_debt(self):
        wall,last,period,tick=self.clocks('T1000000\n!VCM 1\nK\n')[0]
        self.assertEqual(last,wall)
        self.assertEqual(tick,0)

    def test_vc_pause_advances_once_without_a_catchup_burst(self):
        rows=self.clocks('!VCM 1\n!VCMD -70\nT1000000\nK\nL25\nK\nT1999\nK\nT1\nK\n')
        self.assertEqual([r[3] for r in rows],[1,1,1,2])
        self.assertEqual(rows[0][0],rows[0][1])

    def test_vc_late_start_reports_deadline_even_when_solver_is_fast(self):
        x=diagnostic('T1000000\nT2000\n')
        self.assertEqual(list(x[:,8].astype(int)),[64,0])

    def test_return_to_cc_reanchors_wall_clock(self):
        rows=self.clocks('!VCM 1\nT1000000\n!VCM 0\nK\nL25\nK\n')
        self.assertEqual(rows[0][0],rows[0][1])
        self.assertEqual(rows[0],rows[1])

    def test_vc_wraparound_keeps_two_millisecond_period(self):
        wall=self.clocks('K\n')[0][0]
        jump=(2**32-1000-wall)%2**32
        rows=self.clocks(f'!VCM 1\nT{jump}\nK\nT2000\nK\nL10\nK\n')
        self.assertEqual([r[3] for r in rows],[1,2,2])
        self.assertEqual(rows[1][0],1000)


class ClockAnalysis(unittest.TestCase):
    def tool(self):
        import sys
        sys.path.insert(0,str(ROOT/'Firmware/tools'))
        try:
            import verify_vc_clock
            return verify_vc_clock
        finally:
            sys.path.pop(0)

    def test_usb_batching_preserves_500_hz_acceptance(self):
        rows=[{'sequence':i+1,'wall_s':(i//4)*.008} for i in range(7000)]
        self.assertTrue(self.tool().clock_metrics(rows)['passed'])

    def test_fast_catchup_rate_fails_even_without_duration_flags(self):
        rows=[{'sequence':i+1,'wall_s':i*.0015} for i in range(7000)]
        result=self.tool().clock_metrics(rows)
        self.assertFalse(result['passed'])
        self.assertAlmostEqual(result['updates_per_second'],2000/3,places=6)

    def test_early_burst_fails_when_global_average_is_within_tolerance(self):
        wall=0.;rows=[]
        for i in range(7000):
            rows.append({'sequence':i+1,'wall_s':wall})
            wall+=.0015 if i<300 else .002
        result=self.tool().clock_metrics(rows)
        self.assertLess(result['updates_per_second'],510)
        self.assertFalse(result['passed'])


class FirmwareIntegration(unittest.TestCase):
    def test_current_clamp_matches_original_packets_for_all_presets(self):
        for preset in range(20):
            with self.subTest(preset=preset):
                scenario=f'!NEU {preset}\n!PC1 15\nR300\nD38 1\nR1\nD38 0\nR100\n!NO1 5\n!PG1 10\nA1 5 2400\nR100\n'
                self.assertEqual(sketch(scenario),sketch(scenario,True))

    def test_cc_command_is_preserved(self):
        out=sketch('!PC1 12\n!VCM 1\n!VCMD -70\n!VCM 0\nS\n').decode()
        state=out.strip().split(',');self.assertEqual(state[3],'0');self.assertEqual(state[7],'12');self.assertEqual(state[6],'0')

    def test_mode_switch_preserves_drug_state_and_rng(self):
        out=sketch('P1\nP\n!VCM 1\n!VCMD -70\n!VCT 1\nR10\n!VCM 0\nP\n').decode()
        rows=out.splitlines();p=[r for r in rows if r.startswith('PHARM,')]
        self.assertEqual(p[0],p[1])
        for row in rows:
            if row.startswith('VC1,'):self.assertEqual(int(row.split(',')[9])&32,32)

    def test_device_protocol_has_exact_sample_counts(self):
        x=diagnostic('!VSTEP -60 1 2\nR50\n')
        np.testing.assert_array_equal(x[:,2],np.r_[np.repeat(-70,10),np.repeat(-60,20),np.repeat(-70,20)])
        np.testing.assert_array_equal(x[:,0],np.arange(1,51))

    def test_noise_override_is_consumed_once(self):
        x=diagnostic('!NO1 100\nR100\n')
        np.testing.assert_allclose(x[:,7],1,atol=1e-7)
        self.assertAlmostEqual(x[-1,4],-500/505,places=5)

    def test_photodiode_current_remains_active(self):
        x=diagnostic('!PG1 10\nA1 5 2400\nR30\n')
        self.assertGreater(x[:,7].max(),0)
        self.assertLess(x[-1,4],0)

    def test_incoming_synapse_and_decay_remain_active(self):
        x=diagnostic('!SG11 40\nD38 1\nR1\nD38 0\nR20\n')
        self.assertGreater(x[0,7],0)
        self.assertGreater(x[0,7],x[-1,7])

    def test_vc_never_emits_spike_ttl(self):
        out=sketch('!VCM 1\n!VCI 1\n!VCMD 80\n!VCT 1\nR2\nS\n!VCM 0\nS\nR1\nS\n')
        # The final R1 emits a binary frame, so isolate the ASCII state lines.
        states=[line.decode().split(',') for line in re.findall(rb'STATE,[^\n]+',out)]
        self.assertEqual(states[0][4:6],['0','0']);self.assertEqual(states[1][4:6],['0','0'])
        self.assertEqual(states[2][4:6],['0','0'])

    def test_positive_command_is_independent_of_spike_peak(self):
        x=diagnostic('!VCI 1\n!VCMD 80\nR2\n')
        np.testing.assert_array_equal(x[:,3],80)

    def test_pc1_does_not_reset_cell_voltage(self):
        x=diagnostic('R20\n!PC1 -60\nR1\n')
        self.assertAlmostEqual(x[-1,3],-63.70514,places=4)

    def test_current_in_voltage_command_is_not_injected_twice(self):
        x=diagnostic('!PC1 -70\nR100\nA1 7 3500\nR100\n')
        self.assertGreater(x[-1,2],-60)
        np.testing.assert_array_equal(x[:,7],0)

    def test_direct_command_ignores_current_in_voltage_steps(self):
        x=diagnostic('R100\nA1 7 3500\nR100\n')
        np.testing.assert_array_equal(x[:,2],-70)

    def test_invalid_commands_rejected_without_mutating_state(self):
        for command in ['VCMD nan','VCMD -20junk','VCMD 90','VCP 0 500 5 -70','VCP 20 500 5 nan','VCL 5 -5','VCI 2','VSTEP -60 1 .15','VSTEP -60 1 -2','VCM junk']:
            with self.subTest(command=command):
                x=diagnostic('!'+command+'\nR1\n')
                self.assertEqual(int(x[-1,8])&2,2)
                self.assertEqual(x[-1,2],-70)
                self.assertEqual(x[-1,3],-70)

    def test_vrs_and_preset_reset_sync_cell(self):
        x=diagnostic('!VCI 1\n!VCMD -60\nR2\n!VRS\n!NEU 1\nR1\n')
        self.assertAlmostEqual(x[-1,2],-64,places=5);self.assertAlmostEqual(x[-1,3],-64,places=5)

    def test_legacy_packet_layout_is_still_18_bytes(self):
        data=sketch('!VCM 1\n!VCMD -70\nR3\n')
        self.assertEqual(len(data),54)
        for i in range(3):self.assertEqual(data[i*18:i*18+2],b'\xaa\x55')

    def test_vc_synapse_packet_uses_the_same_na_units_as_input(self):
        data=sketch('!VCM 1\n!VCMD -70\n!SG11 40\nD38 1\nR1\n')
        packet=struct.unpack('<8h',data[2:18])
        x=diagnostic('!SG11 40\nD38 1\nR1\n')
        self.assertAlmostEqual(packet[4]/100,x[0,7],delta=.0051)

    def test_return_to_cc_disables_diagnostic_stream(self):
        data=sketch('!VCM 1\n!VCT 1\n!VCM 0\nR2\n')
        self.assertEqual(len(data),36);self.assertEqual(data[:2],b'\xaa\x55')

    def test_explicit_identity_query(self):
        self.assertIn(b'VC-PASSIVE-1,mV,ms,nA,pF,MOhm',sketch('!VCINFO\n'))
        self.assertIn(b',clock=2',sketch('!VCINFO\n'))

    def test_hardware_capture_validator_accepts_native_sketch_trace(self):
        tool=load_capture_tool()
        data=sketch('!VCM 1\n!VCMD -70\n!VCT 1\n!VSTEP -60 1 2\nR50\n')
        rows=[tool.parse_sample(line) for line in data.splitlines()]
        result=tool.validate(rows)
        self.assertLess(result['max_voltage_error_mV'],.00003)

    def test_hardware_capture_validator_rejects_loss_and_first_sample_fault(self):
        tool=load_capture_tool()
        data=sketch('!VCM 1\n!VCMD -70\n!VCT 1\nR10\n')
        rows=[tool.parse_sample(line) for line in data.splitlines()]
        with self.assertRaises(ValueError):tool.validate(rows[:4]+rows[5:])
        rows[0]['flags']=4
        with self.assertRaises(ValueError):tool.validate(rows)


def load_capture_tool():
    spec=importlib.util.spec_from_file_location('capture_passive_vc',ROOT/'Firmware/tools/capture_passive_vc.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


if __name__=='__main__':unittest.main()
