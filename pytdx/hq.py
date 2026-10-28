# coding=utf-8

#
# Just for practising
#


import datetime
import os
import random
import socket
import sys
import threading

from pytdx.base_socket_client import BaseSocketClient, update_last_ack_time
from pytdx.heartbeat import HqHeartBeatThread
from pytdx.log import DEBUG, log
from pytdx.params import TDXParams
from pytdx.parser.get_auction_series import GetAuctionSeries
from pytdx.parser.get_company_info_category import GetCompanyInfoCategory
from pytdx.parser.get_company_info_content import GetCompanyInfoContent
from pytdx.parser.get_finance_info import GetFinanceInfo
from pytdx.parser.get_history_minute_time_data import GetHistoryMinuteTimeData
from pytdx.parser.get_history_transaction_data import (
    GetHistoryOpeningAuction, GetHistoryTransactionData)
from pytdx.parser.get_index_bars import GetIndexBarsCmd
from pytdx.parser.get_minute_time_data import GetMinuteTimeData
from pytdx.parser.get_security_bars import GetSecurityBarsCmd
from pytdx.parser.get_security_count import GetSecurityCountCmd
from pytdx.parser.get_security_list import GetSecurityList
from pytdx.parser.get_security_quotes import GetSecurityQuotesCmd
from pytdx.parser.get_transaction_data import (GetOpeningAuction,
                                               GetTransactionData)
from pytdx.parser.get_xdxr_info import GetXdXrInfo
from pytdx.parser.get_report_file import GetReportFile
from pytdx.parser.setup_commands import SetupCmd1, SetupCmd2, SetupCmd3, SetupCmdV2

if __name__ == '__main__':
    sys.path.append(os.path.dirname(
        os.path.dirname(os.path.realpath(__file__))))


class TdxHq_API(BaseSocketClient):

    # 是否在建连时发送旧协议登录帧（`0c 02 18 93/94` 那三帧）
    #
    # 2026-07 协议更新后，登录只用新帧（80B，见 SetupCmdV2）就够了：
    # 目录 / 财务 / 除权 / 历史分时 / 历史逐笔 在同一连接上照常应答，
    # 而且旧登录帧会把会话切到旧语义——当日逐笔 `0x0fc5` 会静默返回空包。
    # 只有对接仍只认旧帧的老主站时才需要打开。
    send_legacy_setup = False

    def setup(self):
        if self.send_legacy_setup:
            # 旧协议的会话（老主站目录 / 财务等命令可能需要）
            SetupCmd1(self.client).call_api()
            SetupCmd2(self.client).call_api()
            SetupCmd3(self.client).call_api()
        # 新协议的登录帧（2026-07 起 K 线 / 快照 / 分时 / 逐笔等行情命令
        # 必须使用新帧，否则服务端静默返回空数据）
        SetupCmdV2(self.client).call_api()

    # API List

    # Notice：，如果一个股票当天停牌，那天的K线还是能取到，成交量为0
    @update_last_ack_time
    def get_security_bars(self, category, market, code, start, count):
        cmd = GetSecurityBarsCmd(self.client, lock=self.lock)
        cmd.setParams(category, market, code, start, count)
        return cmd.call_api()

    @update_last_ack_time
    def get_index_bars(self, category, market, code, start, count):
        cmd = GetIndexBarsCmd(self.client, lock=self.lock)
        cmd.setParams(category, market, code, start, count)
        return cmd.call_api()

    @update_last_ack_time
    def get_security_quotes(self, all_stock, code=None):
        """
        支持三种形式的参数
        get_security_quotes(market, code )
        get_security_quotes((market, code))
        get_security_quotes([(market1, code1), (market2, code2)] )
        :param all_stock （market, code) 的数组
        :param code{optional} code to query
        :return:
        """

        if code is not None:
            all_stock = [(all_stock, code)]
        elif (isinstance(all_stock, list) or isinstance(all_stock, tuple))\
                and len(all_stock) == 2 and type(all_stock[0]) is int:
            all_stock = [all_stock]

        cmd = GetSecurityQuotesCmd(self.client, lock=self.lock)
        cmd.setParams(all_stock)
        return cmd.call_api()

    @update_last_ack_time
    def get_security_count(self, market):
        cmd = GetSecurityCountCmd(self.client, lock=self.lock)
        cmd.setParams(market)
        return cmd.call_api()

    @update_last_ack_time
    def get_security_list(self, market, start):
        cmd = GetSecurityList(self.client, lock=self.lock)
        cmd.setParams(market, start)
        return cmd.call_api()

    @update_last_ack_time
    def get_minute_time_data(self, market, code):
        cmd = GetMinuteTimeData(self.client, lock=self.lock)
        cmd.setParams(market, code)
        return cmd.call_api()

    @update_last_ack_time
    def get_history_minute_time_data(self, market, code, date):
        cmd = GetHistoryMinuteTimeData(self.client, lock=self.lock)
        cmd.setParams(market, code, date)
        return cmd.call_api()

    @update_last_ack_time
    def get_transaction_data(self, market, code, start, count):
        cmd = GetTransactionData(self.client, lock=self.lock)
        cmd.setParams(market, code, start, count)
        return cmd.call_api()

    @update_last_ack_time
    def get_auction_series(self, market, code, date=None, start=0,
                           limit=TDXParams.MAX_AUCTION_COUNT):
        """集合竞价过程快照（当日或历史）

        返回早盘 09:15-09:25 / 尾盘 14:57-15:00 的秒级竞价快照，每条含
        `time` / `price`（虚拟撮合价）/ `matched_vol`（虚拟匹配量，手）/
        `unmatched_vol`（未匹配量，正 = 买方剩余，负 = 卖方剩余）。

        注意：序列末尾的 09:25:00（如果有）仍是虚拟撮合，不是成交；
        正式撮合成交请用 `get_opening_auction()`。

        :param market: 市场代码 0=深圳 1=上海
        :param code: 6 位代码
        :param date: None/0 = 当前交易日；也可传 20261027 或 '2026-10-27'
        :param start: 分页起始序号
        :param limit: 单页条数，上限 500
        """
        cmd = GetAuctionSeries(self.client, lock=self.lock)
        cmd.setParams(market, code, date, start=start, limit=limit)
        return cmd.call_api()

    def _find_opening_auction(self, parser_cls, max_pages, market, code,
                              *extra):
        """按页往回翻，直到扫出 09:25 正式撮合或确定没有。

        每页只解码到 09:25；页首已晚于 09:25 时只解码第一条记录。
        单页条数取 ``parser_cls.page_size``。
        """
        page_size = parser_cls.page_size
        for page in range(max_pages):
            cmd = parser_cls(self.client, lock=self.lock)
            cmd.setParams(market, code, page * page_size, page_size, *extra)
            scan = cmd.call_api()
            if scan.done:
                return scan.matched
        log.debug("opening auction not found in %d pages" % max_pages)
        return None

    @update_last_ack_time
    def get_opening_auction(self, market, code, max_pages=20):
        """09:25 集合竞价正式撮合（成交价 / 成交量 / 笔数）

        内部从最新一页成交明细往回翻，取 `time == '09:25'` 且状态不是
        竞价快照的那一条；当天还没到 09:25 或超过 `max_pages` 页时返回 None。
        非交易日主站会返回最近一个交易日的数据。

        只解析到 09:25 为止，不完整解析每一页。

        :param market: 市场代码 0=深圳 1=上海
        :param code: 6 位代码
        :param max_pages: 最多翻多少页（每页 1800 条）
        :return: {'time', 'price', 'vol', 'num', 'buyorsell'} 或 None
        """
        return self._find_opening_auction(
            GetOpeningAuction, max_pages, market, code)

    @update_last_ack_time
    def get_history_opening_auction(self, market, code, date, max_pages=20):
        """历史某日 09:25 集合竞价正式撮合（成交价 / 成交量）

        与 :meth:`get_opening_auction` 相同，但读取历史逐笔（``0x0fb5``）。
        历史逐笔没有成交笔数字段，故不返回 ``num``。
        只解析到 09:25 为止，不完整解析每一页。

        :param market: 市场代码 0=深圳 1=上海
        :param code: 6 位代码
        :param date: 交易日期，如 20261027
        :param max_pages: 最多翻多少页（每页 2000 条）
        :return: {'time', 'price', 'vol', 'buyorsell'} 或 None
        """
        return self._find_opening_auction(
            GetHistoryOpeningAuction, max_pages, market, code, date)

    @update_last_ack_time
    def get_history_transaction_data(self, market, code, start, count, date):
        cmd = GetHistoryTransactionData(self.client, lock=self.lock)
        cmd.setParams(market, code, start, count, date)
        return cmd.call_api()

    @update_last_ack_time
    def get_company_info_category(self, market, code):
        cmd = GetCompanyInfoCategory(self.client, lock=self.lock)
        cmd.setParams(market, code)
        return cmd.call_api()

    @update_last_ack_time
    def get_company_info_content(self, market, code, filename, start, length):
        cmd = GetCompanyInfoContent(self.client, lock=self.lock)
        cmd.setParams(market, code, filename, start, length)
        return cmd.call_api()

    @update_last_ack_time
    def get_xdxr_info(self, market, code):
        cmd = GetXdXrInfo(self.client, lock=self.lock)
        cmd.setParams(market, code)
        return cmd.call_api()

    @update_last_ack_time
    def get_finance_info(self, market, code):
        cmd = GetFinanceInfo(self.client, lock=self.lock)
        cmd.setParams(market, code)
        return cmd.call_api()

    @update_last_ack_time
    def get_block_info_meta(self, blockfile):
        from pytdx.parser.get_block_info import GetBlockInfoMeta
        cmd = GetBlockInfoMeta(self.client, lock=self.lock)
        cmd.setParams(blockfile)
        return cmd.call_api()

    @update_last_ack_time
    def get_block_info(self, blockfile, start, size):
        from pytdx.parser.get_block_info import GetBlockInfo
        cmd = GetBlockInfo(self.client, lock=self.lock)
        cmd.setParams(blockfile, start, size)
        return cmd.call_api()

    def get_and_parse_block_info(self, blockfile):
        from pytdx.parser.get_block_info import get_and_parse_block_info
        return get_and_parse_block_info(self, blockfile)

    @update_last_ack_time
    def get_report_file(self, filename, offset):
        cmd = GetReportFile(self.client, lock=self.lock)
        cmd.setParams(filename, offset)
        return cmd.call_api()

    def get_report_file_by_size(self, filename, filesize=0, reporthook=None):
        """
        Download file from proxy server

        :param filename the filename to download
        :param filesize the filesize to download , if you do not known the actually filesize, leave this value 0
        """
        filecontent = bytearray(filesize)
        current_downloaded_size = 0
        get_zero_length_package_times = 0
        while current_downloaded_size < filesize or filesize == 0:
            response = self.get_report_file(filename, current_downloaded_size)
            if response["chunksize"] > 0:
                current_downloaded_size = current_downloaded_size + \
                    response["chunksize"]
                filecontent.extend(response["chunkdata"])
                if reporthook is not None:
                    reporthook(current_downloaded_size,filesize)
            else:
                get_zero_length_package_times = get_zero_length_package_times + 1
                if filesize == 0:
                    break
                elif get_zero_length_package_times > 2:
                    break

        return filecontent

    def do_heartbeat(self):
        self.get_security_count(random.randint(0, 1))

    def get_k_data(self, code, start_date, end_date):
        import pandas as pd

        # 具体详情参见 https://github.com/rainx/pytdx/issues/5
        # 具体详情参见 https://github.com/rainx/pytdx/issues/21
        def __select_market_code(code):
            code = str(code)
            if code[0] in ['5', '6', '9'] or code[:3] in ["009", "126", "110", "201", "202", "203", "204"]:
                return 1
            return 0
        # 新版一劳永逸偷懒写法zzz
        market_code = 1 if str(code)[0] == '6' else 0
        # https://github.com/rainx/pytdx/issues/33
        # 0 - 深圳， 1 - 上海

        # 单次最多 700 条（服务端上限），10 页足够覆盖 20 年以上的日线
        page_size = TDXParams.MAX_KLINE_COUNT
        data = pd.concat([self.to_df(self.get_security_bars(9, __select_market_code(
            code), code, (9 - i) * page_size, page_size)) for i in range(10)], axis=0)

        data = data.assign(date=data['datetime'].apply(lambda x: str(x)[0:10])).assign(code=str(code))\
            .set_index('date', drop=False)\
            .drop(['year', 'month', 'day', 'hour', 'minute', 'datetime'], axis=1)[start_date:end_date]
        return data.assign(date=data['date'].apply(lambda x: str(x)[0:10]))


if __name__ == '__main__':
    import pprint

    api = TdxHq_API()
    if api.connect('101.227.73.20', 7709):
        log.info("获取股票行情")
        stocks = api.get_security_quotes([(0, "000001"), (1, "600300")])
        pprint.pprint(stocks)
        log.info("获取k线")
        data = api.get_security_bars(9, 0, '000001', 4, 3)
        pprint.pprint(data)
        log.info("获取 深市 股票数量")
        pprint.pprint(api.get_security_count(0))
        log.info("获取股票列表")
        stocks = api.get_security_list(1, 255)
        pprint.pprint(stocks)
        log.info("获取指数k线")
        data = api.get_index_bars(9, 1, '000001', 1, 2)
        pprint.pprint(data)
        log.info("查询分时行情")
        data = api.get_minute_time_data(TDXParams.MARKET_SH, '600300')
        pprint.pprint(data)
        log.info("查询历史分时行情")
        data = api.get_history_minute_time_data(
            TDXParams.MARKET_SH, '600300', 20161209)
        pprint.pprint(data)
        log.info("查询分时成交")
        data = api.get_transaction_data(TDXParams.MARKET_SZ, '000001', 0, 30)
        pprint.pprint(data)
        log.info("查询历史分时成交")
        data = api.get_history_transaction_data(
            TDXParams.MARKET_SZ, '000001', 0, 10, 20170209)
        pprint.pprint(data)
        log.info("查询公司信息目录")
        data = api.get_company_info_category(TDXParams.MARKET_SZ, '000001')
        pprint.pprint(data)
        log.info("读取公司信息-最新提示")
        data = api.get_company_info_content(0, '000001', '000001.txt', 0, 10)
        pprint.pprint(data)
        log.info("读取除权除息信息")
        data = api.get_xdxr_info(1, '600300')
        pprint.pprint(data)
        log.info("读取财务信息")
        data = api.get_finance_info(0, '000001')
        pprint.pprint(data)
        log.info("日线级别k线获取函数")
        data = api.get_k_data('000001', '2017-07-01', '2017-07-10')
        pprint.pprint(data)

        api.disconnect()
