# coding=utf-8

from collections import OrderedDict
import struct

import six

from pytdx.log import log
from pytdx.parser.base import BaseParser

"""
实时快照（原 get_security_quotes）

2026-07 起旧帧（`0c 02 18 93` 系列之后的老快照请求）被服务端静默丢弃，
响应固定为 4 字节空包。这里改用新协议的快照帧（方法 0x122b，58 字节）::

    u16 0x0005 | u16 0x0029 | u16 0x0001 | u16 长度 | u16 长度 | u16 0x122b
    | ... | market @34 | code 6B @36 | ...

响应载荷（16 字节帧头已剥离）::

    [28:34]  代码回显（ASCII）
    [锚点:]  五个 f32：[昨收][开][高][低][现价]
    [锚点+20] u32 成交量（个股为手，指数为股，服务端原样返回）
    [锚点+24] f32 未知
    [锚点+28] f32 成交额(元)
    [锚点+32] u32 外盘(手, s_vol)
    [锚点+36] u32 内盘(手, b_vol)
    [锚点+40] f32 流通股本(万股) / [锚点+44] f32 总股本(万股)
    [锚点+68] f32 买一价 / [锚点+72] f32 卖一价

价格块没有固定偏移（载荷里混有请求回显和变长 GBK 名称区），因此用
OHLC 关系 + 量额互洽来锚定，见 _find_price_block。指数快照的成交额/成交量
与指数点位不成比例，量额判据不适用，会退化为只校验 OHLC。

与旧协议相比，新快照**只提供一档买卖价，没有档位量、没有二至五档**，
这些字段统一返回 None；active1 / reversed_bytes* 等调试字段同样是 None。
"""

_QUOTE_PKG = bytearray.fromhex(
    '000500290001300030002b12ffffffffff58ff07000000020000000000000000'
    '0100000043304445303000000000000000000000000000000000'
)

_MARKET_OFFSET = 34
_CODE_OFFSET = 36

# 响应载荷里代码回显的位置
_CODE_ECHO_OFFSET = 28

# 价格块锚点相对偏移
_OFF_LAST_CLOSE = 0
_OFF_OPEN = 4
_OFF_HIGH = 8
_OFF_LOW = 12
_OFF_PRICE = 16
_OFF_VOL = 20
_OFF_FIELD24 = 24
_OFF_AMOUNT = 28
_OFF_S_VOL = 32
_OFF_B_VOL = 36
_OFF_BID1 = 68
_OFF_ASK1 = 72


class GetSecurityQuotesCmd(BaseParser):

    def setParams(self, all_stock):
        """
        :param all_stock: 一个包含 (market, code) 元组的列表， 如 [ (0, '000001'), (1, '600001') ]
        :return:
        """
        stocks = []
        for stock in all_stock:
            market, code = stock
            if isinstance(code, six.text_type):
                code = code.encode("utf-8")
            code = code.strip()
            if len(code) != 6:
                raise ValueError(
                    "stock code must be 6 bytes/characters, got: %r" % (code,))
            stocks.append((market, code))
        self.stocks = stocks

    def call_api(self):
        # 新协议的快照帧一次只能查一只股票，这里串行拼成批量结果；
        # 锁放在整个批次外面，避免多线程时批次之间互相插包
        if self.lock:
            with self.lock:
                return self._call_batch()
        return self._call_batch()

    def _call_batch(self):
        quotes = []
        for market, code in self.stocks:
            self.market = market
            self.code = code
            self.send_pkg = self._build_pkg(market, code)
            one = self._call_api()
            if one:
                quotes.append(one)
        return quotes

    def _build_pkg(self, market, code):
        pkg = bytearray(_QUOTE_PKG)
        pkg[_MARKET_OFFSET] = market
        pkg[_CODE_OFFSET: _CODE_OFFSET + 6] = code
        return pkg

    def parseResponse(self, body_buf):
        if len(body_buf) < 34:
            # 服务端短帧：无此代码数据
            log.debug("quote short frame: %d bytes" % len(body_buf))
            return None

        if body_buf[_CODE_ECHO_OFFSET:_CODE_ECHO_OFFSET + 6] != self.code:
            log.debug("quote code echo mismatch: %r != %r"
                      % (body_buf[_CODE_ECHO_OFFSET:_CODE_ECHO_OFFSET + 6],
                         self.code))
            return None

        anchor = self._find_price_block(body_buf)
        if anchor is not None:
            def price(off):
                return round(struct.unpack(
                    "<f", body_buf[anchor + off: anchor + off + 4])[0], 3)

            def uint(off):
                return struct.unpack(
                    "<I", body_buf[anchor + off: anchor + off + 4])[0]

            last_close = price(_OFF_LAST_CLOSE)
            open_price = price(_OFF_OPEN)
            high = price(_OFF_HIGH)
            low = price(_OFF_LOW)
            current = price(_OFF_PRICE)
            vol = uint(_OFF_VOL)
            amount = price(_OFF_AMOUNT)
            s_vol = uint(_OFF_S_VOL)
            b_vol = uint(_OFF_B_VOL)
            bid1 = price(_OFF_BID1)
            ask1 = price(_OFF_ASK1)
            # 指数快照没有买卖盘（那两个槽位是别的字段），且一档价必须
            # 紧挨着现价才认
            if not (0 < bid1 <= 1e6 and 0 < ask1 <= 1e6
                    and abs(ask1 - bid1) <= max(current * 0.02, 0.02)
                    and current * 0.9 <= bid1 <= current * 1.1
                    and current * 0.9 <= ask1 <= current * 1.1):
                bid1 = ask1 = None
        else:
            # 停牌 / 无成交的退化快照：只有昨收，其余为零
            last_close = self._find_no_quote_last_close(body_buf)
            if last_close is None:
                log.debug("quote payload has no price block, skip")
                return None
            open_price = high = low = current = 0.0
            vol = s_vol = b_vol = 0
            amount = 0.0
            bid1 = ask1 = None

        return OrderedDict([
            ("market", self.market),
            ("code", self.code.decode("utf-8")),
            ("active1", None),
            ("price", current),
            ("last_close", last_close),
            ("open", open_price),
            ("high", high),
            ("low", low),
            ("reversed_bytes0", None),
            ("reversed_bytes1", None),
            ("vol", vol),
            ("cur_vol", None),
            ("amount", amount),
            ("s_vol", s_vol),
            ("b_vol", b_vol),
            ("reversed_bytes2", None),
            ("reversed_bytes3", None),
            ("bid1", bid1),
            ("ask1", ask1),
            ("bid_vol1", None),
            ("ask_vol1", None),
            ("bid2", None),
            ("ask2", None),
            ("bid_vol2", None),
            ("ask_vol2", None),
            ("bid3", None),
            ("ask3", None),
            ("bid_vol3", None),
            ("ask_vol3", None),
            ("bid4", None),
            ("ask4", None),
            ("bid_vol4", None),
            ("ask_vol4", None),
            ("bid5", None),
            ("ask5", None),
            ("bid_vol5", None),
            ("ask_vol5", None),
            ("reversed_bytes4", None),
            ("reversed_bytes5", None),
            ("reversed_bytes6", None),
            ("reversed_bytes7", None),
            ("reversed_bytes8", None),
            ("reversed_bytes9", None),
            ("active2", None),
        ])

    @staticmethod
    def _find_price_block(payload):
        """定位 [昨收][开][高][低][现价] 五连 f32 块，返回其起点偏移。

        价格块没有固定偏移，先按「OHLC 关系 + 量额互洽」找一遍（个股）；
        指数快照的成交额/成交量单位与指数点位不成比例，互洽判据不成立，
        因此再用「OHLC 关系 + 价格全距 + 成交量非零」宽松找一遍。
        """
        anchor = GetSecurityQuotesCmd._scan_price_block(payload, True)
        if anchor is None:
            anchor = GetSecurityQuotesCmd._scan_price_block(payload, False)
        return anchor

    @staticmethod
    def _scan_price_block(payload, check_amount):
        n = len(payload)
        for pos in range(32, n - 36):
            last_close, o, h, low, current = struct.unpack(
                "<5f", payload[pos: pos + 20])
            prices = (last_close, o, h, low, current)
            if not all(0.01 <= v <= 1e6 for v in prices):
                continue
            if not (h >= max(o, low, current) and low <= min(o, current)
                    and h >= low):
                continue
            # 同一根 K 线内最高/最低不会差太多（A 股涨跌幅限制）
            if max(prices) / min(prices) > 1.25:
                continue

            vol, = struct.unpack("<I", payload[pos + _OFF_VOL:
                                               pos + _OFF_VOL + 4])
            if vol <= 0:
                continue
            field24, = struct.unpack("<f", payload[pos + _OFF_FIELD24:
                                                   pos + _OFF_FIELD24 + 4])
            if not (0.0 < field24 < 1e4):
                continue

            if not check_amount:
                return pos

            amount, = struct.unpack("<f", payload[pos + _OFF_AMOUNT:
                                                  pos + _OFF_AMOUNT + 4])
            if amount > 0:
                avg = amount / (vol * 100.0)
                if not (low * 0.98 <= avg <= h * 1.02):
                    continue
            return pos
        return None

    @staticmethod
    def _find_no_quote_last_close(payload):
        """停牌/无成交退化快照：开高低为 0、现价为 0 或等于昨收、量额全 0。"""
        n = len(payload)
        for pos in range(n - 136, 32, -1):
            last_close, o, h, low, current = struct.unpack(
                "<5f", payload[pos: pos + 20])
            if not (0.01 < last_close <= 1e6):
                continue
            if o != 0.0 or h != 0.0 or low != 0.0:
                continue
            if current != 0.0 and current != last_close:
                continue
            vol, = struct.unpack("<I", payload[pos + _OFF_VOL:
                                               pos + _OFF_VOL + 4])
            amount, = struct.unpack("<f", payload[pos + _OFF_AMOUNT:
                                                  pos + _OFF_AMOUNT + 4])
            if vol == 0 and amount == 0.0:
                return round(last_close, 3)
        return None
