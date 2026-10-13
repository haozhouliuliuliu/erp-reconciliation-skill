#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成完全虚构的对账示例数据。

**本脚本产出的每一个名称、料号、单价、数量都是编造的**，与任何真实公司、
客户或业务无关。它只用来演示数据结构与业务规则。

运行：
    python examples/make_sample_data.py

产出：
    examples/sample-reconciliation-data.xlsx
        ├── 产品基础资料   料号 / 规格 / 名称 / 单位 / 单价（未税）
        ├── 送货单明细     单号 / 行号 / 单据日期 / 料号 / 数量
        └── 说明           数据生成规则与刻意植入的边界情况

需要 openpyxl（pip install openpyxl）。
"""
from __future__ import annotations

import pathlib
import random

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "sample-reconciliation-data.xlsx"

SEED = 20260801          # 固定种子：每次生成结果一致，便于核对
MONTH = "2026-08"
COMPANY = "示例精密制造有限公司（虚构）"

#: 虚构产品主数据 —— (料号, 规格, 名称, 单位, 单价未税)
#: 注意第 5 项单价为 None：用来演示「缺单价 → 填 0 + 进清单」规则
PRODUCTS = [
    ("DEMO-1001", "SPEC-A-0001", "左侧安装支架（示例）", "件", 1.20),
    ("DEMO-1002", "SPEC-A-0002", "右侧安装支架（示例）", "件", 1.20),
    ("DEMO-1003", "SPEC-B-0011", "中部连接板（示例）",   "件", 2.45),
    ("DEMO-1004", "SPEC-B-0012", "加强筋（示例）",       "件", 0.88),
    ("DEMO-1005", "SPEC-C-0101", "定位销（示例）",       "个", None),
    ("DEMO-1006", "SPEC-C-0102", "缓冲垫（示例）",       "个", 0.35),
]


def build_records() -> list[tuple[str, int, str, str, int]]:
    """构造虚构的送货单明细。

    刻意植入的边界情况（见「说明」工作表）：
      A. 同一单号 + 同一行号出现两次   -> R1 去重后应只留一条
      B. 同一天 + 同一料号出现两笔     -> R2 应求和，不可当作重复
      C. 同一天 + 同料号 + 同数量的两笔 -> 恰恰是最容易误删的情况
      D. 某个料号单价缺失              -> R6 金额填 0 并进清单
    """
    rng = random.Random(SEED)
    rows: list[tuple[str, int, str, str, int]] = []
    doc_seq = 1

    for day in (3, 5, 5, 11, 11, 11, 18, 24, 24):
        d = f"{MONTH}-{day:02d}"

        # B / C：同一天对同一料号的两笔（数量故意相同，最易被误判为重复）
        if day in (5, 11):
            code = "DEMO-1003"
            doc = f"SH-{MONTH.replace('-', '')}-{doc_seq:04d}"
            rows.append((doc, 1, d, code, 400))
            rows.append((doc, 2, d, code, 400))
            doc_seq += 1

        # A：重复抓取的同单同行（真正的重复）
        doc = f"SH-{MONTH.replace('-', '')}-{doc_seq:04d}"
        rows.append((doc, 1, d, "DEMO-1001", rng.choice([500, 600, 750])))
        if day == 11:
            rows.append((doc, 1, d, "DEMO-1001", 600))   # ← A：完全重复
        doc_seq += 1

        # 常规记录
        doc = f"SH-{MONTH.replace('-', '')}-{doc_seq:04d}"
        rows.append((doc, 1, d, "DEMO-1002", rng.choice([300, 450])))
        rows.append((doc, 2, d, "DEMO-1004", rng.choice([1000, 1200])))
        doc_seq += 1
        if day % 11 == 0:
            doc = f"SH-{MONTH.replace('-', '')}-{doc_seq:04d}"
            rows.append((doc, 1, d, "DEMO-1005", 250))   # ← D：该料号无单价
            doc_seq += 1

    return rows


HEAD_FILL = PatternFill("solid", fgColor="DCE6F1")
HEAD_FONT = Font(bold=True, size=11)
THIN = Side(style="thin", color="B0B7BF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def style_header(ws, ncols: int) -> None:
    for c in range(1, ncols + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill = HEAD_FILL
        cell.font = HEAD_FONT
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center")


def main() -> int:
    wb = Workbook()

    # ---- 产品基础资料 ----
    ws = wb.active
    ws.title = "产品基础资料"
    ws.append(["料号", "规格型号", "名称", "单位", "单价（未税）", "备注"])
    for code, spec, name, unit, price in PRODUCTS:
        note = "★ 单价缺失（演示 R6：填0并进清单）" if price is None else ""
        ws.append([code, spec, name, unit, price, note])
    style_header(ws, 6)
    for col, w in zip("ABCDEF", (14, 16, 26, 8, 14, 30)):
        ws.column_dimensions[col].width = w

    # ---- 送货单明细 ----
    ws2 = wb.create_sheet("送货单明细")
    ws2.append(["单据编号", "行号", "单据日期", "料号", "数量"])
    for doc, line, d, code, qty in build_records():
        ws2.append([doc, line, d, code, qty])
    style_header(ws2, 5)
    for col, w in zip("ABCDE", (22, 8, 14, 14, 10)):
        ws2.column_dimensions[col].width = w

    # ---- 说明 ----
    ws3 = wb.create_sheet("说明")
    ws3.append(["项", "内容"])
    notes = [
        ("数据性质", "★ 全部虚构。名称、料号、单价、数量均为编造，与任何真实公司或业务无关。"),
        ("生成方式", "由 examples/make_sample_data.py 生成，随机种子固定，可复现。"),
        ("产品主数据", f"{len(PRODUCTS)} 个虚构料号，其中一个（DEMO-1005）刻意不给单价。"),
        ("送货单明细", f"{len(build_records())} 行虚构记录（含刻意植入的重复行）。"),
        ("刻意植入 A", "同一「单据编号+行号」出现两次 —— 用于验证 R1 去重键。"),
        ("刻意植入 B", "同一天对同一料号的两笔 —— 用于验证 R2 按「单据日期+料号」求和。"),
        ("刻意植入 C", "同一天、同料号、同数量的两笔 —— 最容易被误判为重复的情况，必须保留。"),
        ("刻意植入 D", "DEMO-1005 无单价 —— 用于验证 R6「缺单价填 0 并进清单」。"),
        ("不可用于", "不得据此推断任何真实业务规模、单价水平或对账结果。"),
    ]
    for k, v in notes:
        ws3.append([k, v])
    style_header(ws3, 2)
    ws3.column_dimensions["A"].width = 16
    ws3.column_dimensions["B"].width = 96
    for r in range(2, ws3.max_row + 1):
        ws3.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical="top")

    wb.save(OUT)
    print(f"已生成: {OUT}")
    print(f"  产品基础资料  {len(PRODUCTS)} 行")
    print(f"  送货单明细    {len(build_records())} 行")
    print(f"  说明          {len(notes)} 条")
    print("\n提示：全部数据均为虚构，仅供演示。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
