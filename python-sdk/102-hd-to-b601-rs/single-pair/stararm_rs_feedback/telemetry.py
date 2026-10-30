"""Nonblocking, atomic telemetry messages over an inherited local socket."""
import json
import socket

MAX_FRAME_BYTES=65536

class TelemetrySender:
    def __init__(self,fd):
        if type(fd) is not int or fd<0:raise ValueError('Invalid telemetry descriptor')
        self.socket=socket.socket(fileno=fd)
        if self.socket.type != socket.SOCK_DGRAM:
            self.socket.close();raise ValueError('Telemetry requires a datagram socket')
        self.socket.setblocking(False)

    def send(self,value):
        data=json.dumps(value,ensure_ascii=False,allow_nan=False).encode('utf-8')
        if len(data)>MAX_FRAME_BYTES:return False
        try:
            self.socket.send(data);return True
        except OSError:
            return False

    def close(self):self.socket.close()
