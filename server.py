"""PHONEMORE local-only test server. No customer personal data."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import sqlite3, json, os, re, secrets, datetime
ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get('PHONEMORE_DB',str(ROOT/'test.sqlite3')))
TOKEN=os.environ.get('PHONEMORE_TEST_ADMIN_TOKEN') or secrets.token_urlsafe(24)
STATES=['접수','해피콜 및 상담','개통 진행','배송','완료','취소']
def connect():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
 c.execute('CREATE TABLE IF NOT EXISTS demo_orders (id TEXT PRIMARY KEY, created TEXT NOT NULL, model TEXT NOT NULL, carrier TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL)');c.commit();return c
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def send_json(self,status,obj):
  body=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def authorized(self):return secrets.compare_digest(self.headers.get('X-Test-Admin-Token',''),TOKEN)
 def body(self):
  n=int(self.headers.get('Content-Length','0'))
  if n>4096 or n<1:raise ValueError('잘못된 요청 크기')
  x=json.loads(self.rfile.read(n));
  if not isinstance(x,dict):raise ValueError('JSON 객체만 허용')
  return x
 def do_GET(self):
  path=urlparse(self.path).path
  if path=='/api/health':return self.send_json(200,{'ok':True,'mode':'local-test','database':'sqlite'})
  if path=='/api/orders':
   if not self.authorized():return self.send_json(401,{'error':'관리자 테스트 토큰이 필요합니다'})
   with connect() as c: rows=[dict(r) for r in c.execute('SELECT * FROM demo_orders ORDER BY created DESC LIMIT 100')]
   return self.send_json(200,{'orders':rows})
  if path.startswith('/api/orders/'):
   key=path.split('/')[-1]
   if not re.fullmatch(r'T[0-9A-F]{12}',key):return self.send_json(400,{'error':'번호 형식 오류'})
   with connect() as c:r=c.execute('SELECT id,model,carrier,kind,status,created FROM demo_orders WHERE id=?',(key,)).fetchone()
   return self.send_json(200,dict(r)) if r else self.send_json(404,{'error':'기록 없음'})
  if path not in ("/", "/index.html", "/test-panel.js"):
   return self.send_json(404,{"error":"없는 경로"})
  return super().do_GET()
 def do_POST(self):
  if urlparse(self.path).path!='/api/orders':return self.send_json(404,{'error':'없는 경로'})
  if not self.authorized():return self.send_json(401,{'error':'관리자 테스트 토큰이 필요합니다'})
  try:
   x=self.body();model=x.get('model','');carrier=x.get('carrier','');kind=x.get('kind','')
   if not all(isinstance(v,str) and 1<=len(v)<=60 for v in [model,carrier,kind]):raise ValueError('모델·통신사·가입유형을 입력하세요')
   key='T'+secrets.token_hex(6).upper();created=datetime.datetime.now(datetime.timezone.utc).isoformat()
   with connect() as c:c.execute('INSERT INTO demo_orders VALUES (?,?,?,?,?,?)',(key,created,model,carrier,kind,'접수'))
   self.send_json(201,{'id':key,'status':'접수'})
  except (ValueError,json.JSONDecodeError) as e:self.send_json(400,{'error':str(e)})
 def do_PATCH(self):
  path=urlparse(self.path).path
  if not re.fullmatch(r'/api/orders/T[0-9A-F]{12}',path):return self.send_json(404,{'error':'없는 경로'})
  if not self.authorized():return self.send_json(401,{'error':'관리자 테스트 토큰이 필요합니다'})
  try:
   x=self.body();status=x.get('status')
   if status not in STATES:raise ValueError('허용되지 않은 상태')
   with connect() as c:
    cur=c.execute('UPDATE demo_orders SET status=? WHERE id=?',(status,path.split('/')[-1]));found=cur.rowcount
   self.send_json(200,{'ok':True,'status':status}) if found else self.send_json(404,{'error':'기록 없음'})
  except (ValueError,json.JSONDecodeError) as e:self.send_json(400,{'error':str(e)})
if __name__=='__main__':
 connect().close()
 port=int(os.environ.get('PORT','8000'))
 print(f'폰모어 테스트 서버 listening on port {port}',flush=True)
 ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
