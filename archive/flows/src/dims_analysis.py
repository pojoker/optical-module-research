#!/usr/bin/env python3
"""X1 维度挖掘：贸易方式 × 注册地纯聚合（不下判定）。

输入（只读，GBK）：
  flows/input/customs-85177950-2025-breakdown-usd.csv
  flows/input/customs-85177950-2026H1-breakdown-usd.csv

产出：
  flows/out/customs-trademode.csv  月份,贸易伙伴,贸易方式,出口量kg,金额USD
  flows/out/customs-province.csv   月份,注册地,贸易伙伴,出口量kg,金额USD

规则：伙伴取全月金额 top8 +「其他」合并；注册地全保留；金额写整数字符串。
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = ROOT / "flows" / "input"
OUT_DIR = ROOT / "flows" / "out"

INPUT_FILES = [
    INPUT_DIR / "customs-85177950-2025-breakdown-usd.csv",
    INPUT_DIR / "customs-85177950-2026H1-breakdown-usd.csv",
]
MONTHLY_CSV = OUT_DIR / "customs-monthly.csv"
TRADEMODE_OUT = OUT_DIR / "customs-trademode.csv"
PROVINCE_OUT = OUT_DIR / "customs-province.csv"

TOP_N = 8
OTHER = "其他"
TOL = 0.005  # 0.5%


def parse_num(s: str) -> float:
    s = (s or "").strip().replace(",", "")
    if not s or s == "?":
        return 0.0
    return float(s)


def load_breakdown(paths: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for path in paths:
        with path.open("r", encoding="gbk", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            # drop trailing empty header cell from customs export
            if header and header[-1] == "":
                header = header[:-1]
            for raw in reader:
                if raw and raw[-1] == "":
                    raw = raw[:-1]
                if len(raw) < 14:
                    continue
                rows.append(
                    {
                        "月份": raw[0].strip(),
                        "贸易伙伴": raw[4].strip(),
                        "贸易方式": raw[6].strip(),
                        "注册地": raw[8].strip(),
                        "出口量kg": parse_num(raw[9]),
                        "金额USD": parse_num(raw[13]),
                        "来源": path.name,
                    }
                )
    return rows


def month_top_partners(rows: list[dict], n: int = TOP_N) -> dict[str, set[str]]:
    """每月按金额合计取 top-n 伙伴名集合。"""
    by_mp: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for r in rows:
        by_mp[r["月份"]][r["贸易伙伴"]] += r["金额USD"]
    out: dict[str, set[str]] = {}
    for month, partners in by_mp.items():
        ranked = sorted(partners.items(), key=lambda x: (-x[1], x[0]))
        out[month] = {name for name, _ in ranked[:n]}
    return out


def fmt_int(x: float) -> str:
    # 海关数量/金额为整数口径；浮点累加后四舍五入到整数再写字符串
    return str(int(round(x)))


def build_trademode(rows: list[dict], top: dict[str, set[str]]) -> list[dict]:
    agg: dict[tuple[str, str, str], list[float]] = defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        partner = r["贸易伙伴"] if r["贸易伙伴"] in top[r["月份"]] else OTHER
        key = (r["月份"], partner, r["贸易方式"])
        agg[key][0] += r["出口量kg"]
        agg[key][1] += r["金额USD"]
    out = []
    for (month, partner, mode), (kg, usd) in agg.items():
        out.append(
            {
                "月份": month,
                "贸易伙伴": partner,
                "贸易方式": mode,
                "出口量kg": fmt_int(kg),
                "金额USD": fmt_int(usd),
                "_kg": kg,
                "_usd": usd,
            }
        )
    # 排序：月 → 伙伴金额降序（其他垫底）→ 方式金额降序
    partner_usd: dict[tuple[str, str], float] = defaultdict(float)
    for row in out:
        partner_usd[(row["月份"], row["贸易伙伴"])] += row["_usd"]

    def sort_key(row: dict):
        p = row["贸易伙伴"]
        rank = 10**18 if p == OTHER else -partner_usd[(row["月份"], p)]
        return (row["月份"], rank, p, -row["_usd"], row["贸易方式"])

    out.sort(key=sort_key)
    return out


def build_province(rows: list[dict], top: dict[str, set[str]]) -> list[dict]:
    agg: dict[tuple[str, str, str], list[float]] = defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        partner = r["贸易伙伴"] if r["贸易伙伴"] in top[r["月份"]] else OTHER
        key = (r["月份"], r["注册地"], partner)
        agg[key][0] += r["出口量kg"]
        agg[key][1] += r["金额USD"]
    out = []
    for (month, province, partner), (kg, usd) in agg.items():
        out.append(
            {
                "月份": month,
                "注册地": province,
                "贸易伙伴": partner,
                "出口量kg": fmt_int(kg),
                "金额USD": fmt_int(usd),
                "_kg": kg,
                "_usd": usd,
            }
        )
    partner_usd: dict[tuple[str, str], float] = defaultdict(float)
    for row in out:
        partner_usd[(row["月份"], row["贸易伙伴"])] += row["_usd"]

    def sort_key(row: dict):
        p = row["贸易伙伴"]
        rank = 10**18 if p == OTHER else -partner_usd[(row["月份"], p)]
        return (row["月份"], row["注册地"], rank, p)

    out.sort(key=sort_key)
    return out


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row[k] for k in fieldnames})


def load_monthly_ref() -> dict[str, tuple[float, float]]:
    """月份 -> (kg, usd) from customs-monthly.csv (USD rows only)."""
    ref: dict[str, tuple[float, float]] = {}
    with MONTHLY_CSV.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("币种") != "USD":
                continue
            ref[row["月份"]] = (float(row["出口量kg"]), float(row["金额"]))
    return ref


def month_totals(rows: list[dict]) -> dict[str, tuple[float, float]]:
    tot: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        tot[r["月份"]][0] += r["_kg"]
        tot[r["月份"]][1] += r["_usd"]
    return {m: (v[0], v[1]) for m, v in tot.items()}


def print_malaysia_share(rows: list[dict]) -> None:
    """马来西亚按贸易方式的月度占比表（打印，不落盘）。"""
    by_mm: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    month_tot: dict[str, float] = defaultdict(float)
    for r in rows:
        if r["贸易伙伴"] != "马来西亚":
            continue
        by_mm[r["月份"]][r["贸易方式"]] += r["_usd"]
        month_tot[r["月份"]] += r["_usd"]
    months = sorted(month_tot)
    modes = sorted({m for d in by_mm.values() for m in d})
    print("\n===== ① 马来西亚按贸易方式的月度占比（金额USD） =====")
    header = ["月份", "合计USD"] + [f"{m}%" for m in modes] + modes
    # compact printable table: month | total | mode: share% (amount)
    print(f"{'月份':<8}{'合计USD':>14}  " + "  ".join(f"{m}" for m in modes))
    for month in months:
        total = month_tot[month]
        cells = []
        for mode in modes:
            amt = by_mm[month].get(mode, 0.0)
            pct = (amt / total * 100.0) if total else 0.0
            cells.append(f"{pct:5.1f}%({fmt_int(amt)})")
        print(f"{month:<8}{fmt_int(total):>14}  " + "  ".join(f"{c:>22}" for c in cells))
    # also a share-only matrix for readability
    print("\n占比矩阵（% of 当月马来西亚合计）：")
    print(f"{'月份':<8}" + "".join(f"{m:>28}" for m in modes))
    for month in months:
        total = month_tot[month]
        print(
            f"{month:<8}"
            + "".join(
                f"{(by_mm[month].get(m, 0.0) / total * 100.0) if total else 0.0:27.2f}%"
                for m in modes
            )
        )


def reconcile(label: str, totals: dict[str, tuple[float, float]], ref: dict[str, tuple[float, float]]) -> None:
    print(f"\n===== ② {label} vs customs-monthly 对账（容差<{TOL*100}%） =====")
    print(f"{'月份':<8}{'表合计USD':>14}{'monthlyUSD':>14}{'ΔUSD%':>10}{'表合计kg':>12}{'monthlykg':>12}{'Δkg%':>10}  结果")
    months = sorted(totals)
    fails = 0
    for m in months:
        kg, usd = totals[m]
        if m not in ref:
            print(f"{m:<8} SKIP — customs-monthly 无此月")
            fails += 1
            continue
        rkg, rusd = ref[m]
        d_usd = abs(usd - rusd) / rusd if rusd else (0.0 if usd == 0 else 1.0)
        d_kg = abs(kg - rkg) / rkg if rkg else (0.0 if kg == 0 else 1.0)
        ok = d_usd < TOL and d_kg < TOL
        if not ok:
            fails += 1
        print(
            f"{m:<8}{fmt_int(usd):>14}{fmt_int(rusd):>14}{d_usd*100:9.4f}%"
            f"{fmt_int(kg):>12}{fmt_int(rkg):>12}{d_kg*100:9.4f}%  {'PASS' if ok else 'FAIL'}"
        )
    print(f"对账结果: {'ALL PASS' if fails == 0 else f'{fails} FAIL'}")


def main() -> None:
    rows = load_breakdown(INPUT_FILES)
    top = month_top_partners(rows, TOP_N)

    trademode = build_trademode(rows, top)
    province = build_province(rows, top)

    write_csv(
        TRADEMODE_OUT,
        ["月份", "贸易伙伴", "贸易方式", "出口量kg", "金额USD"],
        trademode,
    )
    write_csv(
        PROVINCE_OUT,
        ["月份", "注册地", "贸易伙伴", "出口量kg", "金额USD"],
        province,
    )

    print_malaysia_share(trademode)

    ref = load_monthly_ref()
    reconcile("customs-trademode", month_totals(trademode), ref)
    reconcile("customs-province", month_totals(province), ref)

    print("\n===== ③ 行数 =====")
    print(f"输入原始行数: {len(rows)}")
    print(f"customs-trademode.csv 行数: {len(trademode)}")
    print(f"customs-province.csv 行数: {len(province)}")
    print(f"写出: {TRADEMODE_OUT}")
    print(f"写出: {PROVINCE_OUT}")

    # top8 sanity per month
    print("\n每月 top8 伙伴:")
    for m in sorted(top):
        names = sorted(top[m])
        print(f"  {m}: {', '.join(names)}")


if __name__ == "__main__":
    main()
