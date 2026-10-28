# coding=utf-8

import struct

import six

from pytdx.helper import build_v2_request
from pytdx.log import log
from pytdx.params import TDXParams
from pytdx.parser.base import BaseParser
from pytdx.parser.opening_auction import scan_opening_page
from pytdx.parser.ticks import TODAY_LAYOUT, parse_ticks

"""
当日分笔成交（含集合竞价段）

2026-07 服务端协议更新后，旧帧 `0c 17 08 01 ...` 被静默丢弃，这里改用
新协议命令 `0x0fc5`：

    请求（24B，新协议帧头见 `helper.build_v2_request`）::

        0c | msg_id u32 | 01 | u16 长度 | u16 长度 | c5 0f
        | market u8 | 00 | code 6B | start u16 | count u16

        * start 是**从最新一笔往回**的偏移（0 = 最新一页，与旧协议一致），
          要取 09:15 起的竞价段需要按 count 翻页翻到底
        * count 单页上限 1800（超过时服务端截断且不报错，这里按上限收敛）

    响应载荷::

        [u16 记录数] + N × 变长记录::

            [u16 距午夜分钟数][价差 varint][成交量][成交笔数][状态][保留]

        价格 = 累加价差 / 100；变长整数用的是与旧协议相同的编码
        （见 `helper.get_price`）。

    状态（`buyorsell` 字段）::

        0 / 1 : 主动卖 / 主动买（连续竞价）
        2     : 09:25 正式撮合，即集合竞价成交（价 = 开盘价）
        5     : 15:05-15:30 盘后固定价格成交
        8     : 集合竞价过程快照（09:15-09:24 / 14:57-15:00），vol 恒为 0

    所以竞价数据有两条路：
      * `get_auction_series()`：竞价过程的价 / 虚拟匹配量 / 未匹配量（秒级）
      * `get_opening_auction()`：09:25 正式撮合的成交价 / 成交量 / 笔数

参考: https://github.com/electkismet/eltdx
      （docs/methods/7709-当日成交明细.md）
"""

# 命令号
TYPE_TODAY_TICKS = 0x0fc5


class GetTransactionData(BaseParser):

    # 该命令一页的载荷格式与单页上限（翻页查询按 page_size 步进）
    layout = TODAY_LAYOUT
    page_size = TDXParams.MAX_TICK_COUNT

    def setParams(self, market, code, start, count):
        """
        :param market: 市场代码，0=深圳 1=上海
        :param code: 6 位代码
        :param start: 从最新一笔往回数的偏移，0 = 最新一页
        :param count: 条数，上限 1800
        """
        if isinstance(code, six.text_type):
            code = code.encode("utf-8")
        code = code.strip()
        if len(code) != 6:
            raise ValueError(
                "stock code must be 6 bytes/characters, got: %r" % (code,))

        count = int(count)
        if count <= 0:
            raise ValueError("count must be positive, got: %r" % (count,))
        if count > TDXParams.MAX_TICK_COUNT:
            log.debug("count %d exceeds server limit, truncated to %d"
                      % (count, TDXParams.MAX_TICK_COUNT))
            count = TDXParams.MAX_TICK_COUNT

        start = int(start)
        if not 0 <= start <= 0xffff:
            raise ValueError(
                "start must be within 0..65535, got: %r" % (start,))

        self.market = market
        self.code = code

        payload = bytearray([market, 0])
        payload.extend(code)
        payload.extend(struct.pack("<HH", start, count))
        self.send_pkg = build_v2_request(TYPE_TODAY_TICKS, payload)

    def parseResponse(self, body_buf):
        return parse_ticks(body_buf, self.layout)


class GetOpeningAuction(GetTransactionData):
    """``GetTransactionData`` 的轻量版本：只扫描到 09:25 正式撮合。

    ``parseResponse`` 返回 :class:`OpeningScan`。
    """

    def parseResponse(self, body_buf):
        return scan_opening_page(body_buf, self.layout)
