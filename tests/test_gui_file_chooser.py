"""Deferred native chooser lifetime controls; real Cocoa qualification is separate."""
from pathlib import Path
import json
from types import SimpleNamespace
from unittest.mock import Mock
import tempfile
import unittest
from tests.test_gui import window_method
from autorouter import preferences as pref

class FileChooserTests(unittest.TestCase):
    def chooser(self):
        callback=window_method('choose_path');wx=callback.__globals__['wx'];wx.ID_OK=5100
        queued=[];wx.CallAfter.side_effect=queued.append
        window=SimpleNamespace(busy=False,chooser=None,input_generation=0,closing=False,refresh=Mock(),refused=Mock(),timer=Mock(),Destroy=Mock(),status=Mock())
        dialog=Mock();dialog.GetPath.return_value='/owned/settings.json';adopt=Mock()
        callback(window,dialog,adopt)
        closed=dialog.Bind.call_args.args[1]
        event=Mock();event.GetDialog.return_value=dialog;event.GetReturnCode.return_value=5100
        return window,dialog,adopt,queued,closed,event

    def test_no_mutation_until_matching_completion_and_no_double_adoption(self):
        window,dialog,adopt,queued,closed,event=self.chooser()
        dialog.ShowWindowModal.assert_not_called();dialog.Destroy.assert_not_called();adopt.assert_not_called()
        queued.pop()();dialog.ShowWindowModal.assert_called_once();dialog.Destroy.assert_not_called()
        closed(event);adopt.assert_called_once_with('/owned/settings.json');dialog.Destroy.assert_called_once()
        closed(event);adopt.assert_called_once();dialog.Destroy.assert_called_once()
        self.assertIsNone(window.chooser)

    def test_cancel_does_not_adopt_or_mutate_settings(self):
        window,dialog,adopt,queued,closed,event=self.chooser();queued.pop()();event.GetReturnCode.return_value=5101;closed(event)
        adopt.assert_not_called();dialog.Destroy.assert_called_once();window.refused.assert_not_called()

    def test_wrong_dialog_and_stale_input_cannot_adopt(self):
        window,dialog,adopt,queued,closed,event=self.chooser();queued.pop()();event.GetDialog.return_value=Mock();closed(event)
        adopt.assert_not_called();dialog.Destroy.assert_not_called()
        event.GetDialog.return_value=dialog;window.input_generation+=1;closed(event)
        adopt.assert_not_called();window.refused.assert_called_once();dialog.Destroy.assert_called_once()

    def test_close_before_deferred_show_never_opens_or_destroys_live_panel(self):
        window,dialog,adopt,queued,closed,event=self.chooser()
        window_method('close')(window,Mock());window.Destroy.assert_not_called();dialog.Destroy.assert_not_called()
        queued.pop()();dialog.ShowWindowModal.assert_not_called();dialog.Destroy.assert_called_once();window.Destroy.assert_called_once()

    def test_close_live_sheet_defers_until_cancel_then_closes_without_adoption(self):
        window,dialog,adopt,queued,closed,event=self.chooser();queued.pop()()
        window_method('close')(window,Mock());window.Destroy.assert_not_called();dialog.Destroy.assert_not_called()
        closed(event);adopt.assert_not_called();dialog.Destroy.assert_called_once();window.Destroy.assert_called_once()

    def test_action_behind_chooser_cannot_start_a_worker(self):
        window,dialog,adopt,queued,closed,event=self.chooser()
        window_method('act')(window,'preview');window.refused.assert_not_called()
        dialog.ShowWindowModal.assert_not_called();adopt.assert_not_called()

    def test_save_callback_preserves_new_file_and_original_path_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();source=root/'project';source.mkdir();board=source/'board.kicad_pcb';board.write_text('immutable source')
            callback=window_method('save_preset');wx=callback.__globals__['wx'];wx.FD_SAVE=1
            window=SimpleNamespace(busy=False,chooser=None,config=lambda:dict(pref.DEFAULTS),board=Mock(),refused=Mock())
            window.board.GetValue.return_value=str(board);callbacks=[];window.choose_path=lambda dialog,save:callbacks.append(save)
            callback(window,None);save=callbacks.pop();target=root/'settings.json';save(str(target));self.assertEqual(json.loads(target.read_text()),pref.DEFAULTS)
            before=target.read_bytes()
            with self.assertRaises((ValueError,FileExistsError)):save(str(target))
            self.assertEqual(target.read_bytes(),before)
            with self.assertRaisesRegex(ValueError,'outside'):save(str(source/'settings.json'))
            self.assertFalse((source/'settings.json').exists());self.assertEqual(board.read_text(),'immutable source')
            window.board.GetValue.return_value='/different/board.kicad_pcb'
            with self.assertRaisesRegex(ValueError,'changed'):save(str(root/'stale.json'))
            self.assertFalse((root/'stale.json').exists())

if __name__=='__main__':unittest.main()
