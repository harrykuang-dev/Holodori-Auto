"""Display setup tests use fake APIs; the local desktop never changes."""
import os
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
from tools.configure_ci_display import configure


class DisplayTests(unittest.TestCase):
    def api(self):
        state=[1024,768]
        modes=[SimpleNamespace(PelsWidth=w,PelsHeight=h,BitsPerPel=32,DisplayFrequency=60)
               for w,h in ((1024,768),(2560,1440),(1920,1080))]
        def change(mode,flags):
            if flags == 0:state[:]=[mode.PelsWidth,mode.PelsHeight]
            return 0
        api=SimpleNamespace(error=OSError,GetSystemMetrics=lambda index:state[index],
                            EnumDisplaySettings=Mock(side_effect=modes+[OSError('end')]),
                            ChangeDisplaySettings=Mock(side_effect=change))
        return api,SimpleNamespace(CDS_TEST=2,DISP_CHANGE_SUCCESSFUL=0)

    def test_local_read_only_probe_does_not_change_display(self):
        api,constants=self.api()
        result=configure(api,constants,width=1920,height=1080)
        self.assertFalse(result['ready'])
        api.ChangeDisplaySettings.assert_not_called()

    def test_apply_is_rejected_outside_ci(self):
        api,constants=self.api()
        with patch.dict(os.environ,{},clear=True),self.assertRaises(RuntimeError):
            configure(api,constants,width=1920,height=1080,apply=True)
        api.ChangeDisplaySettings.assert_not_called()

    def test_ci_selects_smallest_supported_sufficient_mode_and_verifies_it(self):
        api,constants=self.api()
        with patch.dict(os.environ,GITHUB_ACTIONS='true',RUNNER_OS='Windows'):
            result=configure(api,constants,width=1920,height=1080,apply=True)
        self.assertTrue(result['ready'])
        self.assertEqual(result['after'],[1920,1080])
        self.assertEqual(len(api.ChangeDisplaySettings.call_args_list),2)

    def test_rejected_modes_fail_instead_of_skipping_gui_tests(self):
        api,constants=self.api();api.ChangeDisplaySettings.side_effect=None
        api.ChangeDisplaySettings.return_value=-2
        with patch.dict(os.environ,GITHUB_ACTIONS='true',RUNNER_OS='Windows'),self.assertRaises(RuntimeError):
            configure(api,constants,width=1920,height=1080,apply=True)
