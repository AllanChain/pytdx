# coding=utf-8


class TDXParams:

    #市场

    MARKET_SZ = 0  # 深圳
    MARKET_SH = 1  # 上海

    #K线种类
    # K 线种类
    # 0 -   5 分钟K 线
    # 1 -   15 分钟K 线
    # 2 -   30 分钟K 线
    # 3 -   1 小时K 线
    # 4 -   日K 线
    # 5 -   周K 线
    # 6 -   月K 线
    # 7 -   1 分钟
    # 8 -   1 分钟K 线
    # 9 -   日K 线
    # 10 -  季K 线
    # 11 -  年K 线

    KLINE_TYPE_5MIN = 0
    KLINE_TYPE_15MIN = 1
    KLINE_TYPE_30MIN = 2
    KLINE_TYPE_1HOUR = 3
    KLINE_TYPE_DAILY = 4
    KLINE_TYPE_WEEKLY = 5
    KLINE_TYPE_MONTHLY = 6
    KLINE_TYPE_EXHQ_1MIN = 7
    KLINE_TYPE_1MIN = 8
    KLINE_TYPE_RI_K = 9
    KLINE_TYPE_3MONTH = 10
    KLINE_TYPE_YEARLY = 11


    # ref : https://github.com/rainx/pytdx/issues/7
    # 分笔行情最多2000条（旧协议 0x0fb5 / 0x0fc5 之前的上限；
    # 新协议当日逐笔单页上限见 MAX_TICK_COUNT）
    MAX_TRANSACTION_COUNT = 2000
    # 新协议当日逐笔（0x0fc5）单页上限
    MAX_TICK_COUNT = 1800
    # 新协议集合竞价过程快照（0x056a）单页上限
    MAX_AUCTION_COUNT = 500
    # k线数据单次最多 700 条（2026-07 服务端协议更新后的上限，
    # 旧协议为 800）
    MAX_KLINE_COUNT = 700


    # 板块相关参数
    BLOCK_SZ = "block_zs.dat"
    BLOCK_FG = "block_fg.dat"
    BLOCK_GN = "block_gn.dat"
    BLOCK_DEFAULT = "block.dat"
