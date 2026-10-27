# coding=utf-8

from pytdx.parser.base import BaseParser
from pytdx.helper import get_datetime, get_volume, get_price
from collections import OrderedDict
import struct


class SetupCmd1(BaseParser):
    def setup(self):
        self.send_pkg = bytearray.fromhex(u'0c 02 18 93 00 01 03 00 03 00 0d 00 01')

    def parseResponse(self, body_buf):
        return body_buf


class SetupCmd2(BaseParser):
    def setup(self):
        self.send_pkg = bytearray.fromhex(u'0c 02 18 94 00 01 03 00 03 00 0d 00 02')

    def parseResponse(self, body_buf):
        return body_buf


class SetupCmd3(BaseParser):

    def setup(self):
        self.send_pkg = bytearray.fromhex(u'0c 03 18 99 00 01 20 00 20 00 db 0f d5'
                                      u'd0 c9 cc d6 a4 a8 af 00 00 00 8f c2 25'
                                      u'40 13 00 00 d5 00 c9 cc bd f0 d7 ea 00'
                                      u'00 00 02')

    def parseResponse(self, body_buf):
        return body_buf


class SetupCmdV2(BaseParser):
    """
    新一代行情协议的登录帧（80 字节，官方客户端建连后立即发送）。

    2026-07 起通达信服务端只对新帧格式的**行情类**请求应答（K 线 / 快照 /
    分时 / 逐笔），旧的 `0c 02` 系请求会静默返回空数据。目录、财务、除权除息、
    历史分时等命令仍旧使用老帧，所以连接建立后 SetupCmd1/2/3 和这一条登录帧
    需要都发出去：先老后新，两类命令可以在同一条连接上交替使用。

    参考: https://github.com/jiangtaovan/tdxrs/pull/14
    """

    def setup(self):
        self.send_pkg = bytearray.fromhex(
            u'000300010001460046000f1204002d31'
            u'00000000000000000027100e00000000'
            u'00000000000000000000000000000000'
            u'00000000000000000000000000000000'
            u'00000000000000000000000000000000')

    def parseResponse(self, body_buf):
        return body_buf