"""本地控制台。启动网页只监听 localhost；设备仅在用户点击启动后连接。"""
import argparse
import csv
import math
import fcntl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit

from .web_settings import defaults, validate, read, atomic_json, SCALARS, ARRAYS

WEB_ROOT=Path(__file__).parent/'web'
from .resources import runtime_file, ready

class Dashboard:
    def __init__(self,root):
        self.root=Path(root).resolve();self.store=self.root/'data'/'web'
        self.store.mkdir(parents=True,exist_ok=True)
        self.settings_path=self.store/'settings.json'
        if not self.settings_path.exists():atomic_json(self.settings_path,defaults())
        initial=read(self.settings_path)
        history=self.store/f"settings_v{initial['revision']:06d}.json"
        if not history.exists():atomic_json(history,initial)
        self.token=secrets.token_urlsafe(32);self.lock=threading.RLock()
        self.proc=None;self.run_id=None;self.state_path=None;self.log_path=None
        self.started=None;self.stop_requested=False

    def settings(self):return read(self.settings_path)

    def save(self,body):
        with self.lock:
            data=validate(body)
            current=self.settings()
            if data['revision']!=current['revision']:raise ValueError('参数已被其他页面修改，请刷新后重试')
            data['revision']=current['revision']+1
            atomic_json(self.store/f"settings_v{data['revision']:06d}.json",data)
            atomic_json(self.settings_path,data)
            return data

    def running(self):return self.proc is not None and self.proc.poll() is None

    @staticmethod
    def other_session():
        # 同机已用终端启动的旧会话也要排除，避免两份程序占用同一机械臂。
        modules={'stararm_rs_feedback.dynamic','stararm_rs_feedback.trial','stararm_rs_feedback.preview',
                 'stararm_rs_feedback','stararm_rs_feedback.launcher','lerobot.scripts.lerobot_teleoperate'}
        for p in Path('/proc').glob('[0-9]*/cmdline'):
            try:args=p.read_bytes().decode(errors='replace').split('\0')
            except OSError:continue
            if '-m' in args:
                i=args.index('-m')
                if i+1<len(args) and args[i+1] in modules:return str(p.parent.name)
        return None

    def start(self,body):
        if set(body)!={'mode'} or body['mode'] not in ('feedback','monitor'):
            raise ValueError('请选择反馈运行或仅监测运行')
        with self.lock:
            if self.running():raise ValueError('已有网页会话正在运行')
            other=self.other_session()
            if other:raise ValueError(f'检测到终端遥操作会话 PID {other}，请先退出旧程序')
            if not (self.root/'feedback.rs-dynamic.json').is_file():raise ValueError('缺少 feedback.rs-dynamic.json')
            settings=self.settings();run_id=time.strftime('%Y%m%d_%H%M%S')+'_'+secrets.token_hex(3)
            state=self.store/(run_id+'.json');log=self.store/(run_id+'.log')
            args=[sys.executable,'-u','-m','stararm_rs_feedback.dynamic',
                  '--dynamic-spec',str(self.root/'feedback.rs-dynamic.json'),
                  '--dynamic-max-power-mw',str(settings['max_power_mw']),
                  '--feedback-log',str(self.root/'data'/('dynamic_web_'+run_id+'.csv')),
                  '--web-settings',str(self.settings_path),'--web-state',str(state),'--web-run-id',run_id,
                  '--robot.type=seeed_b601_rs_follower','--robot.port=can0','--robot.can_adapter=socketcan',
                  '--robot.id=follower1','--teleop.type=rebot_arm_102_leader','--teleop.port=/dev/ttyUSB0',
                  '--teleop.id=rebot_arm_102_leader','--fps=30']
            if body['mode']=='feedback':args.append('--feedback-enable')
            env=dict(os.environ,PYTHONPATH=str(Path(__file__).parent.parent)+os.pathsep+os.environ.get('PYTHONPATH',''))
            with log.open('x',encoding='utf-8') as out:
                proc=subprocess.Popen(args,cwd=self.root,env=env,stdin=subprocess.DEVNULL,
                                      stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
            self.proc=proc;self.run_id=run_id;self.state_path=state;self.log_path=log
            self.started=time.time();self.stop_requested=False
            return self.status()

    def stop(self):
        with self.lock:
            if self.running() and not self.stop_requested:
                # 相当于终端 Ctrl+C，保留官方清理；不强杀、不宣称急停。
                self.proc.send_signal(signal.SIGINT);self.stop_requested=True
            return self.status()

    def status(self):
        with self.lock:
            running=self.running()
            state=None
            if self.state_path and self.state_path.exists():
                try:
                    state=json.loads(self.state_path.read_text())
                    if state.get('run_id')!=self.run_id:state=None
                except (OSError,ValueError):pass
            age=max(0.,time.time()-state['wall_time']) if state else None
            fresh=running and state is not None and age<.8
            return dict(running=running,stop_requested=self.stop_requested,
                        phase=('stopping' if self.stop_requested else 'running' if fresh else 'connecting') if running
                              else 'exited' if self.proc else 'idle',
                        exit_code=self.proc.poll() if self.proc else None,
                        run_id=self.run_id,started=self.started,age_s=age,fresh=fresh,telemetry=state,
                        saved_revision=self.settings()['revision'],
                        log_file=str(self.log_path) if self.log_path else None)

    def replay(self):
        if self.running():raise ValueError('请先停止实时会话，再回放日志')
        from .config import NAMES
        files=sorted((self.root/'data').glob('dynamic_*.csv'),key=lambda p:p.stat().st_mtime,reverse=True)
        for path in files:
            frames=[];group={};stamp=None;last=-math.inf
            def number(row,key):
                try:
                    n=float(row.get(key,''))
                    return n if math.isfinite(n) else None
                except (ValueError,TypeError):return None
            with path.open(newline='',encoding='utf-8') as file:
                for row in csv.DictReader(file):
                    t=number(row,'monotonic_s')
                    if t is None:continue
                    if stamp!=t:group={};stamp=t
                    n=row.get('joint')
                    if n not in NAMES:continue
                    group[n]=dict(name=n,index=NAMES.index(n)+1,motor_pos_deg=number(row,'motor_pos_deg'),
                        leader_pos_deg=None,torque_nm=number(row,'motor_torque_nm'),current_a=number(row,'current_iq_a'),
                        residual_nm=number(row,'residual_torque_nm'),deadzone_nm=number(row,'deadzone_nm'),
                        temperature_c=None,valid=row.get('dynamic_valid')=='True',
                        reason=row.get('unloaded_status',''),
                        leader_mode={'0x10':'FREE','0x11':'HOLD','0x12':'DAMPING'}.get(row.get('mode'),'UNKNOWN'),
                        leader_power_mw=number(row,'power_mw'),can_age_s=None)
                    if len(group)==7 and t-last>=.1:
                        last=t
                        frames.append(dict(source='replay',monotonic_s=t,joints=[group[n] for n in NAMES],
                            output_enabled=row.get('output_enabled')=='True',holding=any(j['leader_mode']=='HOLD' for j in group.values()),
                            status='历史日志回放',applied_revision=None,leader_read_retry_count=0,leader_read_issues=[]))
            if frames:
                step=max(1,math.ceil(len(frames)/1200))
                return dict(file=path.name,frames=frames[::step])
        raise ValueError('data/ 中还没有可回放的动态日志')

    def logs(self):
        if not self.log_path:return ''
        try:
            with self.log_path.open('rb') as f:
                f.seek(0,2);f.seek(max(0,f.tell()-18000))
                return f.read().decode('utf-8',errors='replace')
        except OSError:return ''

class Server(ThreadingHTTPServer):
    daemon_threads=True


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,code,body,kind='application/json; charset=utf-8'):
            if not isinstance(body,bytes):body=json.dumps(body,ensure_ascii=False,allow_nan=False).encode()
            self.send_response(code);self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass

        def local_request(self):
            port=self.server.server_port
            return self.headers.get('Host') in (f'127.0.0.1:{port}',f'localhost:{port}')

        def do_GET(self):
            if not self.local_request():self.send(403,{'error':'仅允许本机访问'});return
            path=urlsplit(self.path).path
            if path=='/api/bootstrap':
                self.send(200,dict(token=app.token,settings=app.settings(),defaults=defaults(),scalars=SCALARS,arrays=ARRAYS,version='0.7.0'));return
            if path=='/api/state':self.send(200,app.status());return
            if path=='/api/log':self.send(200,{'text':app.logs()});return
            if path=='/api/replay':
                try:self.send(200,app.replay())
                except (ValueError,OSError) as e:self.send(400,{'error':str(e)})
                return
            # 固定静态资源根目录，不能访问日志、校准或工作区的任意文件。
            from urllib.parse import unquote
            rel=unquote(path).lstrip('/') or 'index.html'
            file=(WEB_ROOT/rel).resolve()
            if not file.is_relative_to(WEB_ROOT.resolve()):
                self.send(404,{'error':'File not found'});return
            if not file.is_file() and (rel.startswith(('vendor/','model/')) or rel=='icons.svg'):
                try:file=runtime_file('web/'+rel)
                except ValueError:self.send(404,{'error':'File not found'});return
            if not file.is_file():
                self.send(404,{'error':'文件不存在'});return
            self.send(200,file.read_bytes(),mimetypes.guess_type(file)[0] or 'application/octet-stream')

        def do_POST(self):
            if not self.local_request() or self.headers.get('X-RS-Token')!=app.token:
                self.send(403,{'error':'网页会话已失效，请刷新'});return
            origin=self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'):
                self.send(403,{'error':'请求来源不匹配'});return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=32000:raise ValueError('请求过大或为空')
                if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('需要 JSON')
                body=json.loads(self.rfile.read(length))
                path=urlsplit(self.path).path
                if path=='/api/settings':result=app.save(body)
                elif path=='/api/start':result=app.start(body)
                elif path=='/api/stop':
                    if body!={}:raise ValueError('无效停止请求')
                    result=app.stop()
                else:self.send(404,{'error':'接口不存在'});return
                self.send(200,result)
            except (ValueError,OSError) as e:self.send(400,{'error':str(e)})
    return Handler


def main(argv=None):
    parser=argparse.ArgumentParser(description='B601-RS 本地控制台：启动网页不连接硬件')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    args=parser.parse_args(argv)
    if not ready():parser.error('Run python -m stararm_rs_feedback.resources before starting the dashboard')
    app=Dashboard(args.root)
    lock=(app.store/'server.lock').open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:parser.error('这个目录已有网页服务，请打开原来的页面')
    server=Server(('127.0.0.1',args.port),make_handler(app))
    print(f'RS 本地控制台：http://127.0.0.1:{server.server_port}\n网页已启动，尚未连接硬件。关闭网页标签不会停止机械臂。',flush=True)
    try:server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:pass
    finally:
        app.stop()
        if app.proc:
            print('等待遥操作正常清理；不强制终止。',flush=True)
            while app.running():time.sleep(.1)
        server.server_close();lock.close()

if __name__=='__main__':main()
