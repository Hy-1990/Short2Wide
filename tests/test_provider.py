import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch,Mock
import requests
spec=importlib.util.spec_from_file_location('provider',Path(__file__).resolve().parents[1]/'scripts/dreamapi.py');provider=importlib.util.module_from_spec(spec);spec.loader.exec_module(provider)
class ProviderTests(unittest.TestCase):
    def test_query_never_submits_a_new_task_and_retries_only_the_same_id(self):
        result={'task':{'taskId':'existing','status':3},'videos':[{'videoUrl':'https://example.invalid/result.mp4'}]}
        with patch.object(sys,'argv',['provider','seedance-2.5','query','--task-id','existing']),patch.dict(provider.os.environ,{'DREAMAPI_API_KEY':'synthetic-key'}),patch.object(provider.time,'sleep'),patch.object(provider,'post',side_effect=[requests.ReadTimeout('read timeout'),result]) as post,contextlib.redirect_stdout(io.StringIO()):
            provider.main()
        self.assertEqual(post.call_count,2)
        for call in post.call_args_list:self.assertEqual(call.args[:2],('/api/getAsyncResult',{'taskId':'existing'}))
    def test_new_generation_can_disable_model_audio_without_changing_query_semantics(self):
        with patch.object(sys,'argv',['provider','seedance-2.5','run','--videos','clip.mp4','--prompt','preserve scene','--duration','6']),patch.dict(provider.os.environ,{'DREAMAPI_API_KEY':'synthetic-key'}),patch.object(provider.time,'sleep'),patch.object(provider,'upload',return_value='https://media.example.invalid/input.mp4'),patch.object(provider,'post',side_effect=[{'taskId':'new-id'},{'task':{'status':3},'videos':[]}]) as post,contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            provider.main()
        self.assertFalse(post.call_args_list[0].args[1]['generateAudio'])
        self.assertEqual(post.call_args_list[1].args[:2],('/api/getAsyncResult',{'taskId':'new-id'}))

    def test_remote_terminal_failure_keeps_the_task_id(self):
        with patch.object(sys,'argv',['provider','seedance-2.5','query','--task-id','existing']),patch.dict(provider.os.environ,{'DREAMAPI_API_KEY':'synthetic-key'}),patch.object(provider.time,'sleep'),patch.object(provider,'post',return_value={'task':{'status':4,'errorCode':123,'reason':'rejected'}}):
            with self.assertRaises(provider.DreamAPIError) as caught:provider.main()
        self.assertEqual(caught.exception.task_id,'existing')
    def test_upload_uses_the_returned_policy_and_verifies_the_result(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'clip.mp4';path.write_bytes(b'synthetic')
            policy={'host':'https://upload.example.invalid','key':'object-key','policy':'policy','OSSAccessKeyId':'access','signature':'signature','reqId':'request'}
            response=Mock();response.json.return_value={'data':{'reqId':'request'}}
            with patch.object(provider,'post',side_effect=[policy,{'url':'https://media.example.invalid/clip.mp4'}]) as post,patch.object(provider.requests,'post',return_value=response) as upload:
                self.assertEqual(provider.upload(path,'synthetic-key'),'https://media.example.invalid/clip.mp4')
                self.assertEqual(upload.call_args.kwargs['data']['key'],'object-key')
                self.assertEqual(post.call_args_list[-1].args[:2],('/api/file/v1/policy_upload_finish',{'reqId':'request'}))
if __name__=='__main__':unittest.main()
