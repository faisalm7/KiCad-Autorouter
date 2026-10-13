"""Pure API misuse controls; actual via native witness is a separate gate."""
from types import SimpleNamespace
import unittest
from autorouter.floor_context import route_width


class Via:
    def __init__(self,widths=(1500000,1500000),kind=4,layers=(0,2)):
        self.widths=dict(zip((0,2),widths));self.kind=kind;self.layers=layers;self.calls=[]
    def GetWidth(self,layer):
        self.calls.append(layer);return self.widths[layer]
    def GetViaType(self):return self.kind
    def IsOnLayer(self,layer):return layer in self.layers


class WidthObservation(unittest.TestCase):
    api=SimpleNamespace(PCB_VIA=Via,F_Cu=0,B_Cu=2)
    def test_uniform_via_reads_both_explicit_layer_diameters(self):
        via=Via();self.assertEqual(route_width(via,self.api),1500000)
        self.assertEqual(via.calls,[0,2])
    def test_nonuniform_zero_blind_or_missing_layer_reject(self):
        for via in (Via((1000000,1500000)),Via((0,0)),Via(kind=3),Via(layers=(0,))):
            with self.subTest(via=via),self.assertRaises(ValueError):route_width(via,self.api)
    def test_segment_keeps_ordinary_width_call(self):
        self.assertEqual(route_width(SimpleNamespace(GetWidth=lambda:300000),self.api),300000)
