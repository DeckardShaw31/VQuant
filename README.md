# VQuant: Vietnam Quantitative Trading & Backtesting Framework

[![PyPI Version](https://img.shields.io/pypi/v/vquant.svg)](https://pypi.org/project/vquant/)
[![Python Versions](https://img.shields.io/pypi/pyversions/vquant.svg)](https://pypi.org/project/vquant/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

VQuant la thu vien ma nguon mo chuyen sau ve Quantitative Trading, Factor Research va Backtesting duoc thiet ke rieng cho Thi truong Chung khoan Viet Nam (HOSE, HNX, UPCOM, Phai sinh VN30).

## 🌟 Tinh nang noi bat

1. **Chu ky thanh toan T+2.5**: Tu dong khoa co phieu mua ngay T den phien chieu T+2 moi cho phep ban.
2. **Thue ban 0.1% theo luat VN**: Tu dong tru thue TNCN 0.1% tren tong doanh so ban va phi moi gioi.
3. **Smart Money Flow**: Chien luoc bat song Khoi ngoai gom rong, Do rong thi truong (Breadth Thrust), San co phieu vuot dinh thoi dai (ATH).
4. **Chien luoc Trend & Momentum**: Minervini VCP (Trend Template), Turtle Breakout VN.
5. **Du lieu mau tich hop**: Co san load_sample_data() va load_sample_flow_data() de chay thu ngay khong can mang.

## 🚀 Cai dat (Installation)

```bash
pip install vquant
```

## ⚡ Bat dau nhanh (Quickstart)

```python
from vquant import VNBacktest, ForeignFlowStrategy, load_sample_flow_data

# 1. Tai du lieu nen kem dong tien khoi ngoai
df = load_sample_flow_data(periods=300)

# 2. Khoi tao chien luoc bat song khoi ngoai gom rong 3 phien lien tiep
strategy = ForeignFlowStrategy(min_streak=3, exit_streak=2, trend_ma=20, stop_loss_pct=0.07)

# 3. Kiem thu backtest chuan T+2.5 va thue 0.1%
bt = VNBacktest(initial_capital=100_000_000, settlement_days=2, tax_rate=0.001)
results = bt.run_strategy(df, strategy, symbol="FOREIGN_MOMENTUM")
print(results.summary())
```

## 📚 Danh muc Chien luoc & Factors

| Nhom | Module / Class | Mo ta |
| :--- | :--- | :--- |
| **Smart Money** | `ForeignFlowStrategy` | Bat song Khoi ngoai gom rong >= 3 phien kem gia tren MA20. |
| **Market Flow** | `BreadthThrustStrategy` | Tin hieu Bung no Do rong toan san tu <15% len >60% tren MA20. |
| **Momentum** | `AllTimeHighBreakoutStrategy` | San co phieu vuot dinh 52 tuan / lich su kem Volume no. |
| **Trend** | `MinerviniVCPStrategy` | Bo loc Trend Template + Diem no bien dong VCP kem Volume Pivot. |
| **Trend** | `TurtleBreakoutVN` | He thong pha vo kenh Donchian 20 phien cai tien cho T+2.5. |
| **Factors** | `calculate_foreign_streak` | Tinh so phien mua rong lien tiep cua NDT nuoc ngoai. |
| **Factors** | `calculate_cumulative_foreign_flow` | Tinh luy ke dong tien rong cua khoi ngoai. |
| **Factors** | `calculate_ma_breadth` | Tinh % so ma toan thi truong nam tren MA20/MA50. |

## 📄 Ban quyen (License)

Du an duoc phat hanh duoi giay phep ma nguon mo MIT License.
