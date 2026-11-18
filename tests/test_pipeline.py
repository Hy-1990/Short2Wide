import json
import math
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pipeline


class PipelineTests(unittest.TestCase):
    def test_cut_plan_covers_timeline_without_tiny_tail(self):
        for duration in (1.2, 4, 12.2, 25, 128.7, 299.9):
            pieces = pipeline.plan_segments(duration, [8.8, 10.4, 24, 100])
            self.assertEqual(pieces[0][0], 0)
            self.assertEqual(pieces[-1][1], duration)
            self.assertAlmostEqual(sum(b-a for a,b in pieces), duration)
            for a,b in pieces:
                self.assertLessEqual(b-a, 12.01)
                self.assertGreaterEqual(b-a, min(4, duration)-.02)
            for previous, next_ in zip(pieces, pieces[1:]):
                self.assertEqual(previous[1], next_[0])
        for duration in (0,300,301):
            with self.assertRaises(pipeline.WorkflowError): pipeline.plan_segments(duration, [])
        self.assertFalse(pipeline.valid_link('https://youtube.com.attacker.example/video'))
        self.assertFalse(pipeline.valid_link('http://youtube.com/watch?v=x'))
        self.assertTrue(pipeline.valid_link('https://www.youtube.com/watch?v=x'))

    def test_real_media_prepare_align_and_export_uses_original_audio(self):
        with tempfile.TemporaryDirectory(prefix='short2wide 中文 ') as directory, patch.object(pipeline, 'DATA', Path(directory)):
            project=pipeline.create('synthetic 中文.mp4', '16:9'); pid=project['id']; root=pipeline.folder(pid)
            pipeline.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','testsrc2=size=360x640:rate=30','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','4.8','-c:v','libx264','-preset','ultrafast','-c:a','aac','-f','mp4',root/'input.media'])
            pipeline.prepare(pid)
            project=pipeline.load(pid)
            self.assertEqual(project['status'],'ready',project.get('error'))
            self.assertTrue(project['audio'])
            self.assertEqual(len(project['shots']),1)
            pipeline.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','testsrc2=size=640x360:rate=30','-f','lavfi','-i','sine=frequency=880:sample_rate=48000','-t','6','-c:v','libx264','-preset','ultrafast','-c:a','aac',root/'shot-0-generated.mp4'])
            provider=root/'provider.mp4'; (root/'shot-0-generated.mp4').rename(provider)
            stub=root/'stub.py'; key=root/'key.json'; key.write_text(json.dumps({'api_key':'synthetic-not-a-real-key'}))
            stub.write_text("import json,sys\nprint('Task submitted. taskId: test-123',file=sys.stderr)\nprint(json.dumps({'task':{'taskId':'test-123','status':3},'videos':[{'videoUrl':'https://fixture.example/video.mp4'}]}))\n")
            with patch.object(pipeline,'SCRIPT',stub),patch.object(pipeline,'CONFIG',key),patch.object(pipeline,'urlopen',lambda *a,**k: provider.open('rb')):
                pipeline.model_call(pid,0,False)
            generated=pipeline.load(pid)['shots'][0]
            self.assertEqual(generated['status'],'review',generated.get('error'))
            self.assertEqual(generated['task_id'],'test-123')
            self.assertTrue(generated['generated_audio'])
            pipeline.align(pid,0,[[1,1.25],[3,3.75]])
            shot=pipeline.load(pid)['shots'][0]
            self.assertAlmostEqual(shot['scale'],.8)
            self.assertFalse(shot['reviewed'])
            self.assertAlmostEqual(pipeline.probe(root/'shot-0-aligned.mp4')['duration'],4.8,places=1)
            with self.assertRaises(pipeline.WorkflowError): pipeline.export(pid)
            before=(root/'shot-0-aligned.mp4').stat().st_size
            with patch.object(pipeline,'run',side_effect=pipeline.WorkflowError('synthetic ffmpeg failure')):
                with self.assertRaises(pipeline.WorkflowError):pipeline.align(pid,0,[])
            self.assertEqual(pipeline.load(pid)['shots'][0]['status'],'review')
            self.assertEqual((root/'shot-0-aligned.mp4').stat().st_size,before)
            preview=pipeline.build_preview(pid,0)
            self.assertTrue(pipeline.probe(preview)['audio'])
            cached_time=preview.stat().st_mtime_ns
            self.assertEqual(pipeline.build_preview(pid,0).stat().st_mtime_ns,cached_time)
            pipeline.confirm_all(pid)
            self.assertTrue(all(s['reviewed'] for s in pipeline.load(pid)['shots']))
            pipeline.export(pid)
            self.assertTrue(pipeline.build_cover(pid).is_file())
            final=pipeline.probe(root/'export.mp4')
            self.assertEqual((final['width'],final['height']),(1280,720))
            self.assertTrue(final['audio'])
            self.assertAlmostEqual(final['duration'],4.8,places=1)
            audio=pipeline.subprocess.run(['ffmpeg','-v','error','-i',str(root/'export.mp4'),'-vn','-ac','1','-ar','8000','-t','2','-f','s16le','-'],capture_output=True,check=True).stdout
            samples=struct.unpack('<'+'h'*(len(audio)//2),audio)
            def energy(hz):
                real=sum(x*math.cos(2*math.pi*hz*i/8000) for i,x in enumerate(samples))
                imag=sum(x*math.sin(2*math.pi*hz*i/8000) for i,x in enumerate(samples))
                return real*real+imag*imag
            self.assertGreater(energy(440),energy(880)*100)
            pipeline.align(pid,0,[])
            self.assertFalse(preview.exists())
            self.assertFalse(pipeline.load(pid)['export_ready'])
            self.assertFalse(pipeline.load(pid)['shots'][0]['reviewed'])

    def test_uncertain_model_responses_never_allow_new_paid_submission(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(pipeline,'DATA',Path(directory)):
            p=pipeline.create('failure-test.mp4','16:9');pid=p['id'];root=pipeline.folder(pid)
            p.update(status='ready',shots=[{'index':0,'duration':5,'status':'generating','task_id':'existing-task','prompt':'','reviewed':False}]);pipeline.save(p)
            key=root/'key.json';key.write_text(json.dumps({'api_key':'synthetic-not-real-key'}))
            script=root/'stub.py'
            with patch.object(pipeline,'SCRIPT',script),patch.object(pipeline,'CONFIG',key):
                for exception in ["raise TimeoutError('timed out')", "raise ValueError('invalid JSON')", "class ReadTimeout(Exception): pass\nraise ReadTimeout('read timed out')"]:
                    script.write_text(exception)
                    pipeline.model_call(pid,0,True)
                    self.assertEqual(pipeline.load(pid)['shots'][0]['status'],'resumable')
                pipeline.shot_update(pid,0,task_id='',status='uploading')
                script.write_text("raise ValueError('response missing task id')")
                pipeline.model_call(pid,0,False)
                self.assertEqual(pipeline.load(pid)['shots'][0]['status'],'interrupted')
                with self.assertRaises(pipeline.WorkflowError):pipeline.generate(pid,0,retry=True)
                for payload in ["print('invalid JSON')", "print('{}')"]:
                    pipeline.shot_update(pid,0,task_id='',status='uploading')
                    script.write_text(payload)
                    pipeline.model_call(pid,0,False)
                    self.assertEqual(pipeline.load(pid)['shots'][0]['status'],'interrupted')
                pipeline.shot_update(pid,0,task_id='existing-task',status='generating')
                script.write_text("class DreamAPIError(Exception):\n task_id='existing-task'\n code=4\nraise DreamAPIError('remote terminal failure')")
                pipeline.model_call(pid,0,True)
                self.assertEqual(pipeline.load(pid)['shots'][0]['status'],'failed')

    def test_confirm_all_requires_every_generated_file_and_preserves_metadata(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(pipeline,'DATA',Path(directory)):
            p=pipeline.create('multi.mp4','16:9');root=pipeline.folder(p['id'])
            p['shots']=[{'index':0,'status':'review','reviewed':False,'task_id':'keep-0'}, {'index':1,'status':'ready','reviewed':False,'task_id':'keep-1'}];pipeline.save(p)
            (root/'shot-0-aligned.mp4').write_bytes(b'test')
            with self.assertRaises(pipeline.WorkflowError):pipeline.confirm_all(p['id'])
            p['shots'][1]['status']='review';pipeline.save(p)
            with self.assertRaises(pipeline.WorkflowError):pipeline.confirm_all(p['id'])
            (root/'shot-1-aligned.mp4').write_bytes(b'test')
            pipeline.confirm_all(p['id']);saved=pipeline.load(p['id'])
            self.assertTrue(all(s['reviewed'] for s in saved['shots']))
            self.assertEqual([s['task_id'] for s in saved['shots']],['keep-0','keep-1'])
            pipeline.ACTIVE.add(p['id'])
            try:
                with self.assertRaises(pipeline.WorkflowError):pipeline.confirm_all(p['id'])
            finally:pipeline.ACTIVE.discard(p['id'])

    def test_history_lists_all_local_projects_with_progress_and_thumbnail(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(pipeline,'DATA',Path(directory)):
            p=pipeline.create('existing.mp4','9:16');root=pipeline.folder(p['id'])
            p.update(duration=31,export_ready=True,shots=[{'index':0,'status':'review'}]);pipeline.save(p)
            (root/'shot-0.jpg').write_bytes(b'thumbnail')
            (root/'source.mp4').write_bytes(b'placeholder')
            result=pipeline.project_summaries()['projects'][0]
            self.assertEqual(result['id'],p['id']);self.assertEqual(result['generated_count'],1)
            self.assertTrue(result['export_ready']);self.assertIn(p['id'],result['thumbnail'])
            self.assertNotIn('shots',result)

    def test_explicit_audio_off_retry_archives_the_failed_attempt_and_blocks_ambiguous_restarts(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(pipeline,'DATA',Path(directory)):
            p=pipeline.create('retry.mp4','16:9');root=pipeline.folder(p['id'])
            p.update(status='ready',shots=[{'index':0,'status':'failed','task_id':'old-failed-id','prompt':'original','generate_audio':True,'error':'output audio rejected'}]);pipeline.save(p)
            key=root/'test-key.json';key.write_text('{"api_key":"synthetic-key"}')
            with patch.object(pipeline,'CONFIG',key),patch.object(pipeline,'start') as start:
                pipeline.generate(p['id'],0,prompt='same scene',retry=True,generate_audio=False)
                start.assert_called_once_with(p['id'],pipeline.model_call,0,False)
                shot=pipeline.load(p['id'])['shots'][0]
                self.assertFalse(shot['generate_audio']);self.assertEqual(shot['attempts'][0]['task_id'],'old-failed-id')
                self.assertEqual(shot['task_id'],'')
                with self.assertRaises(pipeline.WorkflowError):pipeline.generate(p['id'],0,retry=True,generate_audio=False)

    def test_short_silent_video_is_supported(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(pipeline,'DATA',Path(directory)):
            p=pipeline.create('silent.mp4','9:16');root=pipeline.folder(p['id'])
            pipeline.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','color=c=blue:s=320x180:r=30','-t','1.5','-c:v','libx264','-f','mp4',root/'input.media'])
            pipeline.prepare(p['id']);p=pipeline.load(p['id'])
            self.assertEqual(p['status'],'ready',p['error']);self.assertFalse(p['audio'])
            self.assertAlmostEqual(pipeline.probe(root/'shot-0-reference.mp4')['duration'],4,places=1)

if __name__=='__main__': unittest.main()
