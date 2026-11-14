"""StarArm local dashboard; hardware opens only on Start."""
import argparse
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
from urllib.parse import unquote, urlsplit

from . import __version__
from .web_settings import defaults, validate, read, atomic_json, GRIPPER_FIELDS

PROJECT = 'stararm-rs-unloaded-damping'
WEB_ROOT = Path(__file__).parent / 'web'


class Dashboard:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.store = self.root / 'data/web'
        self.store.mkdir(parents=True, exist_ok=True)
        self.settings_path = self.store / 'settings.json'
        if not self.settings_path.exists():
            atomic_json(self.settings_path, defaults())
        initial = self.settings()
        history = self.store / f"settings_v{initial['revision']:06d}.json"
        if not history.exists():
            atomic_json(history, initial)
        self.token, self.lock = secrets.token_urlsafe(32), threading.RLock()
        self.proc = self.run_id = self.state_path = self.log_path = self.started = None
        self.stop_requested = False

    def settings(self):
        return read(self.settings_path)

    def save(self, body):
        with self.lock:
            value = validate(body)
            current = self.settings()
            if value['revision'] != current['revision']:
                raise ValueError('参数已被其他页面修改，请刷新后重试')
            fixed = set(current['gripper_lock']) - {'enabled', 'hold_mw', *GRIPPER_FIELDS}
            if any(value['gripper_lock'][key] != current['gripper_lock'][key] for key in fixed):
                raise ValueError('夹爪方向、运动判定和数据时效为固定参数')
            value['revision'] += 1
            atomic_json(self.store / f"settings_v{value['revision']:06d}.json", value)
            atomic_json(self.settings_path, value)
            return value

    def running(self):
        return self.proc is not None and self.proc.poll() is None

    @staticmethod
    def other_session(exclude_pid=None):
        modules = {'stararm_rs_feedback.dynamic', 'stararm_rs_feedback.trial',
                   'stararm_rs_feedback.preview', 'stararm_rs_feedback', 'stararm_rs_feedback.launcher',
                   'stararm_rs_feedback.diagnose_gripper_hold', 'stararm_rs_damping.teleoperate',
                   'lerobot.scripts.lerobot_teleoperate'}
        for path in Path('/proc').glob('[0-9]*/cmdline'):
            if exclude_pid is not None and path.parent.name == str(exclude_pid):
                continue
            try:
                args = path.read_bytes().decode(errors='replace').split('\0')
            except OSError:
                continue
            if '-m' in args:
                index = args.index('-m')
                if index + 1 < len(args) and args[index + 1] in modules:
                    return str(path.parent.name)
            if any(arg.endswith('/fs102hd_damping.py') or arg == 'fs102hd_damping.py' for arg in args):
                return str(path.parent.name)
        return None

    def build_command(self, state, run_id):
        return [sys.executable, '-u', '-m', 'stararm_rs_damping.teleoperate',
            '--settings', str(self.settings_path), '--web-state', str(state), '--web-run-id', run_id,
            '--robot.type=seeed_b601_rs_follower', '--robot.port=can0', '--robot.can_adapter=socketcan',
            '--robot.id=follower1', '--teleop.type=rebot_arm_102_leader', '--teleop.port=/dev/ttyUSB0',
            '--teleop.id=rebot_arm_102_leader', '--fps=30']

    def start(self, body):
        if body != {'mode': 'teleop'}:
            raise ValueError('请选择启动跟随')
        with self.lock:
            if self.running():
                raise ValueError('已有会话正在运行')
            other = self.other_session()
            if other:
                raise ValueError(f'另一个项目或终端的会话 PID {other} 正在使用机械臂，请先停止它')
            self.settings()
            run_id = time.strftime('%Y%m%d_%H%M%S') + '_' + secrets.token_hex(3)
            state, log = self.store / (run_id + '.json'), self.store / (run_id + '.log')
            runtime = self.root / 'vendor/runtime'
            if not (runtime / 'motorbridge_smart_servo').is_dir():
                raise ValueError('项目自带 SDK 缺失，请按 vendor/README.md 构建到 vendor/runtime')
            env = dict(os.environ, PYTHONPATH=os.pathsep.join((str(runtime), str(self.root), os.environ.get('PYTHONPATH', ''))))
            with log.open('x', encoding='utf-8') as out:
                proc = subprocess.Popen(self.build_command(state, run_id), cwd=self.root, env=env,
                    stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
            self.proc, self.run_id, self.state_path, self.log_path = proc, run_id, state, log
            self.started, self.stop_requested = time.time(), False
            return self.status()

    def stop(self):
        with self.lock:
            if self.running() and not self.stop_requested:
                self.proc.send_signal(signal.SIGINT)
                self.stop_requested = True
            return self.status()

    def status(self):
        with self.lock:
            running, value = self.running(), None
            if self.state_path and self.state_path.exists():
                try:
                    value = json.loads(self.state_path.read_text())
                    if value.get('run_id') != self.run_id:
                        value = None
                except (OSError, ValueError):
                    pass
            age = max(0., time.time() - value['wall_time']) if value else None
            fresh = running and value is not None and age < .8
            phase = ('stopping' if self.stop_requested else 'running' if fresh else 'connecting') if running else 'exited' if self.proc else 'idle'
            return dict(project=PROJECT, running=running, stop_requested=self.stop_requested, phase=phase,
                exit_code=self.proc.poll() if self.proc else None, run_id=self.run_id, started=self.started,
                age_s=age, fresh=fresh, telemetry=value, saved_revision=self.settings()['revision'],
                log_file=str(self.log_path) if self.log_path else None)

    def logs(self):
        if not self.log_path:
            return ''
        try:
            with self.log_path.open('rb') as handle:
                handle.seek(0, 2)
                handle.seek(max(0, handle.tell() - 18000))
                return handle.read().decode('utf-8', errors='replace')
        except OSError:
            return ''


class Server(ThreadingHTTPServer):
    daemon_threads = True


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, code, body, kind='application/json; charset=utf-8'):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(code)
            for key, value in {'Content-Type': kind, 'Content-Length': str(len(body)), 'Cache-Control': 'no-store',
                'X-Content-Type-Options': 'nosniff',
                'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"}.items():
                self.send_header(key, value)
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def local_request(self):
            return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')

        def do_GET(self):
            if not self.local_request():
                self.send(403, {'error': '仅允许本机访问'})
                return
            path = urlsplit(self.path).path
            if path == '/api/bootstrap':
                self.send(200, dict(token=app.token, settings=app.settings(), defaults=defaults(),
                    gripper_fields=GRIPPER_FIELDS, version=__version__, project=PROJECT))
                return
            if path == '/api/state':
                self.send(200, app.status())
                return
            if path == '/api/log':
                self.send(200, {'text': app.logs()})
                return
            rel = unquote(path).lstrip('/') or 'index.html'
            file = (WEB_ROOT / rel).resolve()
            if not file.is_relative_to(WEB_ROOT.resolve()) or not file.is_file():
                self.send(404, {'error': '文件不存在'})
                return
            self.send(200, file.read_bytes(), mimetypes.guess_type(file)[0] or 'application/octet-stream')

        def do_POST(self):
            if not self.local_request() or self.headers.get('X-RS-Token') != app.token:
                self.send(403, {'error': '网页会话已失效，请刷新'})
                return
            origin = self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'):
                self.send(403, {'error': '请求来源不匹配'})
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 32000 or self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    raise ValueError('需要有效 JSON 请求')
                body = json.loads(self.rfile.read(length))
                path = urlsplit(self.path).path
                if path == '/api/settings':
                    value = app.save(body)
                elif path == '/api/start':
                    value = app.start(body)
                elif path == '/api/stop' and body == {}:
                    value = app.stop()
                else:
                    raise ValueError('无效请求')
                self.send(200, value)
            except (ValueError, OSError) as error:
                self.send(400, {'error': str(error)})
    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    app = Dashboard(args.root)
    with (app.store / 'server.lock').open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError('本项目网页已在运行') from error
        server = Server(('127.0.0.1', args.port), make_handler(app))
        print(f'StarArm 空载阻尼工作台：http://127.0.0.1:{args.port}/；点击“启动跟随”连接设备', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            if app.running():
                app.stop()
                try:
                    app.proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print('会话清理尚未完成，请检查终端及设备状态', flush=True)
            server.server_close()


if __name__ == '__main__':
    main()
