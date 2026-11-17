#!/usr/bin/env python3
"""Minimal DreamAPI Seedance CLI used by Short2Wide; no credential persistence."""
import argparse
import json
import mimetypes
import os
from pathlib import Path
import sys
import time
import requests

BASE='https://api.newportai.com'
class DreamAPIError(Exception):
    def __init__(self,code,message,task_id=''):
        self.code=code;self.task_id=task_id
        super().__init__(f'[{code}] {message}')

def post(path,payload,key):
    response=requests.post(BASE+path,headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json=payload,timeout=45)
    response.raise_for_status();value=response.json()
    if value.get('code')!=0:raise DreamAPIError(value.get('code',-1),value.get('message','Unexpected provider response'))
    return value.get('data',{})

def upload(filename,key):
    file=Path(filename)
    policy=post('/api/file/v1/get_policy',{'scene':'Dream-CN'},key)
    object_key=policy.get('key') or (policy.get('dir','')+file.name)
    fields={'key':object_key,'policy':policy.get('policy'),'OSSAccessKeyId':policy.get('accessId') or policy.get('OSSAccessKeyId'),'signature':policy.get('signature'),'success_action_status':'200'}
    if not policy.get('host') or any(not x for x in fields.values()):raise ValueError('Incomplete upload policy')
    if policy.get('callback'):fields['callback']=policy['callback']
    with file.open('rb') as stream:
        response=requests.post(policy['host'],data=fields,files={'file':(file.name,stream,mimetypes.guess_type(file.name)[0] or 'video/mp4')},timeout=300)
    response.raise_for_status();value=response.json();request_id=value.get('data',{}).get('reqId') or policy.get('reqId')
    if not request_id:raise ValueError('Upload response did not include reqId')
    result=post('/api/file/v1/policy_upload_finish',{'reqId':request_id},key)
    if not result.get('url'):raise ValueError('Upload verification did not return a URL')
    return result['url']

def main():
    parser=argparse.ArgumentParser();parser.add_argument('model',choices=['seedance-2.5']);parser.add_argument('action',choices=['run','query'])
    parser.add_argument('--task-id');parser.add_argument('--videos',nargs='+');parser.add_argument('--prompt');parser.add_argument('--ratio',default='16:9',choices=['16:9','9:16']);parser.add_argument('--resolution',default='720p',choices=['480p','720p','1080p']);parser.add_argument('--duration',type=int);parser.add_argument('--generate-audio',action='store_true');parser.add_argument('--timeout',type=float,default=900);parser.add_argument('--json',action='store_true')
    args=parser.parse_args();key=os.environ.get('DREAMAPI_API_KEY','').strip()
    if not key:raise DreamAPIError(401,'API key is missing')
    task=args.task_id
    if args.action=='run':
        if not args.videos or not args.prompt or not args.duration or not 4<=args.duration<=30:raise ValueError('Reference video, prompt and duration 4–30 are required')
        print('Uploading reference media…',file=sys.stderr,flush=True)
        videos=[upload(file,key) for file in args.videos]
        body={'model':'seedance-2.5','videos':videos,'prompt':args.prompt,'ratio':args.ratio,'resolution':args.resolution,'duration':args.duration,'generateAudio':args.generate_audio}
        task=post('/api/async/seedance_2.5',body,key).get('taskId')
        if not task:raise DreamAPIError(-1,'Submit response did not return a task ID')
        print(f'Task submitted. taskId: {task}',file=sys.stderr,flush=True)
    if not task:raise ValueError('Task ID is required to query')
    started=time.monotonic();retried=False
    while time.monotonic()-started<args.timeout:
        time.sleep(5)
        try:result=post('/api/getAsyncResult',{'taskId':task},key)
        except (requests.RequestException,ValueError):
            if retried:raise
            retried=True;continue
        retried=False;info=result.get('task',{});status=info.get('status')
        if status==3:
            print(json.dumps(result,ensure_ascii=False));return
        if status==4:raise DreamAPIError(info.get('errorCode',-1),info.get('reason','Generation failed'),task_id=task)
    raise TimeoutError(f'Task {task} is still processing; resume this same task ID')
if __name__=='__main__':main()
