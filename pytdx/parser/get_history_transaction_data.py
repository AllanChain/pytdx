# coding=utf-8

import struct

import six

from pytdx.params import TDXParams
from pytdx.parser.base import BaseParser
from pytdx.parser.opening_auction import scan_opening_page
from pytdx.parser.ticks import HISTORY_LAYOUT, parse_ticks


class GetHistoryTransactionData(BaseParser):

    # 该命令一页的载荷格式与单页上限（翻页查询按 page_size 步进）
    layout = HISTORY_LAYOUT
    page_size = TDXParams.MAX_TRANSACTION_COUNT

    def setParams(self, market, code, start, count, date):
        if type(code) is six.text_type:
            code = code.encode("utf-8")

        if type(date) is (type(date) is six.text_type) or (type(date) is six.binary_type):
            date = int(date)

        pkg = bytearray.fromhex(u'0c 01 30 01 00 01 12 00 12 00 b5 0f')
        pkg.extend(struct.pack("<IH6sHH", date, market, code, start, count))
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        return parse_ticks(body_buf, self.layout)


class GetHistoryOpeningAuction(GetHistoryTransactionData):
    """``GetHistoryTransactionData`` 的轻量版本：只扫描到 09:25 正式撮合。

    ``parseResponse`` 返回 :class:`OpeningScan`。
    """

    def parseResponse(self, body_buf):
        return scan_opening_page(body_buf, self.layout)


if __name__ == '__main__':
    from pytdx.hq import TdxHq_API
    api = TdxHq_API()
    with api.connect():
        print(api.to_df(api.get_history_transaction_data(0, '000001', 0, 10, 20170811)))
