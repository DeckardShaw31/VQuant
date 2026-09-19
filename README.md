# VQuant: Vietnam Quantitative Trading & Backtesting Framework

[![PyPI Version](https://img.shields.io/pypi/v/vquant.svg)](https://pypi.org/project/vquant/)
[![Python Versions](https://img.shields.io/pypi/pyversions/vquant.svg)](https://pypi.org/project/vquant/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

VQuant la thu vien ma nguon mo chuyen sau ve Quantitative Trading, Factor Research va Backtesting duoc thiet ke rieng cho Thi truong Chung khoan Viet Nam (HOSE, HNX, UPCOM, Phai sinh VN30).

## 🌟 Tinh nang noi bat

1. Chu ky thanh toan T+2.5: Tu dong khoa co phieu mua ngay T den phien chieu T+2 moi cho phep ban.
2. Bay Tran / San: Mo phong chan thanh khoan khi co phieu roi san trang ben mua.
3. Thue ban 0.1% theo luat VN: Tu dong tru thue TNCN 0.1% tren tong doanh so ban va phi moi gioi.
4. Chien luoc Dinh luong mau: Minervini VCP (Trend Template), Turtle Breakout VN, Market Breadth.
5. Du lieu mau tich hop: Co san ham load_sample_data() de chay thu ngay khong can mang.

## 🚀 Cai dat (Installation)

`ash
pip install vquant
`

## ⚡ Bat dau nhanh (Quickstart)

`python
from vquant import VNBacktest, MinerviniVCPStrategy, TurtleBreakoutVN, load_sample_data

# 1. Tai du lieu mau co phieu Viet Nam
df = load_sample_data(periods=300)

# 2. Khoi tao Chien luoc (vi du: Minervini VCP)
strategy = MinerviniVCPStrategy(fast_ma=50, mid_ma=150, slow_ma=200, volume_mult=1.5, stop_loss_pct=0.07)

# 3. Khoi tao Engine Backtest chuan Viet Nam
bt = VNBacktest(initial_capital=100_000_000, settlement_days=2, tax_rate=0.001, commission_rate=0.0015)

# 4. Kiem thu chien luoc va in bao cao hieu qua
results = bt.run_strategy(df, strategy, symbol="VN30_SAMPLE")
print(results.summary())
`

## 📚 Danh muc Chien luoc

- **MinerviniVCPStrategy**: Bo loc Trend Template + Diem no bien dong VCP kem Volume Pocket Pivot.
- **TurtleBreakoutVN**: He thong pha vo kenh Donchian 20 phien cai tien cho T+2.5.
- **calculate_ma_breadth**: Chi bao Do rong thi truong (% co phieu tren MA20/MA50).

## 📄 Ban quyen (License)

Du an duoc phat hanh duoi giay phep ma nguon mo MIT License.
