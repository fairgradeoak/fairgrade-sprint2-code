"""Exercise production handler queries in local PostgreSQL WASM, S3 stubbed."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from botocore.exceptions import ClientError

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('handler',ROOT/'backend/proctoring/handler.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
X='11111111-1111-4111-8111-111111111111'; S='22222222-2222-4222-8222-222222222222'; I='33333333-3333-4333-8333-333333333333'; E='44444444-4444-4444-8444-444444444444'; C='55555555-5555-4555-8555-555555555555'
NOW=datetime.now(timezone.utc).replace(microsecond=0)
class DB:
 def __init__(self):self.process=subprocess.Popen(['node','tests/pglite-bridge.mjs'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
 def send(self,sql,params=(),exec=False):
  self.process.stdin.write(json.dumps({'sql':sql,'params':params,'exec':exec},default=str)+'\n');self.process.stdin.flush();result=json.loads(self.process.stdout.readline())
  if not result['ok']:raise RuntimeError(result['error'])
  return result['result']
 def cursor(self):return Cursor(self)
 def commit(self):self.send('COMMIT')
 def rollback(self):self.send('ROLLBACK')
 def close(self):self.process.stdin.close();self.process.wait(timeout=15)
class Cursor:
 def __init__(self,db):self.db=db;self.description=None
 def execute(self,sql,args):
  count=0
  while '%s' in sql:count+=1;sql=sql.replace('%s',f'${count}',1)
  result=self.db.send(sql,args);self.description=[(f['name'],) for f in result.get('fields',[])] or None
  self.rows=[]
  for row in result.get('rows',[]):
   for name in list(row):
    if name.endswith('_at') and row[name] is not None:row[name]=datetime.fromisoformat(row[name].replace('Z','+00:00'))
   self.rows.append(tuple(row[k[0]] for k in self.description))
 def fetchall(self):return self.rows
 def close(self):pass
class S3:
 def __init__(self):self.objects={};self.signs=[]
 def head_object(self,**kw):
  if kw['Key'] not in self.objects:raise ClientError({'Error':{'Code':'404'}},'HeadObject')
  return self.objects[kw['Key']]
 def generate_presigned_url(self,operation,**kw):self.signs.append((operation,kw));return 'https://private.example/test-signed-url'

@pytest.fixture
def setup():
 db=DB();db.send('''CREATE TABLE users(id uuid PRIMARY KEY,cognito_sub text UNIQUE,role text);
 CREATE TABLE courses(id uuid PRIMARY KEY,instructor_id uuid REFERENCES users(id));
 CREATE TABLE exams(id uuid PRIMARY KEY,course_id uuid REFERENCES courses(id));
 CREATE TABLE exam_attempts(id uuid PRIMARY KEY,exam_id uuid REFERENCES exams(id),student_id uuid REFERENCES users(id),status text);''',exec=True)
 db.send((ROOT/'infra/schema.sql').read_text(),exec=True)
 for ident,sub,role in [(S,'student-sub','student'),(I,'teacher-sub','instructor')]:db.send('INSERT INTO users VALUES($1,$2,$3)',[ident,sub,role])
 db.send('INSERT INTO courses VALUES($1,$2)',[C,I]);db.send('INSERT INTO exams VALUES($1,$2)',[X,C]);db.send('INSERT INTO exam_attempts VALUES($1,$2,$3,$4)',[str(uuid.uuid4()),X,S,'in_progress'])
 s3=S3();service=h.Service(db,s3,{'bucket':'private-clips','client_id':'client','days':30,'policy':'policy-v2','metadata_notice':'Pending separate metadata policy'},now=NOW)
 yield db,s3,service
 db.close()

def event(path,body=None,role='student',method=None):
 return {'rawPath':'/proctoring'+path,'headers':{'Idempotency-Key':E},'body':json.dumps(body) if body is not None else None,
 'requestContext':{'http':{'method':method or ('POST' if body is not None else 'GET')},'authorizer':{'jwt':{'claims':{'sub':'student-sub' if role=='student' else 'teacher-sub','token_use':'access','client_id':'client','cognito:groups':'[Student]' if role=='student' else '[Instructor]'}}}}}

def payload():
 return {'eventId':E,'examId':X,'contentType':'video/webm','sizeBytes':5,'checksumSha256':base64.b64encode(hashlib.sha256(b'video').digest()).decode(),'consentVersion':'policy-v2','consentedAt':(NOW-timedelta(minutes=5)).isoformat()}

def logged(setup):
 db,s3,service=setup;p=payload();status,ticket=service.dispatch(event('/clips/presign',p));assert status==200
 s3.objects[ticket['objectKey']]={'ContentLength':5,'ContentType':'video/webm','ChecksumSHA256':p['checksumSha256']}
 p.update(objectKey=ticket['objectKey'],reasons=['phone'],triggeredAt=(NOW-timedelta(seconds=10)).isoformat(),synthetic=False,clip={'audio':False,'complete':True,'preMs':7500,'postMs':7500,'sourceDurationMs':15000,'encodedElapsedMs':15000})
 status,saved=service.dispatch(event('/events',p));assert status==201
 return p,saved

def problem(code,fn):
 with pytest.raises(h.Problem) as e:fn()
 assert e.value.code==code

def test_upload_event_review_audit_and_retry(setup):
 db,s3,service=setup;p,saved=logged(setup);assert saved['studentId']==S;assert saved['version']==0
 assert s3.signs[0][1]['Params']['IfNoneMatch']=='*'
 assert service.dispatch(event('/clips/presign',payload()))[1]['uploadRequired'] is False
 assert service.dispatch(event('/events',p))[0]==200
 assert db.send('SELECT count(*)::int AS n FROM proctoring_events')['rows'][0]['n']==1
 query=event('/events',role='instructor');query['queryStringParameters']={'examId':X};assert len(service.dispatch(query)[1]['events'])==1
 db.send('BEGIN');code,review=service.dispatch(event(f'/events/{E}/review',{'decision':'confirmed','version':0},'instructor','PATCH'));db.commit()
 assert code==200 and review['version']==1
 assert db.send('SELECT decision,new_version FROM proctoring_review_audit')['rows']==[{'decision':'confirmed','new_version':1}]
 problem('REVIEW_VERSION_CONFLICT',lambda:service.dispatch(event(f'/events/{E}/review',{'decision':'dismissed','version':0},'instructor','PATCH')))
 assert service.dispatch(event(f'/events/{E}/playback',role='instructor'))[0]==200
 p['reasons']=['no_face'];problem('IDEMPOTENCY_CONFLICT',lambda:service.dispatch(event('/events',p)))

def test_auth_and_ownership(setup):
 db,s3,service=setup
 req=event('/policy');req['requestContext']['authorizer']={};problem('ACCESS_TOKEN_REQUIRED',lambda:service.dispatch(req))
 req=event('/policy');req['requestContext']['authorizer']['jwt']['claims']['token_use']='id';problem('ACCESS_TOKEN_REQUIRED',lambda:service.dispatch(req))
 req=event('/policy');req['requestContext']['authorizer']['jwt']['claims']['cognito:groups']='[Instructor]';problem('ROLE_REQUIRED',lambda:service.dispatch(req))
 problem('STUDENT_REQUIRED',lambda:service.dispatch(event('/clips/presign',payload(),'instructor')))
 db.send("UPDATE exam_attempts SET status='completed'");problem('ACTIVE_ATTEMPT_REQUIRED',lambda:service.dispatch(event('/clips/presign',payload())))
 db.send('UPDATE courses SET instructor_id=$1',[S]);req=event('/events',role='instructor');req['queryStringParameters']={'examId':X};problem('EXAM_ACCESS_DENIED',lambda:service.dispatch(req))

def test_checksum_policy_and_identity_conflicts(setup):
 db,s3,service=setup;p=payload();p['consentVersion']='old';problem('CONSENT_POLICY_CHANGED',lambda:service.dispatch(event('/clips/presign',p)))
 p=payload();_,ticket=service.dispatch(event('/clips/presign',p));p['sizeBytes']=6;problem('IDEMPOTENCY_CONFLICT',lambda:service.dispatch(event('/clips/presign',p)))
 s3.objects[ticket['objectKey']]={'ContentLength':5,'ContentType':'video/webm','ChecksumSHA256':'wrong'}
 problem('STORED_OBJECT_MISMATCH',lambda:service.dispatch(event('/clips/presign',payload())))
 p=payload();p['studentId']=I;problem('SERVER_OWNED_FIELD',lambda:service.dispatch(event('/clips/presign',p)))

def test_expired_playback_and_audit_transaction_rollback(setup):
 db,s3,service=setup;p,_=logged(setup)
 db.send('BEGIN');service.dispatch(event(f'/events/{E}/review',{'decision':'dismissed','version':0},'instructor','PATCH'));db.rollback()
 assert db.send('SELECT version FROM proctoring_events')['rows'][0]['version']==0
 assert db.send('SELECT count(*)::int AS n FROM proctoring_review_audit')['rows'][0]['n']==0
 service.now=NOW+timedelta(days=31);problem('CLIP_EXPIRED',lambda:service.dispatch(event(f'/events/{E}/playback',role='instructor')))

def test_sql_constraints(setup):
 db,s3,service=setup;logged(setup)
 with pytest.raises(RuntimeError):db.send('UPDATE proctoring_events SET student_id=$1 WHERE event_id=$2',[I,E])
 with pytest.raises(RuntimeError):db.send("UPDATE proctoring_events SET reasons=ARRAY['not-a-reason'] WHERE event_id=$1",[E])
 with pytest.raises(RuntimeError):db.send('UPDATE proctoring_events SET reviewed=true WHERE event_id=$1',[E])
 with pytest.raises(RuntimeError):db.send('DELETE FROM users WHERE id=$1',[S])

def test_invalid_ids_json_and_groups():
 for value in ['demo-exam',None,'11111111-1111-1111-1111-111111111111']:problem('INVALID_UUID',lambda:h.uid(value))
 for raw in ['[]','{bad']:problem('INVALID_JSON',lambda:h.unpack_body({'body':raw}))
 assert h.groups('[Student, Instructor]')=={'Student','Instructor'}
 assert h.groups('["Student"]')=={'Student'}
 problem('INVALID_TIMESTAMP',lambda:h.stamp('2026-10-30'))

def test_missing_upload_never_logs_and_bad_review_is_400(setup):
 db,s3,service=setup;p=payload();_,ticket=service.dispatch(event('/clips/presign',p))
 p.update(objectKey=ticket['objectKey'],reasons=['phone'],triggeredAt=NOW.isoformat(),synthetic=False,clip={'audio':False,'complete':False,'preMs':0,'postMs':0,'sourceDurationMs':0,'encodedElapsedMs':0})
 problem('UPLOAD_NOT_FOUND',lambda:service.dispatch(event('/events',p)))
 assert db.send('SELECT count(*)::int AS n FROM proctoring_events')['rows'][0]['n']==0
 s3.objects[ticket['objectKey']]={'ContentLength':5,'ContentType':'video/webm','ChecksumSHA256':p['checksumSha256']};service.dispatch(event('/events',p))
 problem('INVALID_REVIEW',lambda:service.dispatch(event(f'/events/{E}/review',{'decision':[],'version':0},'instructor','PATCH')))

def test_presign_sdk_signs_immutable_checksum_headers():
 from urllib.parse import urlparse,parse_qs
 client=h.boto3.client('s3',region_name='eu-north-1',aws_access_key_id='test-only',aws_secret_access_key='test-only',config=h.Config(signature_version='s3v4',s3={'addressing_style':'virtual'}))
 url=client.generate_presigned_url('put_object',Params={'Bucket':'example-private-clips','Key':'proctoring/test.webm','ContentType':'video/webm','ChecksumSHA256':payload()['checksumSha256'],'IfNoneMatch':'*'},ExpiresIn=300)
 headers=parse_qs(urlparse(url).query)['X-Amz-SignedHeaders'][0].split(';')
 assert {'content-type','if-none-match','x-amz-checksum-sha256'}<=set(headers)
