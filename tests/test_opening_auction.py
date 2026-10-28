# coding: utf-8

import struct

from pytdx.hq import TdxHq_API
from pytdx.parser.get_history_transaction_data import GetHistoryOpeningAuction
from pytdx.parser.get_transaction_data import GetOpeningAuction
from pytdx.parser.opening_auction import (
    OPENING_MATCH_MINUTES, OpeningScan, opening_matches, scan_opening_page)
from pytdx.parser.ticks import (HISTORY_LAYOUT, STATUS_AUCTION_SNAPSHOT,
                                TODAY_LAYOUT, parse_ticks)

OPENING = OPENING_MATCH_MINUTES
SNAPSHOT = STATUS_AUCTION_SNAPSHOT


def encode_signed(value):
    """Encode one TDX variable-length signed integer."""
    out = bytearray()
    sign = value < 0
    value = abs(value)
    first = value & 0x3F
    value >>= 6
    if sign:
        first |= 0x40
    if value:
        first |= 0x80
        out.append(first)
        while value:
            byte = value & 0x7F
            value >>= 7
            if value:
                byte |= 0x80
            out.append(byte)
    else:
        out.append(first)
    return bytes(out)


def build_today_page(rows):
    body = bytearray(struct.pack("<H", len(rows)))
    for minutes, delta, vol, order_count, status in rows:
        body += struct.pack("<H", minutes)
        for value in (delta, vol, order_count, status, 0):
            body += encode_signed(value)
    return bytes(body)


def build_history_page(rows):
    body = bytearray(struct.pack("<H", len(rows)))
    body += b"\x00\x00\x00\x00"
    for minutes, delta, vol, status in rows:
        body += struct.pack("<H", minutes)
        for value in (delta, vol, status, 0):
            body += encode_signed(value)
    return bytes(body)


def test_scan_today_page_finds_opening_match():
    body = build_today_page([
        (OPENING - 1, 1000, 100, 5, SNAPSHOT),
        (OPENING, 0, 300, 7, 2),
        (OPENING + 1, 10, 5, 1, 1),
    ])

    scan = scan_opening_page(body, TODAY_LAYOUT)

    assert scan.matched == {
        "time": "09:25",
        "price": 10.0,
        "vol": 300,
        "num": 7,
        "buyorsell": 2,
    }
    assert scan.done is True


def test_scan_today_page_skips_whole_page_after_opening():
    body = build_today_page([
        (OPENING + 10, 100, 1, 1, 1),
        (OPENING + 11, 1, 2, 1, 0),
    ])

    # 页首已晚于 09:25：让调用方继续往回翻页
    assert scan_opening_page(body, TODAY_LAYOUT) == OpeningScan(None, False)


def test_scan_today_page_ignores_snapshot_at_opening():
    body = build_today_page([
        (OPENING, 1000, 100, 5, SNAPSHOT),
        (OPENING + 1, 1, 5, 1, 1),
    ])

    # 竞价段结束仍只有快照：更早的页不会再有正式撮合
    assert scan_opening_page(body, TODAY_LAYOUT) == OpeningScan(None, True)


def test_scan_continues_past_snapshot_to_match():
    body = build_today_page([
        (OPENING, 1000, 100, 5, SNAPSHOT),
        (OPENING, 0, 300, 7, 2),
    ])

    assert scan_opening_page(body, TODAY_LAYOUT).matched["vol"] == 300


def test_scan_history_page_finds_opening_match():
    body = build_history_page([
        (OPENING - 1, 500, 20, SNAPSHOT),
        (OPENING, 0, 80, 2),
        (OPENING + 1, 1, 3, 1),
    ])

    scan = scan_opening_page(body, HISTORY_LAYOUT)

    assert scan.matched == {
        "time": "09:25",
        "price": 5.0,
        "vol": 80,
        "buyorsell": 2,
    }
    assert scan.done is True


def test_scan_history_page_skips_whole_page_after_opening():
    body = build_history_page([(OPENING + 10, 100, 1, 1)])

    assert scan_opening_page(body, HISTORY_LAYOUT) == OpeningScan(None, False)


def test_scan_empty_and_truncated_pages():
    assert scan_opening_page(b"", TODAY_LAYOUT) == OpeningScan(None, True)
    assert scan_opening_page(b"", HISTORY_LAYOUT) == OpeningScan(None, True)
    empty = struct.pack("<H", 0)
    assert scan_opening_page(empty, TODAY_LAYOUT) == OpeningScan(None, True)

    truncated = struct.pack("<H", 1) + struct.pack("<H", OPENING) + b"\x80"
    assert scan_opening_page(truncated, TODAY_LAYOUT) == \
        OpeningScan(None, True)


def test_scan_matches_full_parse():
    today_body = build_today_page([
        (OPENING - 1, 1000, 100, 5, SNAPSHOT),
        (OPENING, 0, 300, 7, 2),
        (OPENING + 1, 10, 5, 1, 1),
    ])
    history_body = build_history_page([
        (OPENING - 1, 500, 20, SNAPSHOT),
        (OPENING, 0, 80, 2),
        (OPENING + 1, 1, 3, 1),
    ])

    for body, layout in ((today_body, TODAY_LAYOUT),
                         (history_body, HISTORY_LAYOUT)):
        full = parse_ticks(body, layout)
        scan = scan_opening_page(body, layout)
        assert [row["time"] for row in full] == ["09:24", "09:25", "09:26"]
        assert scan.matched == next(
            row for row in full
            if row["time"] == "09:25" and row["buyorsell"] != SNAPSHOT)


def test_opening_parser_subclasses_return_scan():
    today_body = build_today_page([(OPENING, 1000, 100, 5, 2)])
    history_body = build_history_page([(OPENING, 1000, 100, 2)])

    today = GetOpeningAuction(None).parseResponse(today_body)
    history = GetHistoryOpeningAuction(None).parseResponse(history_body)

    assert today == OpeningScan({
        "time": "09:25",
        "price": 10.0,
        "vol": 100,
        "num": 5,
        "buyorsell": 2,
    }, True)
    assert history == OpeningScan({
        "time": "09:25",
        "price": 10.0,
        "vol": 100,
        "buyorsell": 2,
    }, True)


def test_opening_matches_filters_parsed_rows():
    body = build_today_page([
        (OPENING - 1, 1000, 100, 5, SNAPSHOT),
        (OPENING, 0, 300, 7, 2),
        (OPENING + 1, 10, 5, 1, 1),
    ])
    rows = parse_ticks(body, TODAY_LAYOUT)

    assert opening_matches(rows) == [
        scan_opening_page(body, TODAY_LAYOUT).matched]


class FakeOpeningParser(object):
    """按脚本返回 OpeningScan 的假解析器，记录 setParams 收到的分页参数。"""

    page_size = 100
    pages = []
    calls = []

    def __init__(self, client, lock=None):
        pass

    def setParams(self, market, code, start, count, *extra):
        FakeOpeningParser.calls.append((start, count, extra))

    def call_api(self):
        return FakeOpeningParser.pages.pop(0)


def find_opening_auction(pages, max_pages, *extra):
    FakeOpeningParser.pages = list(pages)
    FakeOpeningParser.calls = []
    api = TdxHq_API()
    result = api._find_opening_auction(
        FakeOpeningParser, max_pages, 0, "000001", *extra)
    return result, FakeOpeningParser.calls


def test_find_opening_auction_pages_back():
    match = {"time": "09:25", "price": 11.43}

    result, calls = find_opening_auction(
        [OpeningScan(None, False), OpeningScan(match, True)], 5)

    assert result == match
    assert calls == [(0, 100, ()), (100, 100, ())]


def test_find_opening_auction_stops_when_done():
    result, calls = find_opening_auction([OpeningScan(None, True)], 5)

    assert result is None
    assert calls == [(0, 100, ())]


def test_find_opening_auction_gives_up_after_max_pages():
    result, calls = find_opening_auction([OpeningScan(None, False)] * 3, 3)

    assert result is None
    assert len(calls) == 3


def test_find_opening_auction_forwards_history_date():
    result, calls = find_opening_auction(
        [OpeningScan(None, True)], 5, 20261027)

    assert result is None
    assert calls == [(0, 100, (20261027,))]
