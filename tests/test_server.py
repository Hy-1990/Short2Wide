import functools
import http.client
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
import pipeline
from server import Handler


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = Path(self.temp.name) / 'private' / 'dreamapi.json'
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, config=self.config))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, method, path='/api/settings/dreamapi', body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        conn.request(method, path, body, headers or {})
        response = conn.getresponse()
        result = response.status, response.read().decode()
        conn.close()
        return result

    def test_key_roundtrip_never_returns_secret(self):
        key = 'test-only-secret-0123456789'
        self.assertIn('false', self.request('GET')[1])
        status, response = self.request('POST', body=json.dumps({'key': key}), headers={'Content-Type': 'application/json', 'Origin': self.origin})
        self.assertEqual(status, 200)
        self.assertNotIn(key, response)
        self.assertEqual(json.loads(self.config.read_text())['api_key'], key)
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o600)
        status, response = self.request('GET')
        self.assertEqual(json.loads(response), {'configured': True, 'verified': False})
        self.assertNotIn(key, response)
        self.assertEqual(self.request('GET', '/server.py')[0], 404)
        self.assertEqual(self.request('GET', '/.impeccable/design.json')[0], 404)
        self.assertEqual(self.request('DELETE', headers={'Content-Type': 'application/json', 'Origin': self.origin})[0], 200)
        self.assertFalse(self.config.exists())

    def test_one_click_export_confirms_all_and_history_exposes_the_same_project(self):
        with patch.object(pipeline,'DATA',Path(self.temp.name)/'projects'):
            p=pipeline.create('UI export test.mp4','16:9');root=pipeline.folder(p['id'])
            p.update(status='ready',shots=[{'index':0,'status':'review','reviewed':False}]);pipeline.save(p)
            (root/'shot-0-aligned.mp4').write_bytes(b'test')
            headers={'Content-Type':'application/json','Origin':self.origin}
            path=f"/api/projects/{p['id']}/export"
            self.assertEqual(self.request('POST',path,'{}',headers)[0],400)
            with patch.object(pipeline,'start') as start:
                self.assertEqual(self.request('POST',path,json.dumps({'confirm_all':True}),headers)[0],202)
                start.assert_called_once_with(p['id'],pipeline.export)
            self.assertTrue(pipeline.load(p['id'])['shots'][0]['reviewed'])
            status,body=self.request('GET','/api/projects')
            self.assertEqual(status,200);self.assertEqual(json.loads(body)['projects'][0]['id'],p['id'])
            self.assertEqual(self.request('GET','/workspace.html')[0],302)

    def test_cross_origin_and_invalid_keys_cannot_mutate(self):
        payload = json.dumps({'key': 'test-only-key'})
        self.assertEqual(self.request('POST', body=payload, headers={'Content-Type': 'application/json', 'Origin': 'https://other.example'})[0], 403)
        self.assertEqual(self.request('POST', body=payload, headers={'Content-Type': 'text/plain'})[0], 415)
        for value in ('', 'bad\nkey', '含非ASCII字符', None):
            self.assertEqual(self.request('POST', body=json.dumps({'key': value}), headers={'Content-Type': 'application/json'})[0], 400)
        self.assertFalse(self.config.exists())
        self.assertEqual(self.request('GET', headers={'Host': 'attacker.example'})[0], 403)
        self.assertEqual(self.request('DELETE', headers={'Content-Type': 'application/json', 'Origin': 'https://other.example'})[0], 403)
        self.assertEqual(self.request('GET', '/assets/../server.py')[0], 404)
        self.assertEqual(self.request('GET', '/assets/')[0], 404)


if __name__ == '__main__':
    unittest.main()
