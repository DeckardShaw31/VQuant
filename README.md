# VQuant: Vietnam Quantitative Trading & Backtesting Framework

[![PyPI Version](https://img.shields.io/pypi/v/vquant.svg)](https://pypi.org/project/vquant/)
[![Python Versions](https://img.shields.io/pypi/pyversions/vquant.svg)](https://pypi.org/project/vquant/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**VQuant** là thư viện mã nguồn mở chuyên sâu về **Quantitative Trading, Factor Research và Backtesting** được thiết kế riêng cho **Thị trường Chứng khoán Việt Nam (HOSE, HNX, UPCOM, Phái sinh VN30)**.

---

## 🌟 Tại sao lại cần VQuant?

Hầu hết các thư viện backtest quốc tế (`backtrader`, `vectorbt`, `zipline`) đều tạo ra **ảo tưởng lợi nhuận** khi áp dụng tại Việt Nam vì không hỗ trợ các quy tắc vi cấu trúc đặc thù:

1. **Chu kỳ thanh toán T+2.5**: Cổ phiếu mua ngày $T$ chỉ được phép bán vào phiên chiều $T+2$. VQuant tự động khóa số lượng cổ phiếu đang trên đường về (`pending_settlement`).
2. **Bẫy Trần / Sàn & Hiện tượng "Múa bên trăng"**: Khi cổ phiếu rơi sàn và mất thanh khoản mua, VQuant phạt lệnh và ngăn chặn việc khớp lệnh bán giá sàn ảo tưởng.
3. **Thuế bán 0.1% theo luật Việt Nam**: Tự động trừ thuế TNCN 0.1% trên tổng doanh số bán (bất kể lãi hay lỗ) cùng phí môi giới 2 chiều và lãi vay margin.
4. **Phái sinh VN30F1M**: Hỗ trợ giao dịch T+0, Long/Short 2 chiều, tính toán ký quỹ VSD (IM/VM) và đo lường Basis Spread.

---

## 🚀 Cài đặt (Installation)

```bash
pip install vquant
```

---

## ⚡ Bắt đầu nhanh (Quickstart)

```python
import pandas as pd
from vquant import VNBacktest

# 1. Chuẩn bị dữ liệu OHLCV (từ CSV, vnstock hoặc bất kỳ nguồn nào)
# DataFrame yêu cầu các cột: ['date', 'open', 'high', 'low', 'close', 'volume']
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=100, freq='B'),
    'open': [25.0 + i * 0.1 for i in range(100)],
    'high': [25.5 + i * 0.1 for i in range(100)],
    'low': [24.8 + i * 0.1 for i in range(100)],
    'close': [25.2 + i * 0.1 for i in range(100)],
    'volume': [1_000_000 for _ in range(100)],
})

# 2. Tạo tín hiệu giao dịch (1: Mua, -1: Bán, 0: Giữ nguyên)
signals = pd.Series(0, index=df.index)
signals.iloc[10] = 1   # Mua vào phiên thứ 10
signals.iloc[11] = -1  # Cố gắng bán vào phiên thứ 11 -> VQuant sẽ chặn do chưa đủ T+2.5!
signals.iloc[13] = -1  # Bán hợp lệ vào phiên chiều T+2

# 3. Khởi tạo Engine Backtest chuẩn Việt Nam
bt = VNBacktest(
    initial_capital=100_000_000, # 100 triệu VNĐ
    settlement_days=2,           # Quy tắc T+2.5
    tax_rate=0.001,              # Thuế bán 0.1%
    commission_rate=0.0015       # Phí môi giới 0.15%
)

# 4. Chạy kiểm thử chiến lược
results = bt.run(df, signals)
print(results.summary())
```

---

## 🗺️ Lộ trình phát triển (Roadmap)

- [x] **v0.0.1**: Khởi tạo Core Engine, mô phỏng chu kỳ thanh toán T+2.5 và thuế bán 0.1%.
- [ ] **v0.1.0**: Bổ sung bẫy thanh khoản Trần/Sàn (Floor lockout) và bước giá quy định (Tick sizes).
- [ ] **v0.2.0**: Thư viện nhân tố Alpha: Dòng tiền Khối ngoại, Tự doanh CTCK, Độ rộng thị trường (Market Breadth).
- [ ] **v0.3.0**: Module Phái sinh VN30F1M: Backtest T+0, Basis Spread Arbitrage, Hedging.
- [ ] **v0.4.0**: Execution Adapter: Tích hợp DNSE Entrade X Open API để đặt lệnh tự động.

---

## 📄 Bản quyền (License)

Dự án được phát hành dưới giấy phép mã nguồn mở [MIT License](LICENSE).
