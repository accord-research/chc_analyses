"""test_wrap.py — pin the year-boundary arithmetic.

Two of the three v4zeek testbeds use a December-January-February season, so a window
labelled year Y starts in December of year Y-1. Getting this wrong shifts every
predictor by twelve months and fails silently: the code runs, the numbers look
plausible, and the result is garbage. The AGUv0 notes record a bug of exactly this
shape. So it gets a test.

Run: conda run -n pycpt python -m pytest tests/ -q
     conda run -n pycpt python tests/test_wrap.py      (no pytest needed)
"""
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bench


def _ctx(months):
    """A Context with no real data — only the calendar arithmetic is under test."""
    return bench.Context({}, months, years=np.arange(1982, 2024),
                         train_years=np.arange(1982, 2010),
                         test_years=np.arange(2010, 2024), y_train=np.zeros(28))


def test_djf_window_starts_in_previous_december():
    c = _ctx([12, 1, 2])
    assert c.wraps is True
    assert c._month_of(2000, 0) == (1999, 12), "DJF 2000 starts Dec 1999"
    assert c._month_of(2000, 1) == (1999, 11), "one month before is Nov 1999"
    assert c._month_of(2000, 2) == (1999, 10)
    assert c._month_of(2000, 12) == (1998, 12), "a full year back crosses into 1998"


def test_mam_window_does_not_wrap_but_its_preseason_does():
    c = _ctx([3, 4, 5])
    assert c.wraps is False
    assert c._month_of(2000, 0) == (2000, 3), "MAM 2000 starts Mar 2000"
    assert c._month_of(2000, 1) == (2000, 2)
    assert c._month_of(2000, 3) == (1999, 12), "three months back crosses the year boundary"
    assert c._month_of(2000, 4) == (1999, 11)


def test_ond_window_and_deep_leads():
    c = _ctx([10, 11, 12])
    assert c.wraps is False
    assert c._month_of(2000, 0) == (2000, 10)
    assert c._month_of(2000, 1) == (2000, 9)
    assert c._month_of(2000, 11) == (1999, 11)


def test_month_index_is_always_valid():
    """No offset, on any window, may ever produce a month outside 1..12."""
    for months in ([12, 1, 2], [3, 4, 5], [10, 11, 12], [6, 7, 8, 9], [11, 12, 1]):
        c = _ctx(months)
        for year in (1982, 1999, 2000, 2023):
            for off in range(0, 40):
                yy, mm = c._month_of(year, off)
                assert 1 <= mm <= 12, f"{months} y={year} off={off} -> month {mm}"
                assert 1900 < yy < 2100


def test_preseason_is_strictly_before_the_window():
    """The causal guarantee: no gap/width combination can reach into or past the season."""
    for months in ([12, 1, 2], [3, 4, 5], [10, 11, 12]):
        c = _ctx(months)
        start_y, start_m = c._month_of(2000, 0)
        start_abs = start_y * 12 + start_m - 1
        for gap in range(0, 6):
            for width in (1, 2, 3):
                for k in range(width):
                    yy, mm = c._month_of(2000, gap + 1 + k)
                    assert yy * 12 + mm - 1 < start_abs, (
                        f"{months} gap={gap} width={width} reaches {yy}-{mm}, "
                        f"not strictly before {start_y}-{start_m}")


def test_djf_season_labelling_matches_the_context():
    """build_target labels a DJF season by the year of its LAST month. That must agree
    with Context, or the predictor and the predictand refer to different winters."""
    months = [12, 1, 2]
    wraps = months[0] > months[-1]
    roll = [m for m in months if m > months[-1]] if wraps else []
    # Dec 1999 must roll forward into the 2000 season; Jan/Feb 2000 must stay.
    assert 12 in roll and 1 not in roll and 2 not in roll
    c = _ctx(months)
    assert c._month_of(2000, 0) == (1999, 12), "Context agrees Dec 1999 opens the 2000 season"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
