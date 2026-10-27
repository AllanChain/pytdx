# coding=utf-8

from pytdx.parser.get_security_bars import GetSecurityBarsCmd

"""
指数 K 线。

2026-07 之后指数（999999 / 399xxx 等）和个股使用同一套新帧格式，唯一差别
只是 market/code 不同，因此直接复用 GetSecurityBarsCmd。

注意：新协议响应里没有旧的涨跌家数字段，返回结果中的 up_count / down_count
恒为 None（保留字段是为了兼容旧版本的返回结构）。
"""


class GetIndexBarsCmd(GetSecurityBarsCmd):

    _INCLUDE_INDEX_EXTRA_FIELDS = True
