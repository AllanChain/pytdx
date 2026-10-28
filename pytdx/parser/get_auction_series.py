# coding=utf-8

from collections import OrderedDict
import struct

import six

from pytdx.helper import build_v2_request
from pytdx.log import log
from pytdx.params import TDXParams
from pytdx.parser.base import BaseParser

"""
集合竞价过程快照（早盘 09:15-09:25 / 尾盘 14:57-15:00）

旧协议没有这条链路（竞价段只能从分笔里抠出 09:15-09:24 的价格，且没有
量），新协议（2026-07 起）提供了专用的竞价接口 `0x056a`，也就是官方
客户端竞价图用的那一帧：

    请求（40B，新协议帧头见 `helper.build_v2_request`）::

        0c | msg_id u32 | 01 | u16 长度 | u16 长度 | 6a 05
        | market u8 | 00 | code 6B | 日期 u32 | selector u32
        | 0 u32 | start u32 | limit u32

        * 日期 = 0 表示主站当前交易日，否则 YYYYMMDD（历史同样可取）
        * selector 默认 3，实测 0/1/2/3 返回一致
        * start / limit 为分页参数，服务端单次上限 500 条

    响应载荷::

        [u16 记录数] + N × 16B 记录::

            [u16 距午夜分钟数][f32 现价][u32 虚拟匹配量(手)]
            [i32 未匹配量(带符号，正 = 买方剩余 负 = 卖方剩余)]
            [u8 保留][u8 秒]

    与分笔里的竞价段相比，这里额外给出**虚拟匹配量**和**未匹配量**，
    每条间隔 3-10 秒，是竞价过程分析的权威入口（服务端保留约一年）。

    注意：序列末尾的 `09:25:00`（如果有）仍是**虚拟撮合**快照，不是成交。
    09:25 的正式撮合请用 `TdxHq_API.get_opening_auction()`。

参考: https://github.com/electkismet/eltdx
      （docs/methods/7709-集合竞价明细.md）
"""

# 命令号
TYPE_AUCTION_SERIES = 0x056a
# 单条记录长度
RECORD_SIZE = 16
# 竞价类型选择位，实测 0/1/2/3 等价
DEFAULT_SELECTOR = 3


class GetAuctionSeries(BaseParser):
    """读取当日 / 历史集合竞价过程快照。"""

    def setParams(self, market, code, date=None,
                  selector=DEFAULT_SELECTOR, start=0,
                  limit=TDXParams.MAX_AUCTION_COUNT):
        """
        :param market: 市场代码，0=深圳 1=上海
        :param code: 6 位股票代码，如 '000001'
        :param date: None/0 = 主站当前交易日；也可传 20261027、
                     '2026-10-27' 或 datetime.date
        :param selector: 竞价类型选择位，默认 3
        :param start: 分页起始序号
        :param limit: 单页条数，上限 500
        """
        if isinstance(code, six.text_type):
            code = code.encode("utf-8")
        code = code.strip()
        if len(code) != 6:
            raise ValueError(
                "stock code must be 6 bytes/characters, got: %r" % (code,))

        start = int(start)
        if start < 0:
            raise ValueError("start must not be negative, got: %r" % (start,))
        limit = int(limit)
        if limit <= 0:
            raise ValueError("limit must be positive, got: %r" % (limit,))
        if limit > TDXParams.MAX_AUCTION_COUNT:
            log.debug("limit %d exceeds server limit, truncated to %d"
                      % (limit, TDXParams.MAX_AUCTION_COUNT))
            limit = TDXParams.MAX_AUCTION_COUNT

        self.market = market
        self.code = code
        self.date = self._parse_date(date)

        payload = bytearray([market, 0])
        payload.extend(code)
        # 日期 / selector / 保留位 / start / limit
        payload.extend(struct.pack("<IIIII", self.date, selector, 0,
                                   start, limit))
        self.send_pkg = build_v2_request(TYPE_AUCTION_SERIES, payload)

    @staticmethod
    def _parse_date(date):
        """把 None / int / 'YYYY-MM-DD' / datetime.date 统一成 YYYYMMDD。"""
        if date in (None, 0, "", "0"):
            return 0
        if hasattr(date, "strftime"):
            return int(date.strftime("%Y%m%d"))
        if isinstance(date, six.string_types):
            return int(date.replace("-", "").replace("/", "")[:8])
        return int(date)

    def parseResponse(self, body_buf):
        if len(body_buf) < 2:
            return []

        (count,) = struct.unpack("<H", body_buf[:2])
        pos = 2
        points = []
        for _ in range(count):
            if pos + RECORD_SIZE > len(body_buf):
                log.debug("auction payload truncated at %d/%d"
                          % (pos, len(body_buf)))
                break
            (minute, price, matched_vol, unmatched_vol,
             _reserved, second) = struct.unpack(
                "<HfIibB", body_buf[pos: pos + RECORD_SIZE])
            pos += RECORD_SIZE

            points.append(OrderedDict([
                ("time", "%02d:%02d:%02d"
                 % (minute // 60, minute % 60, second)),
                ("price", round(price, 3)),
                # 虚拟匹配量（手）
                ("matched_vol", matched_vol),
                # 未匹配量，带符号：正 = 买方剩余，负 = 卖方剩余
                ("unmatched_vol", unmatched_vol),
            ]))
        return points
