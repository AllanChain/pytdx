# coding=utf-8

"""逐笔成交（当日 ``0x0fc5`` / 历史 ``0x0fb5``）的共享解码。

两路载荷只差三件事：首条记录的偏移、每条的字段个数与含义、状态字段的位置。
价格是**页内累加**的价差，所以只能从页首顺序解码；只想取单条记录（例如
09:25 集合竞价）的调用方应消费 :func:`iter_ticks`，命中后立即停止。
"""

from collections import OrderedDict, namedtuple
import struct

from pytdx.helper import get_price, get_time
from pytdx.log import log

# 成交状态（buyorsell 字段）
# 0 / 1 = 主动卖 / 主动买（连续竞价），5 = 盘后固定价格成交
STATUS_AUCTION_SNAPSHOT = 8  # 竞价过程快照，vol 恒为 0


def _format_row(hour, minute, price, **values):
    row = OrderedDict([
        ("time", "%02d:%02d" % (hour, minute)),
        ("price", float(price) / 100),
    ])
    row.update(values)
    return row


class TodayTick(namedtuple("TodayTick", "diff vol num status reserved")):
    """``0x0fc5`` 的一条记录。"""

    def row(self, hour, minute, price):
        return _format_row(hour, minute, price, vol=self.vol, num=self.num,
                           buyorsell=self.status)


class HistoryTick(namedtuple("HistoryTick", "diff vol status reserved")):
    """``0x0fb5`` 的一条记录（没有成交笔数）。"""

    def row(self, hour, minute, price):
        return _format_row(hour, minute, price, vol=self.vol,
                           buyorsell=self.status)


# offset: 首条记录的载荷偏移
# record: 记录类型，字段名与顺序即载荷字段名与顺序
RecordLayout = namedtuple("RecordLayout", "offset record")

TODAY_LAYOUT = RecordLayout(offset=2, record=TodayTick)
HISTORY_LAYOUT = RecordLayout(offset=6, record=HistoryTick)


def iter_ticks(body_buf, layout):
    """惰性产出 ``(hour, minute, price, record)``。

    ``price`` 是页内累加后的价格（分）。载荷截断时提前结束，不抛异常。
    """
    if len(body_buf) < 2:
        return

    (num,) = struct.unpack("<H", body_buf[:2])
    field_count = len(layout.record._fields)
    pos = layout.offset
    last_price = 0
    for _ in range(num):
        try:
            hour, minute, pos = get_time(body_buf, pos)
            raw = []
            for _ in range(field_count):
                value, pos = get_price(body_buf, pos)
                raw.append(value)
        except Exception:
            log.debug("transaction payload truncated at %d" % pos)
            return

        record = layout.record(*raw)
        last_price += record.diff
        yield hour, minute, last_price, record


def parse_ticks(body_buf, layout):
    """完整解析一页，返回对外字典列表。"""
    return [record.row(hour, minute, price)
            for hour, minute, price, record in iter_ticks(body_buf, layout)]
