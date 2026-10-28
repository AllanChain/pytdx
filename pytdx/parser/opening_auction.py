# coding=utf-8

"""09:25 集合竞价正式撮合的轻量扫描。

``get_opening_auction()`` / ``get_history_opening_auction()`` 只需要 09:25
这一条，但一页逐笔最多 1800 / 2000 条。这里消费 :func:`iter_ticks` 并在命中
09:25 时立即停止；页首时间已晚于 09:25 时只解码第一条记录就返回，交给调用
方继续往回翻页。
"""

from collections import namedtuple

from pytdx.parser.ticks import STATUS_AUCTION_SNAPSHOT, iter_ticks

OPENING_MATCH_MINUTES = 9 * 60 + 25  # 09:25
OPENING_MATCH_TIME = "%02d:%02d" % divmod(OPENING_MATCH_MINUTES, 60)

# matched: 09:25 正式撮合记录，或 None
# done: 不必再往回翻页（命中，或更早的页不可能再有 09:25 记录）
OpeningScan = namedtuple("OpeningScan", "matched done")


def opening_matches(ticks):
    """从一页成交明细里挑出 09:25 集合竞价正式撮合记录。

    注意不能用状态 2 单独判断：连续竞价里也有状态 2 的记录，必须同时看时间。

    :param ticks: `get_transaction_data` 的返回值
    :return: 命中的记录列表（正常情况下 0 或 1 条）
    """
    return [tick for tick in ticks
            if tick["time"] == OPENING_MATCH_TIME
            and tick["buyorsell"] != STATUS_AUCTION_SNAPSHOT]


def scan_opening_page(body_buf, layout):
    """扫描一页逐笔，返回 :class:`OpeningScan`。"""
    for i, (hour, minute, price, record) in enumerate(
            iter_ticks(body_buf, layout)):
        minutes = hour * 60 + minute
        if minutes > OPENING_MATCH_MINUTES:
            # 页内记录按时间升序排列：只有页首已晚于 09:25 时才继续往回翻页
            return OpeningScan(None, i > 0)
        if (minutes == OPENING_MATCH_MINUTES
                and record.status != STATUS_AUCTION_SNAPSHOT):
            return OpeningScan(record.row(hour, minute, price), True)

    # 扫到竞价时段（或页尾）仍没有正式撮合，更早的页也不会有
    return OpeningScan(None, True)
