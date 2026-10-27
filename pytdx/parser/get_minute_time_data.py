# coding=utf-8

from collections import OrderedDict
import struct

import six

from pytdx.log import log
from pytdx.parser.base import BaseParser

"""
当日分时行情

2026-07 起旧帧（`0c 1b 08 00 ...`）返回的是残缺数据，解析出来是乱码。
这里改用新协议的分时帧（方法 0x122d，50 字节）::

    u16 0x0007 | u16 0x003a | u16 0x0101 | u16 长度 | u16 长度 | u16 0x122d
    | market @12 | code 6B @14 | ...

响应载荷（16 字节帧头已剥离）::

    [0:2]    市场回显
    [2:8]    代码回显（ASCII）
    [24:28]  日期 YYYYMMDD (u32)
    [29:33]  昨收 f32
    [33:35]  记录槽位数（u16，可能比实际记录多 1）
    [35:37]  首条记录的分钟数（570 = 09:30）
    [37:...] 18 字节记录：[f32 价格][f32 均价][u32 成交量(手)][u32 保留]
             [u16 距午夜分钟数]（571 = 09:31）

尾部是摘要/名称区，解析时以「分钟数递增且在交易时段内」为截停条件。
"""

_MINUTE_PKG = bytearray.fromhex(
    '0007003a0101280028002d1200004330'
    '44453030000000000000000000000000'
    '00000000000000000100000000000000'
    '0000'
)

_MARKET_OFFSET = 12
_CODE_OFFSET = 14

_RECORD_OFFSET = 37
_RECORD_SIZE = 18

# A 股连续竞价时段（含集合竞价），分钟数 = 距午夜分钟
_MIN_MINUTE = 570
_MAX_MINUTE = 960


class GetMinuteTimeData(BaseParser):

    def setParams(self, market, code):
        if isinstance(code, six.text_type):
            code = code.encode("utf-8")
        code = code.strip()
        if len(code) != 6:
            raise ValueError(
                "stock code must be 6 bytes/characters, got: %r" % (code,))

        self.market = market
        self.code = code

        pkg = bytearray(_MINUTE_PKG)
        pkg[_MARKET_OFFSET] = market
        pkg[_CODE_OFFSET: _CODE_OFFSET + 6] = code
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        if len(body_buf) < _RECORD_OFFSET:
            return []

        if body_buf[2:8] != self.code:
            log.debug("minute code echo mismatch: %r != %r"
                      % (body_buf[2:8], self.code))
            return []

        (slot_count,) = struct.unpack("<H", body_buf[33:35])

        prices = []
        pos = _RECORD_OFFSET
        last_minute = None
        for _ in range(slot_count):
            if pos + _RECORD_SIZE > len(body_buf):
                break

            record = body_buf[pos: pos + _RECORD_SIZE]
            (price, _avg) = struct.unpack("<2f", record[0:8])
            (vol, _reserved) = struct.unpack("<2I", record[8:16])
            (minute,) = struct.unpack("<H", record[16:18])

            # 槽位数可能包含一个不存在的记录，尾部摘要区也会被误读成记录，
            # 用时间字段的合法性 + 单调递增来截停
            if not (_MIN_MINUTE <= minute <= _MAX_MINUTE):
                break
            if not (0.0 < price <= 1e6):
                break
            if last_minute is not None and minute <= last_minute:
                break
            last_minute = minute
            pos += _RECORD_SIZE

            prices.append(OrderedDict([
                ("price", round(price, 3)),
                ("vol", vol),
            ]))
        return prices
