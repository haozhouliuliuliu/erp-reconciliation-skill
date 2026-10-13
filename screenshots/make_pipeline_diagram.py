#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""绘制脱敏的流程示意图。

**不是真实界面截图** —— 真实截图会暴露客户 ERP 的界面与数据。
这张图只用文字与方框表达流程与「人工 / 程序」的边界。

输出: screenshots/pipeline.png
"""
from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw, ImageFont

OUT = pathlib.Path(__file__).resolve().parent.parent / "screenshots" / "pipeline.png"
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

BG = (247, 248, 250)
CARD = (255, 255, 255)
BORDER = (223, 226, 231)
TEXT = (28, 32, 38)
MUTED = (108, 116, 128)
AUTO = (37, 99, 235)
AUTO_BG = (235, 242, 254)
AUTO_BD = (191, 213, 250)
HUMAN = (21, 128, 61)
HUMAN_BG = (232, 245, 233)
HUMAN_BD = (183, 222, 187)
LINE = (170, 178, 190)

_fc: dict = {}


def font(size: int, bold: bool = False):
    key = (size, bold)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size, index=0)
    return _fc[key]


def tw(d, s, f):
    return d.textlength(s, font=f)


def box(d, x, y, w, h, title, lines, *, human=False, r=10):
    fill = HUMAN_BG if human else AUTO_BG
    bd = HUMAN_BD if human else AUTO_BD
    d.rounded_rectangle([x, y, x + w, y + h], r, fill=fill, outline=bd, width=2)
    color = HUMAN if human else AUTO
    d.text((x + 14, y + 11), title, font=font(15, True), fill=color)
    yy = y + 37
    for ln in lines:
        d.text((x + 14, yy), ln, font=font(12), fill=TEXT)
        yy += 19


def arrow(d, x1, y1, x2, y2, color=LINE):
    d.line([x1, y1, x2, y2], fill=color, width=2)
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    L, sp = 9, math.radians(24)
    for s in (+1, -1):
        d.line([x2, y2, x2 - L * math.cos(ang + s * sp), y2 - L * math.sin(ang + s * sp)],
               fill=color, width=2)


def main() -> int:
    W, H = 1420, 880
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # 标题
    d.text((48, 34), "供应商对账自动化 —— 流程与人工边界", font=font(27, True), fill=TEXT)
    d.text((48, 74), "示例流程说明。图中数据为虚构；绘制而非截图，避免暴露真实界面与业务数据。",
           font=font(14), fill=MUTED)
    d.line([48, 108, W - 48, 108], fill=BORDER, width=2)

    # 图例
    lx = 48
    for label, human in (("由程序完成", False), ("由人完成", True)):
        d.rounded_rectangle([lx, 124, lx + 16, 140], 4,
                            fill=HUMAN_BG if human else AUTO_BG,
                            outline=HUMAN_BD if human else AUTO_BD, width=2)
        d.text((lx + 24, 124), label, font=font(13), fill=MUTED)
        lx += 130
    d.text((lx + 10, 124), "—— 人工介入点是有意设计的停顿，不是功能缺失",
           font=font(13), fill=MUTED)

    # ---- 第一行：采集阶段 ----
    d.text((48, 168), "阶段一　采集（只读）", font=font(17, True), fill=TEXT)
    y = 200
    w, h, gap = 232, 118, 26
    x = 48
    box(d, x, y, w, h, "① 环境自检", ["Playwright 驱动", "系统 Edge", "配置 / 资料目录"])
    arrow(d, x + w, y + h // 2, x + w + gap, y + h // 2)
    x += w + gap

    box(d, x, y, w, h, "② 选择账号", ["弹窗选择", "点 X 取消则退出"], human=True)
    arrow(d, x + w, y + h // 2, x + w + gap, y + h // 2)
    x += w + gap

    box(d, x, y, w, h, "③ 打开浏览器", ["持久化 Profile", "免重复登录"])
    arrow(d, x + w, y + h // 2, x + w + gap, y + h // 2)
    x += w + gap

    box(d, x, y, w, h, "④ 人工登录", ["程序不接触账号密码", "登录后备份登录状态"], human=True)
    arrow(d, x + w, y + h // 2, x + w + gap, y + h // 2)
    x += w + gap

    box(d, x, y, w, h, "⑤ 导航与查询", ["菜单树展开", "点可见的「查询」"])

    # ---- 第二行：翻页 + 输出 ----
    d.text((48, 356), "阶段二　翻页读取与去重", font=font(17, True), fill=TEXT)
    y2 = 388
    x = 48
    box(d, x, y2, w + 40, h, "⑥ 逐页读取", ["读到早于目标月份即停", "最大页数上限兜底", "记录终止原因"])
    arrow(d, x + w + 40, y2 + h // 2, x + w + 40 + gap, y2 + h // 2)
    x += w + 40 + gap

    box(d, x, y2, w + 40, h, "⑦ 去重（单号 + 行号）",
        ["同单同行 → 去重", "同单不同行 → 保留", "报告写明重复行数"])
    arrow(d, x + w + 40, y2 + h // 2, x + w + 40 + gap, y2 + h // 2)
    x += w + 40 + gap

    box(d, x, y2, w + 40, h, "⑧ 输出中间产物", ["当前月份记录.csv", "采集报告 .json"])
    arrow(d, x + w + 40, y2 + h // 2, x + w + 40 + gap, y2 + h // 2)
    x += w + 40 + gap

    box(d, x, y2, w + 30, h, "⑨ 生成对账单", ["母版驱动 + 公式", "动态日期列", "料号匹配取单价"])

    # 分隔线
    d.line([48, 548, W - 48, 548], fill=BORDER, width=2)

    # ---- 第三行：质检与人工审核 ----
    d.text((48, 570), "阶段三　质检与人工审核", font=font(17, True), fill=TEXT)
    y3 = 602
    x = 48
    box(d, x, y3, 300, h, "⑩ 质检（fatal 一票否决）",
        ["数量守恒", "料号全覆盖", "来源行数恒等式"])
    arrow(d, x + 300, y3 + h // 2, x + 300 + gap, y3 + h // 2)
    x += 300 + gap

    box(d, x, y3, 330, h, "11　人工审核", [
        "补缺单价料号 → 重跑",
        "判断同物异名（程序只提示）",
        "解释非 fatal 偏差",
    ], human=True)
    arrow(d, x + 330, y3 + h // 2, x + 330 + gap, y3 + h // 2)
    x += 330 + gap

    box(d, x, y3, 300, h, "12　交付前复核", [
        "人看一遍再交客户",
    ], human=True)
    arrow(d, x + 300, y3 + h // 2, x + 300 + gap, y3 + h // 2)
    x += 300 + gap

    box(d, x, y3, 258, h, "×　明确失败的情形", [
        "料号不在产品资料 → FAIL",
        "不允许用相似料号顶替",
    ])

    # 底部注记
    d.text((48, H - 66),
           "关键设计：程序负责「搬数与算数」，人负责「判断与负责」。"
           "料号对不上宁可整体失败，也不猜。",
           font=font(13, True), fill=TEXT)
    d.text((48, H - 42),
           "来源：对打包产物的字节码分析 + 源码交叉验证（详见 docs/analysis-method.md）。"
           "本图不含任何真实客户、系统或业务信息。",
           font=font(12), fill=MUTED)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(f"已生成: {OUT}  ({img.width}x{img.height}, {OUT.stat().st_size/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
