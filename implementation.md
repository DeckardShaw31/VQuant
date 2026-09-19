# VQUANT IMPLEMENTATION ARCHITECTURE & UPGRADE ROADMAP 🗺️

Tài liệu này đóng vai trò là kim chỉ nam kiến trúc (Architectural Blueprint) và lộ trình nâng cấp chi tiết cho thư viện **VQuant**. Mọi tính năng từ phiên bản v0.2.0 đến v1.0.0 đều phải tuân thủ nghiêm ngặt các tiêu chuẩn thiết kế, hợp đồng dữ liệu (Data Contracts), và quy trình kiểm thử tại đây trước khi viết mã nguồn.

---

## 🎯 Triết lý Thiết kế (Core Philosophy)

1. **Vietnam-First Microstructure**: Luôn đặt đặc thù vi cấu trúc của TTCK Việt Nam (T+2.5, thuế bán 0.1%, biên độ trần/sàn, phái sinh VN30) làm trọng tâm. Không sao chép máy móc các thư viện quốc tế.
2. **Provider Agnostic (Không phụ thuộc nguồn cào)**: Tách biệt hoàn toàn giữa **Logic Quant** và **Nguồn Dữ liệu**. VQuant là một computation/backtest engine, dữ liệu có thể đến từ nstock, CSV, Parquet, hoặc API của CTCK.
3. **Vectorized & Event-Driven Hybrid**: Tính toán chỉ báo và tín hiệu theo cơ chế vector hóa (Pandas/Numpy) để đạt tốc độ cao; mô phỏng khớp lệnh, quản trị vị thế và quản trị rủi ro theo cơ chế hướng sự kiện (Event-driven) để đảm bảo tính chân thực của thị trường.
4. **Zero-Hallucination & Type Safety**: Mọi hàm, class đều có type hints đầy đủ, kiểm soát dữ liệu đầu vào nghiêm ngặt để tránh lỗi runtime khi chạy chiến lược tự động.

---

## 🏗️ Cấu trúc Module Tổng thể (Target Architecture v1.0.0)

`	ext
vquant/
├── __init__.py
├── __version__.py
├── backtest/               # Engine kiểm thử chiến lược
│   ├── __init__.py
│   ├── engine.py           # VNBacktest (Cơ sở T+2.5, Thuế 0.1%, Lô 100)
│   ├── derivatives.py      # VN30FBacktest (Phái sinh T+0, Long/Short, Ký quỹ VSD)
│   ├── limits.py           # Bộ lọc bẫy Trần/Sàn ('múa bên trăng') & Bước giá
│   └── metrics.py          # Sharpe, Sortino, Max Drawdown, Win Rate, Profit Factor
├── strategies/             # Thư viện Chiến lược Định lượng
│   ├── __init__.py
│   ├── base.py             # BaseStrategy & Signal Interface
│   ├── trend.py            # Minervini VCP, Turtle Breakout VN, SuperTrend
│   ├── flow.py             # Foreign Flow Momentum, Breadth Thrust, All-Time-High
│   ├── mean_reversion.py   # RSI Divergence, Bollinger Squeeze, Pairs Trading
│   └── derivatives.py      # Basis Arbitrage, Intraday ORB, Beta Hedging
├── factors/                # Thư viện Tính toán Nhân tố Alpha
│   ├── __init__.py
│   ├── market_breadth.py   # % cổ phiếu trên MA20/MA50/MA200 toàn sàn
│   ├── smart_money.py      # Dòng tiền Khối ngoại, Tự doanh CTCK
│   └── analytics.py        # Information Coefficient (IC), Factor Autocorrelation
├── risk/                   # Quản trị Rủi ro & An toàn Đòn bẩy
│   ├── __init__.py
│   ├── margin.py           # MarginGuardian: Tỷ lệ RTT, Cảnh báo Call Margin/Force Sell
│   └── circuit_breaker.py  # Ngắt mạch danh mục khi chạm ngưỡng Max Drawdown
├── portfolio/              # Phân bổ Vốn & Tối ưu Danh mục
│   ├── __init__.py
│   ├── sizing.py           # Kelly Criterion, Fixed Risk 2% NAV, Equal Volatility
│   └── optimizer.py        # Risk Parity, Mean-Variance Optimization
├── data/                   # Adapters kết nối nguồn dữ liệu
│   ├── __init__.py
│   ├── base.py             # BaseDataAdapter
│   ├── vnstock_adapter.py  # Cầu nối dữ liệu vnstock / vnstock_data
│   └── file_adapter.py     # Đọc Parquet, CSV, DuckDB
├── execution/              # Giao dịch Thực chiến & Bot đặt lệnh
│   ├── __init__.py
│   ├── paper.py            # PaperBroker: Môi trường giao dịch tiền ảo Real-time
│   ├── dnse.py             # DNSE Entrade X Open API Connector
│   └── notifier.py         # Bắn thông báo Telegram / Discord Webhook
└── datasets/               # Dữ liệu mẫu tích hợp sẵn
    ├── __init__.py
    └── sample.py           # load_sample_data() nến ngày VN30/VNINDEX
`

---

## 🗺️ Lộ trình Nâng cấp Chi tiết (Roadmap by Milestones)

### 📌 Milestone 1: v0.1.0 (Đã hoàn thành ✅)
* [x] Đăng ký và xuất bản chính thức gói quant lên PyPI.
* [x] Đồng bộ kho mã nguồn GitHub: [DeckardShaw31/VQuant](https://github.com/DeckardShaw31/VQuant).
* [x] Xây dựng VNBacktest cốt lõi: T+2.5 settlement delay, 0.1% thuế bán TNCN, 0.15% phí môi giới.
* [x] Chuẩn hóa kiến trúc BaseStrategy và Signal.
* [x] Triển khai chiến lược MinerviniVCPStrategy và TurtleBreakoutVN.
* [x] Tích hợp bộ sinh dữ liệu mẫu load_sample_data().
* [x] Bộ test tự động pytest (5/5 PASSED).

---

### 📌 Milestone 2: v0.2.0 — Smart Money Flow & Factor Engine (Kế hoạch Tiếp theo)
**Mục tiêu**: Bổ sung hệ thống định lượng dòng tiền tạo lập (Khối ngoại, Tự doanh) và độ rộng thị trường.

1. **Module quant.strategies.flow**:
   * ForeignFlowStrategy:
     * Điều kiện: Khối ngoại mua ròng liên tục 3-5 phiên VÀ giá trị chiếm >15% tổng thanh khoản VÀ giá nằm trên MA20.
     * Thoát hàng: Khi khối ngoại bán ròng 2 phiên liên tục hoặc gãy MA20.
   * BreadthThrustStrategy:
     * Tín hiệu: Độ rộng thị trường (% số mã trên MA20) tăng vọt từ <15% lên >60% trong vòng 10 phiên.
     * Hành động: Kích hoạt mua rổ cổ phiếu Leading có Relative Strength (RS) cao nhất.
   * AllTimeHighBreakoutStrategy:
     * Tín hiệu: Giá vượt đỉnh lịch sử 52 tuần với thanh khoản gấp 1.5x trung bình 20 phiên.
2. **Module quant.factors.smart_money**:
   * Hàm tính toán dòng tiền ròng khối ngoại tích lũy (Cumulative Foreign Net Value).
   * Hàm tính toán dòng tiền tự doanh CTCK.
   * Tỷ lệ khớp lệnh chủ động Mua / Bán (Active Buy/Sell Ratio).
3. **Tiêu chuẩn nghiệm thu**:
   * Unit tests kiểm thử độc lập cho từng hàm factor và chiến lược.
   * Chạy kiểm thử mẫu trên dữ liệu giả lập có cột oreign_net_val.

---

### 📌 Milestone 3: v0.3.0 — High-Fidelity Vi Cấu Trúc Thị Trường Việt Nam
**Mục tiêu**: Nâng cấp VNBacktest đạt độ chân thực tối đa, loại bỏ hoàn toàn các giả định vô lý của phần mềm ngoại.

1. **Mô phỏng Bẫy Trần / Sàn (quant.backtest.limits)**:
   * Biên độ dao động: HOSE (±7%), HNX (±10%), UPCoM (±15%).
   * **Quy tắc Bẫy Sàn ("Múa bên trăng")**: Nếu Close == Floor_Price và khối lượng mua cạn kiệt:
     * Lệnh BÁN không được phép khớp tại phiên đó.
     * Vị thế bị giữ lại, tính toán trượt giá (slippage) và đẩy sang các phiên tiếp theo cho đến khi có thanh khoản trở lại.
   * **Quy tắc Bẫy Trần**: Nếu Close == Ceiling_Price trắng bên bán, bot không được phép khớp lệnh mua đuổi giá trần.
2. **Quy chuẩn Bước giá (Tick Sizes) theo luật UBCK**:
   * Cổ phiếu giá < 10,000 VND: bước giá 10 VND.
   * Cổ phiếu giá 10,000 - 49,950 VND: bước giá 50 VND.
   * Cổ phiếu giá ≥ 50,000 VND: bước giá 100 VND.
   * Làm tròn lệnh mua bán theo đúng bước giá và chuẩn lô 100 cổ phiếu.
3. **Mô phỏng Phiên định kỳ ATO / ATC**:
   * Cho phép đặt lệnh với giá mở cửa ATO hoặc giá đóng cửa ATC.
   * Tính toán rủi ro trượt giá (slippage) ngẫu nhiên tại ATC.

---

### 📌 Milestone 4: v0.4.0 — Phái Sinh Chuyên Biệt (VN30F1M Derivatives Engine)
**Mục tiêu**: Tạo ra framework đầu tiên tại Việt Nam hỗ trợ backtest thuật toán phái sinh T+0 chuyên dụng.

1. **Engine VN30FBacktest (quant.backtest.derivatives)**:
   * Giao dịch T+0 hai chiều (Long / Short).
   * Hệ số nhân hợp đồng: 100,000 VND / điểm.
   * Mô phỏng Ký quỹ VSD: Tỷ lệ ký quỹ ban đầu (IM ~17%), phí giao dịch Sở/VSD và phí CTCK theo từng hợp đồng.
   * Cơ chế Daily Mark-to-Market: Chốt lãi lỗ vị thế qua đêm theo giá DSP (Daily Settlement Price).
2. **Chiến lược Phái sinh Thực chiến (quant.strategies.derivatives)**:
   * BasisArbitrageStrategy: Khai thác hiện tượng hội tụ Basis (VN30F1M vs VN30 Index) trong tuần đáo hạn (thứ Năm tuần thứ 3 mỗi tháng).
   * OpeningRangeBreakout15m: Đánh theo quán tính biên độ 15 phút đầu phiên (9:15 - 9:30), tất toán trước 14:15 để tránh rủi ro biến động khó lường phiên ATC.
   * PortfolioBetaHedging: Tự động tính số lượng hợp đồng Short phái sinh cần mở để bảo hiểm danh mục cơ sở dựa trên hệ số rủi ro $\beta$ mà không cần bán tháo cổ phiếu.

---

### 📌 Milestone 5: v0.5.0 — Quản Trị Rủi Ro Đòn Bẩy & Phân Bổ Vốn Tối Ưu
**Mục tiêu**: Giúp nhà đầu tư và quỹ bảo vệ vốn tuyệt đối trước các đợt suy thoái mạnh.

1. **Module quant.risk.margin**:
   * MarginGuardian: Tính toán Tỷ lệ An toàn Thực tế (RTT) chuẩn các CTCK:
     \text{RTT} = \frac{\text{Tổng Tài sản Thực có}}{\text{Tổng Nợ Vay Margin}}
   * Cảnh báo sớm: Ngưỡng Call Margin ( \le 0.85$) và Ngưỡng Force Sell ( \le 0.80$).
   * Hàm tính toán: *"Mã X trong danh mục được phép giảm tối đa bao nhiêu % nữa trước khi tài khoản bị công ty chứng khoán giải chấp cưỡng bức?"*.
2. **Module quant.portfolio.sizing**:
   * KellyCriterion: Tính toán tỷ trọng vị thế tối ưu dựa trên Win Rate và Win/Loss Ratio lịch sử.
   * FixedRiskSizer: Quy định mỗi giao dịch chỉ chịu rủi ro tối đa \% - 2\%$ tổng NAV.
   * RiskParityOptimizer: Phân bổ vốn cân bằng rủi ro biến động giữa các nhóm ngành.

---

### 📌 Milestone 6: v0.6.0 — Data Adapters & Ecosystem Integration
**Mục tiêu**: Biến VQuant thành trung tâm định lượng kết nối mượt mà với mọi nguồn dữ liệu tài chính tại Việt Nam.

1. **VNStockAdapter**:
   * Tích hợp cắm rút dữ liệu trực tiếp từ nstock / nstock_data chỉ với 1 dòng code:
     `python
     from vquant.data import VNStockAdapter
     adapter = VNStockAdapter()
     df = adapter.get_price("HPG", start="2023-01-01", end="2024-12-31")
     `
2. **FileAdapter**:
   * Tối ưu hóa đọc/ghi dữ liệu tốc độ cao qua định dạng parquet, eather, hoặc cơ sở dữ liệu duckdb.

---

### 📌 Milestone 7: v1.0.0 — Live Execution & Paper Trading (Giao Dịch Thực Chiến)
**Mục tiêu**: Đưa chiến lược từ phòng thí nghiệm ra thị trường thật.

1. **PaperBroker**:
   * Giả lập khớp lệnh thời gian thực theo luồng giá live, theo dõi PnL và danh mục ảo.
2. **DNSEBroker**:
   * Kết nối chính thức với **DNSE Entrade X Open API**: Đăng nhập qua API Key/Secret, đặt lệnh Mua/Bán tự động, truy vấn số dư tiền và cổ phiếu.
3. **TradeNotifier**:
   * Tự động gửi cảnh báo tín hiệu Mua/Bán và báo cáo NAV tổng kết phiên qua **Telegram Bot / Discord Webhook**.

---

## 🔒 Quy trình Làm việc Chuẩn mực (Strict Workflow)

Từ thời điểm này, mỗi khi bắt tay vào một Milestone mới:
1. **Bước 1 — Plan First**: Cập nhật chi tiết các đầu việc, class và hàm vào file implementation.md này và trình bày kế hoạch cho bạn duyệt.
2. **Bước 2 — Review & Approve**: Bạn xem xét, góp ý và bấm duyệt kế hoạch.
3. **Bước 3 — Execution & Testing**: Bắt đầu viết code, viết unit tests đầy đủ, chạy test 100% pass.
4. **Bước 4 — Build & Push**: Nâng version, build gói phân phối, upload lên PyPI và push commit lên GitHub.
