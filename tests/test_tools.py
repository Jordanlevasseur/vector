from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from vector_core.tools import compute,run_tool
from vector_core.memory import Memory
from vector_core.config import Config
from vector_core.portable import export_vector,restore_vector
from vector_core.persistence import records

class ToolTests(unittest.TestCase):
    def test_known_arithmetic_and_dimensions(self):
        self.assertEqual(Decimal(compute('arithmetic',{'expression':'0.1+0.2'})['value']),Decimal('.3'))
        result=compute('arithmetic',{'expression':'mass*acceleration','variables':{'mass':{'value':2,'unit':'kg'},'acceleration':{'value':3,'unit':'m/s^2'}}})
        self.assertEqual(Decimal(result['value']),6);self.assertEqual(result['si_dimensions'][:3],[1,1,-2])
        with self.assertRaises(ValueError):compute('arithmetic',{'expression':'x+y','variables':{'x':{'value':1,'unit':'m'},'y':{'value':1,'unit':'s'}}})
    def test_conversions_temperature_and_linear_verification(self):
        self.assertEqual(Decimal(compute('convert',{'value':1,'from':'ft','to':'m'})['value']),Decimal('.3048'))
        self.assertEqual(Decimal(compute('convert',{'value':0,'from':'degC','to':'K'})['value']),Decimal('273.15'))
        self.assertAlmostEqual(float(compute('convert',{'value':32,'from':'degF','to':'degC'})['value']),0,places=30)
        result=compute('solve_linear',{'a':2,'b':3,'c':11});self.assertEqual(Decimal(result['x']),4);self.assertEqual(Decimal(result['residual']),0)
        with self.assertRaises(ValueError):compute('convert',{'value':-1,'from':'K','to':'degC'})
        with self.assertRaises(ValueError):compute('convert',{'value':1,'from':'m','to':'kg'})
    def test_geometry_statistics_and_versioned_constants(self):
        result=compute('geometry',{'shape':'rectangle','dimensions':[2,3],'unit':'m'});self.assertEqual(Decimal(result['value']),6);self.assertEqual(result['si_dimensions'][0],2)
        self.assertAlmostEqual(float(compute('geometry',{'shape':'circle','dimensions':[1],'unit':'m'})['value']),3.141592653589793)
        stats=compute('statistics',{'values':[1,2,3,4]});self.assertEqual(Decimal(stats['mean']),Decimal('2.5'));self.assertAlmostEqual(float(stats['sample_variance']),5/3)
        self.assertEqual(compute('constant',{'name':'c'})['value'],'299792458');self.assertTrue(compute('constant',{'name':'h'})['exact'])
    def test_invalid_code_overflow_resource_and_authorization(self):
        for expression in ('__import__("os").system("id")','(1).__class__','2**999999','1/0','1e101','[x for x in range(10)]'):
            with self.assertRaises(ValueError):compute('arithmetic',{'expression':expression})
        with self.assertRaises(ValueError):compute('statistics',{'values':[1]*10001})
        with self.assertRaises(ValueError):compute('solve_linear',{'a':0,'b':1,'c':2})
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            with Memory(Config.load(data_dir=str(base/'data'))) as memory:
                with self.assertRaises(PermissionError):run_tool(memory,'arithmetic',{'expression':'2+2'})
                record=run_tool(memory,'arithmetic',{'expression':'2+2'},authorized=True)
                self.assertEqual(record['status'],'ok')
                export_vector(memory,base/'archive')
            target=Config.load(data_dir=str(base/'restored'));restore_vector(target,base/'archive')
            with Memory(target) as memory:self.assertEqual(records(memory,'tool_runs')['items'][0]['payload']['result']['value'],'4')
