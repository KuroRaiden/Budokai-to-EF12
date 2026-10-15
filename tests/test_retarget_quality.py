import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline.retarget_quality import movement_scale, floor_correction, continuous_euler
from mesh_preview import MeshPreviews

class RetargetQualityTests(unittest.TestCase):
    def test_movement_scales_with_character(self):
        source={'lleg1':(0,0,4),'lleg2':(0,0,2),'lfoot1':(0,0,0)}
        target={name:tuple(1.7*x for x in point) for name,point in source.items()}
        self.assertAlmostEqual(movement_scale(source,target),1.7)

    def test_missing_scale_segments_rejected(self):
        with self.assertRaises(ValueError):movement_scale({}, {})

    def test_airborne_clearance_is_not_grounded(self):
        current=[.2,.5];lift=floor_correction(current,[0,0],[3,4],2)
        self.assertAlmostEqual(min(x-lift for x in current),6)

    def test_grounded_pose_stays_on_bind_floor(self):
        current=[.4,1.2];lift=floor_correction(current,[-.01,-.01],[0,.1],1.1)
        self.assertAlmostEqual(min(x-lift for x in current),-.01)

    def test_euler_crosses_wrap_without_full_turn(self):
        old=(math.radians(179),0,0)
        new=continuous_euler((math.radians(-179),0,0),old)
        self.assertAlmostEqual(new[0]-old[0],math.radians(2))

    def test_preview_invalidated_when_retargeter_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);scripts=root/'work/ef12';scripts.mkdir(parents=True)
            file=scripts/'retarget_shin_goku.py';file.write_text('# original')
            first=MeshPreviews(root,{'workspace':str(root)},None,None)
            file.write_text('# new algorithm')
            second=MeshPreviews(root,{'workspace':str(root)},None,None)
            self.assertNotEqual(first.version,second.version)
            first.pool.shutdown();second.pool.shutdown()

if __name__=='__main__':unittest.main()
