# coding=utf-8

from collections import OrderedDict
import struct

import six

from pytdx.log import log
from pytdx.parser.base import BaseParser

"""
获取 K 线数据（日线 / 周线 / 月线 / 分钟线）

2026 年 7 月起，通达信服务端启用了新一代行情帧格式：所有主站对旧的
`0c 01 08 64 ... 2d 05` 请求都会静默返回空数据（响应载荷固定为 `20 03`，
即 0 条记录），只有新帧才会被应答。因此这里改用新帧收发。

请求帧（58 字节，模板取自官方客户端）::

    u16 0x000a | u16 0x6800 | u16 0x0113 | u16 长度 | u16 长度 | u16 方法 0x122e
    | market u16 @12 | code 6B @14 | ... | category u16 @36
    | start u32 @40 | count u16 @44 | ...

    长度字段 = 帧总长 - 10；start 为相对最新一根 K 线的偏移（0 = 最新），
    服务端单次最多返回 700 条。

响应载荷（16 字节帧头已被 BaseParser 剥离）::

    [0:2]    市场回显
    [2:8]    代码回显（ASCII）
    [24:26]  category 回显
    [27:29]  本次返回的记录数（u16）
    [29:33]  start 回显
    [33:...] n 条 36 字节记录
    [-120:]  120 字节 GBK 名称区

36 字节记录::

    u32 日期(YYYYMMDD) | u32 时间(日线为 0，分钟线为距午夜的秒数)
    | f32 开 | f32 高 | f32 低 | f32 收 | f32 成交额(元)
    | f32 成交量 | f32 流通股本(万股)

    注意：成交量字段由服务端直接给出，单位随 category 而变（实测日线
    category=4 为股，category=9 为手），pytdx 不做换算，与旧协议行为一致。

参考: https://github.com/jiangtaovan/tdxrs/pull/14
"""

# 请求帧模板，代码字段用 "C0DE00" 占位，发送前替换
_BARS_PKG = bytearray.fromhex(
    '000a00681301300030002e1200004330444530300000000000000000000000'
    '00000000000400010000000000bc02000001010001000000000000'
)

_MARKET_OFFSET = 12
_CODE_OFFSET = 14
_CATEGORY_OFFSET = 36
_START_OFFSET = 40
_COUNT_OFFSET = 44

# 服务端单次返回上限
MAX_COUNT = 700

_RECORD_SIZE = 36
_RECORD_OFFSET = 33
_COUNT_OFFSET_IN_RESPONSE = 27


class GetSecurityBarsCmd(BaseParser):

    # 指数 K 线沿用旧返回结构，追加 up_count / down_count 两个字段
    _INCLUDE_INDEX_EXTRA_FIELDS = False

    def setParams(self, category, market, code, start, count):
        if isinstance(code, six.text_type):
            code = code.encode("utf-8")
        code = code.strip()
        if len(code) != 6:
            raise ValueError(
                "stock code must be 6 bytes/characters, got: %r" % (code,))

        count = int(count)
        if count > MAX_COUNT:
            log.debug("count %d exceeds server limit, truncated to %d"
                      % (count, MAX_COUNT))
            count = MAX_COUNT

        self.category = category
        self.code = code

        pkg = bytearray(_BARS_PKG)
        pkg[_MARKET_OFFSET] = market
        pkg[_CODE_OFFSET: _CODE_OFFSET + 6] = code
        pkg[_CATEGORY_OFFSET: _CATEGORY_OFFSET + 2] = struct.pack(
            "<H", category)
        pkg[_START_OFFSET: _START_OFFSET + 4] = struct.pack("<I", start)
        pkg[_COUNT_OFFSET: _COUNT_OFFSET + 2] = struct.pack("<H", count)

        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        if len(body_buf) < _RECORD_OFFSET:
            # 空数据（停牌 / 该周期无数据）
            return []

        if body_buf[2:8] != self.code:
            log.debug("code echo mismatch: %r != %r"
                      % (body_buf[2:8], self.code))
            return []

        (ret_count,) = struct.unpack(
            "<H", body_buf[_COUNT_OFFSET_IN_RESPONSE:
                           _COUNT_OFFSET_IN_RESPONSE + 2])
        # 防御：返回条数不能超过载荷实际容纳的记录数
        available = (len(body_buf) - _RECORD_OFFSET) // _RECORD_SIZE
        if ret_count > available:
            log.debug("response count %d exceeds payload records %d"
                      % (ret_count, available))
            ret_count = available

        klines = []
        pos = _RECORD_OFFSET
        for _ in range(ret_count):
            record = body_buf[pos: pos + _RECORD_SIZE]
            pos += _RECORD_SIZE

            (date, kline_time) = struct.unpack("<II", record[0:8])
            (price_open, price_high, price_low, price_close,
             amount, vol) = struct.unpack("<6f", record[8:32])

            if date == 0:
                continue

            year = date // 10000
            month = (date % 10000) // 100
            day = date % 100

            if self.category < 4 or self.category in (7, 8):
                # 分钟线：时间为距午夜秒数
                hour = kline_time // 3600
                minute = (kline_time % 3600) // 60
            else:
                # 日线及以上：旧协议固定返回 15:00
                hour, minute = 15, 0

            kline = OrderedDict([
                ("open", round(price_open, 3)),
                ("close", round(price_close, 3)),
                ("high", round(price_high, 3)),
                ("low", round(price_low, 3)),
                ("vol", round(vol, 3)),
                ("amount", round(amount, 3)),
                ("year", year),
                ("month", month),
                ("day", day),
                ("hour", hour),
                ("minute", minute),
                ("datetime", "%d-%02d-%02d %02d:%02d"
                 % (year, month, day, hour, minute))
            ])
            if self._INCLUDE_INDEX_EXTRA_FIELDS:
                # 新协议响应不含涨跌家数
                kline["up_count"] = None
                kline["down_count"] = None
            klines.append(kline)

        return klines
