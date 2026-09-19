# VQUANT IMPLEMENTATION & ENGINEERING MASTER PLAN 🛠️

> **Tài liệu tham chiếu:** [ARCHITECTURE.md](./ARCHITECTURE.md) | [ROADMAP.md](./ROADMAP.md)  
> **Package Name:** `vquant` (Namespace PyPI & GitHub chính thức; import alias: `import vquant as vq`)  
> **Mục tiêu:** Bản kế hoạch kỹ thuật chi tiết chuyển giao toàn bộ kiến trúc và lộ trình 52 tuần vào mã nguồn, bảo đảm nguyên tắc: **"Mô phỏng TTCK Việt Nam trung thực theo mặc định, không bao giờ gian lận dữ liệu."**

---

## 1. TỔNG QUAN ĐỒNG BỘ KIẾN TRÚC & LỘ TRÌNH

Tài liệu này đồng bộ hóa 100% giữa **Kiến trúc ([ARCHITECTURE.md](./ARCHITECTURE.md))** và **Lộ trình 8 Giai đoạn ([ROADMAP.md](./ROADMAP.md))**, định nghĩa chính xác cấu trúc thư mục, hợp đồng dữ liệu (Data Contracts), các lớp trừu tượng (Protocols) và tiêu chuẩn nghiệm thu cho đội ngũ phát triển.

### 1.1 Triết lý & 8 Nguyên tắc Thiết kế Bắt buộc (P1 - P8)

| Mã | Nguyên tắc | Cách hiện thực hóa trong Code | Kiểm tra & Chặn vi phạm |
|---|---|---|---|
| **P1** | **Market rules are versioned data, not code.** | Mọi quy định thị trường (phiên, biên độ, bước giá, lô, thuế, T+2.5, KRX) nằm trong file YAML tại `vquant/market/regimes/` kèm ngày `effective_from`. Không dùng `if date > '2025-05-05'` trong logic. | Property test: Mỗi ngày từ 2015-01-01 đến 2027-12-31 chỉ map chính xác 1 regime cho mỗi sàn. |
| **P2** | **Point-in-time (PIT) everywhere.** | Mọi bản ghi dữ liệu (giá, BCTC, danh mục chỉ số) đều có trường `available_at`. Mọi truy vấn bắt buộc có tham số `as_of`. | Shift-invariance tests: Dữ liệu tương lai bị làm nhiễu không được làm thay đổi kết quả tính toán tại thời điểm $t$. |
| **P3** | **Reproducible runs.** | Mọi kết quả backtest xuất ra kèm Run Manifest: Hash dữ liệu Parquet, Git commit SHA, thư viện & seed. | Manifest hash validator; chạy lại cùng manifest cho kết quả đồng nhất 100%. |
| **P4** | **Provider-agnostic core.** | Tách rời logic cốt lõi khỏi nguồn cào. Nguồn dữ liệu tuân thủ `typing.Protocol` trong `vquant/data/providers/`. | Contract tests ghi âm VCR-style; nightly canary CI bắt lỗi trôi schema của nguồn ngoài. |
| **P5** | **Pandas-facing, columnar inside.** | API công khai trả về `pandas.DataFrame`. Lưu trữ và xử lý nền tảng bằng Apache Arrow (`pyarrow`), Parquet và DuckDB. | Benchmark: Backtest 100 cổ phiếu × 10 năm < 1 giây trên engine vector hóa. |
| **P6** | **Fail loud.** | `strict=True` theo mặc định. Lỗi vi phạm trần/sàn, bước giá, lô chẵn hoặc lệch giá tham chiếu điều chỉnh sẽ raise lỗi hoặc đưa vào bảng cách ly `quarantine`. Không sửa ngầm. | V001–V011 Validation suite chạy tự động khi nạp và điều chỉnh dữ liệu. |
| **P7** | **Explicit stability tiers.** | Mọi module/class/hàm đều gắn nhãn `@tier("stable" | "beta" | "experimental")`. SemVer áp dụng nghiêm ngặt cho `stable`. | CI cảnh báo deprecation trước 2 minor versions; cấm đổi signature của tier `stable`. |
| **P8** | **Honest by default.** | Mọi báo cáo backtest bắt buộc tích hợp phần Kiểm định Trung thực: Ghi nhận số lần thử ($N$), DSR, PBO, MinBTL, phân bổ chi phí thuế/phí/trượt giá. | Cấm xuất báo cáo chỉ có Sharpe thuần túy mà không có DSR (Deflated Sharpe Ratio). |

---

## 2. KẾ HOẠCH TÁI CẤU TRÚC MÃ NGUỒN (REFACTORING & TARGET LAYOUT)

### 2.1 Đánh giá Hiện trạng Codebase (v0.2.0)
* **Đã có:** Thư viện đã đăng ký thành công trên PyPI và GitHub (`vquant`), có prototype hoạt động được cho `VNBacktest` (T+2.5, thuế 0.1%), các chiến lược mẫu (`MinerviniVCP`, `TurtleBreakoutVN`, `ForeignFlow`, `BreadthThrust`, `AllTimeHighBreakout`), và dữ liệu giả lập `load_sample_data()`.
* **Nợ kỹ thuật (Technical Debt) cần xử lý:**
  1. Luật thị trường còn bị hardcode bên trong `vquant/backtest/engine.py` -> Cần tách ra `vquant/market/regimes/*.yaml` (P1).
  2. Chưa có lớp lưu trữ Parquet + DuckDB chuẩn và cơ chế điều chỉnh giá theo sự kiện quyền (Corporate Actions Reconciler) (P5, P6).
  3. Chưa có giao diện Provider Protocol và cơ chế kiểm soát Point-in-time (P2, P4).
  4. Cần chuẩn hóa cấu trúc thư mục từ dạng phẳng sang phân tầng hoàn chỉnh theo ARCHITECTURE §10.

### 2.2 Cấu trúc Thư mục Đích Chuẩn (Target Package Layout)

```text
vquant/
├── __init__.py                 # Export public API: prices(), backtest.run(), validate.*
├── __version__.py              # Quản lý phiên bản SemVer
├── pyproject.toml              # Cấu hình đóng gói, dependencies, extras, linter
│
├── market/                     # Core Rules Engine (Không phụ thuộc layer khác)
│   ├── __init__.py
│   ├── engine.py               # market.regime(date, exchange), tick, lot, band resolution
│   ├── calendar.py             # Lịch giao dịch HOSE/HNX (2015-2027), Tết, nghỉ lễ, bù
│   └── regimes/                # Dữ liệu quy chế có hiệu lực theo thời gian
│       ├── hose/
│       │   ├── 2000-07-28.yaml # Giai đoạn sơ khai
│       │   ├── 2016-09-12.yaml # Thay đổi bước giá 10/50/100đ
│       │   └── 2025-05-05.yaml # Cutover hệ thống KRX (bước giá, ATO/ATC, T+0 flag)
│       ├── hnx/
│       └── upcom/
│
├── data/                       # Ingest, Validation, Storage & PIT Catalog
│   ├── __init__.py
│   ├── providers/              # Adapters tuân thủ Provider Protocol
│   │   ├── base.py             # Protocol, Capability, RateLimiter, IncrementalCache
│   │   ├── vnstock_adapter.py  # Free community provider adapter
│   │   ├── ssi_adapter.py      # SSI FastConnect API adapter
│   │   ├── dnse_adapter.py     # DNSE Open API adapter
│   │   └── file_adapter.py     # BYO Parquet / CSV adapter
│   ├── store/                  # Lưu trữ nhị phân hiệu năng cao
│   │   ├── raw.py              # Ghi Parquet bất biến (immutable partition theo year/exchange)
│   │   ├── normalized.py       # Parquet đã làm sạch và điều chỉnh giá
│   │   └── catalog.py          # DuckDB catalog, snapshot hashing
│   ├── schema/                 # PyArrow schemas định kiểu chặt chẽ
│   ├── validate/               # Bộ kiểm tra tính toàn vẹn V001–V011
│   │   └── checks.py           # V001 (biên độ), V002 (tick grid), V004 (lô), V008 (quyền)
│   └── pit/                    # Truy vấn bitemporal (available_at, as_of)
│
├── corpactions/                # Động cơ Bóc tách & Điều hòa Quyền
│   ├── __init__.py
│   ├── parser.py               # Chuẩn hóa sự kiện: Cổ tức tiền, cổ phiếu thưởng, phát hành thêm
│   ├── adjust.py               # Tính toán hệ số điều chỉnh Price-return & Total-return
│   ├── reconcile.py            # Khớp nối giá tham chiếu dự phóng với giá Sở công bố
│   └── quarantine.py           # Bảng cách ly các sự kiện lệch giá tham chiếu > 1 tick
│
├── universe/                   # Lịch sử Niêm yết & Danh mục Chỉ số PIT
│   ├── __init__.py
│   ├── listings.py             # Niêm yết, hủy niêm yết, chuyển sàn (UPCoM -> HNX -> HOSE)
│   ├── indices.py              # Thành phần & tỷ trọng VN30, VN100, VNAllShare theo ngày
│   └── status.py               # Lịch sử trạng thái (bình thường, cảnh báo, kiểm soát, tạm ngừng)
│
├── features/                   # Feature Registry & Thư viện Alpha
│   ├── __init__.py
│   ├── registry.py             # @feature decorator, metadata, kiểm tra shift-invariance
│   ├── technical.py            # MA, RSI, MACD, Bollinger Bands, Donchian
│   ├── volatility.py           # Parkinson, Garman-Klass, EWMA ATR
│   ├── microstructure.py       # Tần suất chạm trần/sàn, mất thanh khoản, ATO/ATC imbalance
│   ├── flows.py                # Khối ngoại (streak, cum_flow), Tự doanh, Khớp lệnh chủ động
│   └── macro.py                # Lãi suất điều hành SBV, USD/VND, Tăng trưởng tín dụng, CPI
│
├── labeling/                   # Gán nhãn cho Machine Learning
│   ├── __init__.py
│   ├── fixed.py                # Fixed-horizon forward returns
│   ├── triple_barrier.py       # Triple-barrier có nhận biết biên độ trần/sàn
│   └── meta.py                 # Meta-labeling lọc tín hiệu và định cỡ vị thế
│
├── models/                     # Giao diện Mô hình Thống kê & Machine Learning
│   ├── __init__.py
│   ├── base.py                 # Fit / Predict / Predict_proba interface
│   ├── regimes.py              # Hidden Markov Models (HMM) phân loại chế độ thị trường
│   └── volatility.py           # GARCH(1,1) dự báo phương sai có điều kiện
│
├── validate/                   # Bộ Công cụ Kiểm định Trung thực (Anti-Overfitting)
│   ├── __init__.py
│   ├── purged_cv.py            # Purged & Embargoed K-Fold Cross Validation
│   ├── cpcv.py                 # Combinatorial Purged Cross-Validation
│   ├── dsr.py                  # Deflated Sharpe Ratio (hiệu chỉnh số lần thử N, skew, kurtosis)
│   ├── pbo.py                  # Probability of Backtest Overfitting
│   └── minbtl.py               # Minimum Backtest Length cần thiết để khẳng định Sharpe
│
├── backtest/                   # Hai Động cơ Kiểm thử - Một Lớp Luật Thị trường
│   ├── __init__.py
│   ├── vectorized.py           # Engine vector hóa siêu tốc (Arrow -> NumPy, tradability masks)
│   ├── event.py                # Engine hướng sự kiện (ATO, ATC, LO, MP, partial fills)
│   ├── fills.py                # Mô hình khớp: Chặn bẫy sàn ("múa bên trăng"), bẫy trần, slippage
│   ├── costs.py                # Thuế bán 0.1%, phí môi giới theo bậc, thuế cổ tức tiền 5%
│   ├── ledger.py               # Sổ cái giao dịch: Trạng thái T+0, T+1, T+2 PM và 6 bất biến
│   └── report.py               # Tear sheet hiệu năng kèm Integrity Section & Run Manifest
│
├── portfolio/                  # Tối ưu hóa & Phân bổ Danh mục Thực tế
│   ├── __init__.py
│   ├── lot_allocator.py        # Thuật toán phân bổ nhận biết Lô 100 cổ phiếu (Greedy & MILP)
│   ├── optimizers.py           # Risk Parity, HRP (Hierarchical Risk Parity), Mean-Variance
│   ├── risk.py                 # Quản trị rủi ro thanh khoản ADV, rủi ro kẹt sàn
│   ├── margin.py               # MarginGuardian: Tỷ lệ RTT, Cảnh báo Call Margin / Force Sell
│   └── vn30f.py                # Phái sinh VN30F: Ký quỹ VSD, hệ số nhân 100k, Roll hợp đồng
│
├── execution/                  # Cầu nối Thực thi Giao dịch (Giai đoạn sau)
│   ├── __init__.py
│   ├── oms.py                  # Order Management System (State machine, ID lũy đẳng)
│   ├── paper.py                # Paper trading engine chia sẻ chung fill model với event engine
│   └── brokers/                # Adapters CTCK (DNSE, SSI) kèm Pre-trade Risk Checks
│
├── cli/                        # Giao diện Dòng lệnh (CLI)
│   └── main.py                 # vq fetch | vq validate | vq backtest | vq report
│
└── datasets/                   # Dữ liệu Mẫu đính kèm Thư viện
    ├── __init__.py
    └── sample.py               # load_sample_data(), load_sample_flow_data()
```

---

## 3. KẾ HOẠCH TRIỂN KHAI CHI TIẾT THEO 8 GIAI ĐOẠN (PHASES 0 TO 7)

---

### 🔹 PHASE 0: FOUNDATIONS (Tuần 1–2 · 40 giờ)
**Mục tiêu:** Thiết lập khung sườn kho mã nguồn thực thi nghiêm ngặt các nguyên tắc kiến trúc trước khi viết code nghiệp vụ.

#### 1. Các Đầu việc Kỹ thuật:
- [ ] Chuẩn hóa `pyproject.toml` (hỗ trợ Python 3.10 - 3.13), cấu hình `ruff` (linter/formatter), `mypy --strict`, `import-linter`.
- [ ] Thiết lập hợp đồng phân tầng `import-linter`:
  - `market` không được import bất kỳ module nào khác.
  - `data` chỉ được import `market`.
  - `backtest` chỉ được import `market`, `data`, `corpactions`, `universe`.
  - Các module nghiệp vụ không được import chéo hoặc import ngược từ `execution`.
- [ ] Thiết lập GitHub Actions CI Matrix: Lint, Type check, Unit tests trên 3 hệ điều hành (Ubuntu, macOS, Windows).
- [ ] Viết bộ nạp Quy chế Thị trường (`vquant/market/engine.py` và `vquant/market/calendar.py`):
  - Định nghĩa Schema YAML cho Regimes.
  - Mã hóa các file: `hose/2016-09-12.yaml` (bước giá 10/50/100đ), `hose/2025-05-05.yaml` (cutover KRX), `hnx/default.yaml`, `upcom/default.yaml`.
  - Mã hóa Lịch giao dịch Việt Nam 2015–2027 (`vquant/market/data/calendar.csv` hoặc YAML) gồm Tết âm lịch, Giỗ tổ, 30/4-1/5, 2/9 và các ngày nghỉ bù/giao dịch bù.
- [ ] Khởi tạo thư mục `docs/` với tài liệu song ngữ (Anh - Việt) bằng `mkdocs-material`.

#### 2. Tiêu chí Nghiệm thu (Exit Criteria):
* `market.regime(date, exchange)` trả về duy nhất 1 regime hợp lệ cho mọi ngày từ `2015-01-01` đến `2026-12-31` (Property test: không có khoảng trống ngày, không bị chồng chéo).
* Lịch giao dịch khớp 100% không sai lệch trên mẫu đối soát 50 ngày thực tế (cả ngày làm việc và ngày lễ).
* `import-linter` bắt và chặn đứng thành công 1 trường hợp cố tình import sai tầng trong test suite.

---

### 🔹 PHASE 1: DATA CORE ➔ v0.1 (Tuần 3–8 · 120 giờ)
**Mục tiêu:** Cung cấp dữ liệu giá nến ngày điều chỉnh quyền, Point-in-time, chuẩn hóa tuyệt đối cho VN30 và VN100.

#### 1. Các Đầu việc Kỹ thuật:
- [ ] Thiết kế `Provider` Protocol với `typing.Protocol`:
  - Các capability: `PRICES_DAILY`, `CORPORATE_ACTIONS`, `FUNDAMENTALS`, `UNIVERSE`, `FLOWS`.
  - Tích hợp Client-side Rate Limiter, Retry exponential backoff kèm Jitter.
  - Bộ nhớ đệm phân tầng `IncrementalCache` theo khóa `(symbol, date_range, schema_version)`.
- [ ] Triển khai `VNStockAdapter` và `FileAdapter` (đọc Parquet/CSV tự cung cấp).
- [ ] Xây dựng Lớp Lưu trữ Phân tầng (`vquant/data/store/`):
  - `Raw layer`: Lưu Parquet bất biến theo partition `raw/<provider>/<dataset>/<year>/<exchange>/`.
  - `Normalized layer`: Parquet đã làm sạch và điều chỉnh giá, có thể tái tạo 100% từ Raw.
  - `Catalog layer`: Tệp DuckDB views ánh xạ lên Parquet, tính toán Run Snapshot Hash.
- [ ] Xây dựng Bộ Động cơ Quyền Doanh nghiệp (`vquant/corpactions/`):
  - Parser: Cổ tức tiền, cổ phiếu thưởng, phát hành thêm quyền mua, chia tách.
  - Reconciler: Tính giá tham chiếu lý thuyết tại ngày giao dịch không hưởng quyền (GDKHQ):
    $$P_{	ext{ref\_pred}} = rac{P_{	ext{close}} - C + P_{	ext{issue}} 	imes r_{	ext{issue}}}{1 + r_{	ext{bonus}} + r_{	ext{issue}}}$$
  - So sánh $P_{	ext{ref\_pred}}$ với giá tham chiếu thực tế Sở giao dịch công bố. Nếu lệch $> 1$ bước giá -> Đưa ngay vào bảng cách ly `quarantine`, tuyệt đối không vá ngầm.
- [ ] Xây dựng Bộ Kiểm tra Tính toàn vẹn Dữ liệu V001–V011:
  - V001: Lợi nhuận giá so với tham chiếu nằm trong biên độ trần/sàn `[floor%, ceil%]`.
  - V002: Giá nằm đúng trên lưới bước giá quy chuẩn của từng sàn.
  - V003: $Low \le \min(Open, Close) \le \max(Open, Close) \le High$.
  - V004: Khối lượng là số nguyên không âm và là bội số của lô 100 (trừ lô lẻ).
  - V008: Kiểm tra điều hòa sự kiện quyền doanh nghiệp.
- [ ] Xây dựng Point-in-time Universe:
  - Truy vấn `universe.as_of(date, index="VN100", tradable=True)` trả về đúng các mã đang niêm yết và được giao dịch vào thời điểm đó (loại bỏ hoàn toàn survivorship bias).

#### 2. Tiêu chí Nghiệm thu (Exit Criteria):
* Tỷ lệ khớp nối giá tham chiếu GDKHQ của các mã VN30 trong 10 năm đạt $\ge 99\%$, $100\%$ các trường hợp lệch còn lại được ghi nhận rõ nguyên nhân trong `known-issues.md`.
* Vi phạm V001 sau điều chỉnh bằng 0.
* Tốc độ nạp dữ liệu: Cold fetch 30 mã × 10 năm < 5 phút; Warm incremental fetch < 20 giây.

---

### 🔹 PHASE 2: BACKTEST CORE ➔ v0.2 (Tuần 9–14 · 120 giờ)
**Mục tiêu:** Xây dựng Động cơ Kiểm thử chuẩn xác theo đúng quy tắc giao dịch và chu kỳ thanh toán Việt Nam.

#### 1. Các Đầu việc Kỹ thuật:
- [ ] Triển khai Kiến trúc Hai Động cơ (`vquant/backtest/`):
  - **Vectorized Engine**: Tối ưu hóa trên NumPy mảng 2D cho quét tham số nhanh (Parameter sweeps). Áp dụng Tradability masks, làm tròn lô và sổ cái thanh toán.
  - **Event-Driven Engine**: Mô phỏng khớp lệnh chi tiết từng bar: Lệnh ATO, ATC, LO, MP, khớp một phần, giới hạn tỷ lệ tham gia phiên.
- [ ] Mô hình Khớp lệnh (Fill Model):
  - **Bẫy Sàn ("Múa bên trăng")**: Khi giá mở cửa chạm sàn và khối lượng mua bị nghẽn -> Không cho phép khớp lệnh BÁN.
  - **Bẫy Trần**: Khi giá mở cửa chạm trần trắng bên bán -> Không cho phép khớp lệnh MUA đuổi.
  - **Giới hạn tỷ lệ tham gia**: Khớp tối đa $p 	imes 	ext{Volume}$ phiên (mặc định $5\% - 10\%$).
  - **Mô hình Trượt giá (Slippage)**: $	ext{Slippage} = \max\left(rac{	ext{Tick}}{2}, Y 	imes \sigma_d 	imes \sqrt{rac{Q}{V}}ight)$.
- [ ] Mô hình Chi phí Thực tế Việt Nam (Cost Model):
  - Phí môi giới 2 chiều theo bậc (mặc định $0.15\%$).
  - Thuế TNCN bán chứng khoán: **$0.1\%$ trên tổng doanh số bán** (bất kể lãi lỗ).
  - Thuế cổ tức tiền mặt: $5\%$ khấu trừ tại nguồn.
  - Lãi vay Margin tính theo ngày nắm giữ.
- [ ] Sổ cái Quản lý Vị thế & Chu kỳ Thanh toán (Settlement Ledger):
  - Quản lý 3 trạng thái hàng: `settled` (được bán ngay), `pending_T1` (đang về), `pending_T2_AM` (về tài khoản chiều T+2).
  - Quản lý tiền: Tiền khả dụng, tiền bán chờ về T+2.
  - Kiểm định 6 bất biến sổ cái (Bảo toàn tiền, bảo toàn cổ phiếu, không âm tiền mặt khi không có margin, v.v.) bằng `hypothesis` property-based testing.
- [ ] Bộ Báo cáo Hiệu năng (Tear Sheet) & Run Manifest.

#### 2. Tiêu chí Nghiệm thu (Exit Criteria):
* Mức độ phân kỳ tích lũy (Cumulative equity divergence) giữa Vectorized Engine và Event Engine trên 3 chiến lược chuẩn < 5 bps.
* 6 bất biến của Ledger vượt qua 1,000,000 ca kiểm thử ngẫu nhiên với `hypothesis` (0 lỗi).
* Thời gian chạy: Backtest vector hóa 100 cổ phiếu × 10 năm < 1 giây; Event-driven < 10 giây (pure Python).

---

### 🔹 PHASE 3: RESEARCH TOOLKIT ➔ v0.3 (Tuần 15–20 · 120 giờ)
**Mục tiêu:** Cung cấp bộ công cụ nghiên cứu định lượng trung thực, chống Overfitting và rò rỉ dữ liệu (Lookahead bias).

#### 1. Các Đầu việc Kỹ thuật:
- [ ] Xây dựng Feature Registry (`vquant/features/registry.py`):
  - Decorator `@feature` khai báo rõ `lookback`, `lag`, `availability` ("close_t" hoặc "open_t1").
  - Tự động chạy **Shift-Invariance Test**: Thay đổi dữ liệu sau ngày $t$ tuyệt đối không làm thay đổi giá trị feature tại ngày $t$.
  - Thư viện feature: Kỹ thuật (MA, RSI, MACD, Bollinger), Biến động (Parkinson, Garman-Klass, ATR), Vi cấu trúc (Tần suất trần/sàn, mất thanh khoản).
- [ ] Module Gán nhãn (Labeling):
  - Fixed-horizon forward return.
  - Triple-barrier nhận biết biên độ: Rào cản biến động có tính đến giới hạn biên độ trần/sàn từng phiên.
  - Meta-labeling: Sử dụng mô hình Machine Learning định cỡ vị thế cho chiến lược rule-based.
  - Theo dõi khoảng chồng lấn mẫu `(t0, t1)` phục vụ phân rã dữ liệu.
- [ ] Module Mô hình (Models): Wrapper thống nhất `fit / predict / predict_proba` cho scikit-learn, LightGBM, HMM và GARCH.
- [ ] Module Kiểm định Toàn vẹn (Anti-Overfitting Validation):
  - `PurgedGroupTimeSeriesSplit`: K-Fold loại bỏ rò rỉ dữ liệu kèm thời gian giãn cách (embargo).
  - `CPCV` (Combinatorial Purged Cross-Validation): Tạo phân phối đường cong lợi nhuận ngoài mẫu.
  - `DeflatedSharpeRatio` (DSR): Hiệu chỉnh Sharpe theo số lượng thử nghiệm $N$, độ lệch và độ nhọn.
  - `PBO` (Probability of Backtest Overfitting): Đo xác suất chiến lược tốt nhất là do may mắn.
  - `MinBTL`: Tính toán số năm dữ liệu tối thiểu cần thiết để một mức Sharpe có ý nghĩa thống kê.
  - Tự động tích hợp bảng **Integrity Section** vào mọi báo cáo backtest.

#### 2. Tiêu chí Nghiệm thu (Exit Criteria):
* Thuật toán DSR, PBO, MinBTL khớp chính xác kết quả tham chiếu công bố của Marcos López de Prado với sai số $< 10^{-6}$.
* 100% các features trong Registry vượt qua bài test Shift-invariance.
* Bài test chứng minh tập huấn luyện (train set) không chứa mẫu nào rơi vào cửa sổ embargo của tập kiểm tra (test set).

---

### 🔹 PHASE 4: PORTFOLIO AND RISK ➔ v0.4 (Tuần 21–28 · 160 giờ)
**Mục tiêu:** Phân bổ danh mục thực tế nhận biết ràng buộc Lô 100 cổ phiếu và tích hợp Phái sinh VN30F.

#### 1. Các Đầu việc Kỹ thuật:
- [ ] Bộ Phân bổ Vốn Nhận biết Lô Chẵn (`vquant/portfolio/lot_allocator.py`):
  - Thuật toán Greedy & Tối ưu hóa nguyên MILP: Chuyển đổi tỷ trọng mục tiêu (ví dụ 5%) thành số lượng cổ phiếu tròn lô 100, tối thiểu hóa tiền mặt nhàn rỗi thừa và sai số bám sát (tracking error) với tài khoản nhỏ (100M - 500M VND).
- [ ] Các Thuật toán Phân bổ Vốn Cổ điển & Hiện đại:
  - Equal Weight, Risk Parity, Hierarchical Risk Parity (HRP), Inverse Volatility, Fractional Kelly.
- [ ] Module Quản trị Rủi ro Danh mục:
  - Ma trận hiệp phương sai co rút (Ledoit-Wolf Shrinkage).
  - Rủi ro thanh khoản theo % khối lượng giao dịch trung bình ngày (ADV Cap).
  - Giới hạn sụt giảm tài sản danh mục (Drawdown Circuit Breakers).
- [ ] Module Giám sát Đòn bẩy Margin (`vquant/risk/margin.py`):
  - Mô phỏng tỷ lệ RTT, cảnh báo ngưỡng Call Margin ($RTT \le 0.85$) và Force Sell ($RTT \le 0.80$).
- [ ] Hỗ trợ Phái sinh VN30F1M (`vquant/portfolio/vn30f.py`):
  - Hệ số nhân 100,000 VND/điểm, bước giá 0.1 điểm, biên độ $\pm 7\%$.
  - Tính toán ký quỹ VSD (Ký quỹ ban đầu IM, ký quỹ biến đổi VM hàng ngày).
  - Xử lý đáo hạn và đảo kỳ hạn (Roll contract) vào thứ Năm tuần thứ 3 hàng tháng.
  - Chiến lược bảo hiểm danh mục cơ sở (Portfolio Beta Hedging Overlay).

#### 2. Tiêu chí Nghiệm thu (Exit Criteria):
* Thuật toán `lot_allocator` đạt sai số bám sát thấp hơn phân bổ làm tròn ngây thơ trên danh mục 100M VND (20 mã) trong 5 năm thử nghiệm.
* Tiền mặt dư thừa sau phân bổ $\le 1$ lô của cổ phiếu có thị giá thấp nhất trong danh mục.
* PnL phái sinh khớp chính xác đến từng 1 VND so với bảng tính mẫu đối soát.

---

### 🔹 PHASE 5: PIT FUNDAMENTALS AND FLOWS ➔ v0.5 (Tuần 29–36 · 160 giờ)
**Mục tiêu:** Kho dữ liệu BCTC bitemporal và dữ liệu dòng tiền không rò rỉ tương lai.

#### 1. Các Đầu việc Kỹ thuật:
- [ ] Kho Lưu trữ BCTC Bitemporal (`vquant/data/pit/`):
  - Mỗi bản ghi có `period_end` (kỳ báo cáo) và `available_at` (thời điểm công bố thông tin).
  - Xử lý số liệu hồi tố (restatement): Giá trị điều chỉnh chỉ xuất hiện sau ngày công bố báo cáo kiểm toán mới.
  - Khử lũy kế (De-cumulation): Tự động tính số liệu quý độc lập từ số liệu lũy kế đầu năm: $Q_n = 	ext{YTD}_n - 	ext{YTD}_{n-1}$. Tính TTM chuẩn 4 quý gần nhất.
- [ ] Bộ Taxonomy BCTC Chuẩn hóa theo Ngành:
  - Mẫu Ngân hàng: Thu nhập lãi thuần (NII), NIM, Tỷ lệ nợ xấu (NPL), Tỷ lệ bao phủ nợ xấu (LLR), CASA, CAR.
  - Mẫu Công ty Chứng khoán: Doanh thu môi giới, Dư nợ cho vay margin, Lãi/lỗ FVTPL tự doanh.
  - Mẫu Bất động sản: Hàng tồn kho dự án, Tiền người mua trả tiền trước ngắn hạn.
  - Mẫu Doanh nghiệp Phi tài chính chung (VAS): Doanh thu, Lợi nhuận gộp, EBIT, LNST công ty mẹ, Dòng tiền thuần từ HĐKD (CFO), Vốn lưu động.
- [ ] Dữ liệu Vi cấu trúc & Vĩ mô Chuẩn hóa:
  - Khối ngoại: Mua/bán ròng khớp lệnh, thỏa thuận, tỷ lệ sở hữu nước ngoài (FOL), room ngoại còn lại.
  - Tự doanh CTCK mua/bán ròng.
  - Dư nợ Margin toàn thị trường từ báo cáo CTCK định kỳ.
  - Chuỗi vĩ mô gắn nhãn `available_at`: Lãi suất tái cấp vốn/tái chiết khấu SBV, tỷ giá USD/VND liên ngân hàng, Tăng trưởng tín dụng, CPI, PMI, Giải ngân vốn đầu tư công.

#### 2. Tiêu chí Nghiệm thu (Exit Criteria):
* 0 vi phạm rò rỉ dữ liệu BCTC trong bài test kiểm tra tính bitemporal trên toàn bộ rổ cổ phiếu.
* Khử lũy kế: Tổng 4 quý độc lập khớp với số liệu kiểm toán cả năm trong phạm vi sai số làm tròn cho $\ge 99\%$ các cặp công ty-năm.
* Mẫu ngành phủ kín $\ge 95\%$ danh mục VN100.

---

### 🔹 PHASE 6: EXECUTION AND HARDENING ➔ v0.9 (Tuần 37–48 · 240 giờ)
**Mục tiêu:** Môi trường Paper Trading thực chiến và kết nối cổng API đặt lệnh có kiểm soát rủi ro.

#### 1. Các Đầu việc Kỹ thuật:
- [ ] Kiến trúc OMS (Order Management System):
  - Máy trạng thái đơn hàng (Order State Machine): `PENDING_SUBMIT`, `SUBMITTED`, `PARTIALLY_FILLED`, `FILLED`, `CANCELLED`, `REJECTED`.
  - Sinh mã định danh đơn hàng lũy đẳng (Idempotent Client Order ID) để chống gửi trùng lệnh khi rớt mạng.
- [ ] Động cơ Paper Trading (`vquant/execution/paper.py`):
  - Giả lập khớp lệnh thời gian thực dùng chung mô hình fill và trượt giá với Event-driven backtest engine.
- [ ] Adapters Kết nối Broker (DNSE, SSI) ở trạng thái `beta`:
  - Kiểm tra rủi ro trước giao dịch (Pre-trade Risk Checks): Chặn lệnh sai bước giá, sai lô 100, vượt biên độ trần/sàn, vượt hạn mức tiền mặt hoặc chạm ngưỡng cắt lỗ tài khoản.
  - Cơ chế Kill Switch: Ngắt kết nối và hủy toàn bộ lệnh chờ khi phát hiện bất thường.
  - Ghi nhật ký kiểm toán bất biến (Append-only Audit Log) cho mọi thông điệp gửi/nhận.
- [ ] Giao diện Dòng lệnh (CLI) hoàn chỉnh: `vq fetch`, `vq validate`, `vq backtest`, `vq report`, `vq paper`.
- [ ] Tối ưu hóa Hiệu năng: Biên dịch các vòng lặp cốt lõi bằng Numba (`njit`), chạy song song hóa đa nhân với `joblib`.
- [ ] Rà soát Pháp lý (Legal Review): Kiểm tra tính tuân thủ Luật Chứng khoán 2019 về giao dịch thuật toán và phòng chống thao túng giá.

#### 2. Tiêu chí Nghiệm thu (Exit Criteria):
* Chạy Paper Trading liên tục 30 ngày giao dịch không xuất hiện bất kỳ sai lệch nào so với giá và lệnh thực tế trên bảng điện.
* Hệ thống Pre-trade checks chặn thành công 100% các lệnh cố tình vi phạm quy tắc (lô lẻ, sai bước giá, vượt trần sàn, trùng ID).
* Quét tham số 10,000 cấu hình đạt tốc độ tăng tuyến tính theo số nhân CPU máy tính.

---

### 🔹 PHASE 7: v1.0 GA (Tuần 49–52 · 80 giờ)
**Mục tiêu:** Đóng băng API ổn định, xuất bản bộ benchmark chuẩn quốc gia và hoàn tất tài liệu.

#### 1. Các Đầu việc Kỹ thuật:
- [ ] Đóng băng API (API Freeze) cho toàn bộ các module thuộc tier `stable`. Áp dụng chính sách chuyển đổi Deprecation kéo dài tối thiểu 2 minor versions.
- [ ] Xuất bản Bộ Benchmark Mẫu ("VN-Bench"): Bộ dữ liệu và kết quả backtest chuẩn có thể tái tạo 100% bằng 1 dòng lệnh.
- [ ] Kiểm toán An ninh Mã nguồn: Quét lỗ hổng dependency bằng `pip-audit`, thiết lập GitHub Trusted Publishing phát hành tự động lên PyPI bằng OIDC token có chữ ký số.
- [ ] Hoàn thiện Tài liệu Hướng dẫn Chuyển đổi từ `vnstock` thuần sang `vquant`.
- [ ] Công bố bản phát hành chính thức v1.0 song ngữ Anh - Việt.

#### 2. Tiêu chí Nghiệm thu (Exit Criteria):
* Tối thiểu 3 lập trình viên độc lập hoàn thành bài hướng dẫn Quickstart mà không cần sự trợ giúp từ tác giả.
* Số lượng lỗi chưa xử lý (open bugs) thuộc tier `stable` tồn đọng quá 30 ngày bằng 0.
* Tái tạo bộ kết quả VN-Bench từ một môi trường máy tính trắng cho ra số liệu trùng khớp 100%.

---

## 4. KẾ HOẠCH HÀNH ĐỘNG 14 NGÀY ĐẦU TIÊN (SPRINT 1: PHASE 0 FOUNDATIONS)

Bảng phân công chi tiết 40 giờ đầu tiên để hoàn thành Phase 0:

| Ngày | Nhiệm vụ Kỹ thuật | Sản phẩm Đầu ra (Artifacts) | Số giờ |
|:---:|---|---|:---:|
| **1** | Đồng bộ tài liệu kiến trúc, rà soát bản quyền và quy chế đóng góp mã nguồn. | `LICENSE` (Apache-2.0), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`. | 3h |
| **2** | Cấu hình tooling môi trường: `pyproject.toml`, `ruff`, `mypy --strict`, pre-commit secret scanning. | Bộ cấu hình CI chạy qua không lỗi; cấm commit token bí mật. | 3h |
| **3** | Thiết lập GitHub Actions CI Matrix (Python 3.10-3.13 × Ubuntu/macOS/Windows) và khung tài liệu MkDocs. | Workflow `.github/workflows/ci.yml` và khung `docs/`. | 3h |
| **4** | Thiết lập cấu trúc package layout và cài đặt bộ quy tắc chặn import sai tầng bằng `import-linter`. | File `.importlinter` với các hợp đồng phân tầng kiểm tra tự động. | 3h |
| **5** | Xây dựng Schema YAML nạp quy chế thị trường (`vquant.market.engine`) kèm unit tests. | Schema YAML và class `MarketRegime`, hàm `load_regime()`. | 3h |
| **6** | Mã hóa quy chế sàn HOSE: Giai đoạn trước KRX và giai đoạn từ `2025-05-05` kèm trích dẫn văn bản Sở. | `vquant/market/regimes/hose/2016-09-12.yaml`, `2025-05-05.yaml`. | 3h |
| **7** | Mã hóa quy chế sàn HNX và UPCoM. Viết property test kiểm tra tính liên tục không chồng lấn ngày. | `vquant/market/regimes/hnx/`, `upcom/`; test suite kiểm tra mọi ngày. | 3h |
| **8** | Xây dựng bảng dữ liệu Lịch giao dịch Việt Nam 2015–2027 (ngày nghỉ Tết, lễ hội, ngày giao dịch bù). | `vquant/market/data/calendar.csv` hoặc YAML. | 3h |
| **9** | Đối soát và kiểm thử tự động Lịch giao dịch với mẫu 50 ngày thực tế trong quá khứ. | Test case xác nhận không có ngày giao dịch nào bị gán nhầm là ngày nghỉ. | 3h |
| **10**| Đặc tả kỹ thuật động cơ điều hòa sự kiện quyền doanh nghiệp (công thức, quy tắc làm tròn giá tham chiếu). | Module `vquant/corpactions/reconcile.py` (bản dự thảo đặc tả). | 3h |
| **11**| Thu thập thủ công dữ liệu kiểm thử vàng (Golden Fixtures) cho 15 sự kiện cổ tức tiền và cổ phiếu thưởng. | `tests/fixtures/corpactions/golden_15_events.json`. | 3h |
| **12**| Thu thập bổ sung 15–35 sự kiện quyền mua phát hành thêm và sự kiện chia tách/gộp phức tạp. | Bổ sung file fixtures kiểm thử quyền doanh nghiệp. | 3h |
| **13**| Xây dựng bài kiểm thử thuộc tính (Hypothesis property tests) cho lưới bước giá, lô chẵn và biên độ. | `tests/test_market_invariants.py` chạy 10,000 ca ngẫu nhiên. | 3h |
| **14**| Hoàn thiện tài liệu ADR-001 đến ADR-005, cập nhật README, gắn tag git `v0.0.1`. Rà soát tiêu chuẩn Phase 0. | Báo cáo nghiệm thu Phase 0 thành công, sẵn sàng bước vào Phase 1. | 4h |

---

## 5. ĐỊNH NGHĨA HOÀN THÀNH (DEFINITION OF DONE - DOD)

Mọi Pull Request (PR) hoặc tính năng mới trước khi được sáp nhập vào nhánh `main` bắt buộc phải thỏa mãn:
1. **Tests đầy đủ**: Unit test bao phủ các nhánh rẽ; có property-based test hoặc golden test đối với module giá và luật.
2. **Type Safety 100%**: Đạt chuẩn `mypy --strict` không có bất kỳ cảnh báo nào (`# type: ignore` phải có comment giải thích lý do cụ thể).
3. **Docstrings chuẩn mực**: Mọi class, function đều có docstring mô tả rõ tham số, kiểu trả về và ví dụ sử dụng.
4. **Tài liệu song ngữ**: Có trang tài liệu tương ứng bằng tiếng Anh và tiếng Việt cho các tính năng hướng đến người dùng.
5. **Trích dẫn nguồn luật**: Nếu tính năng liên quan đến quy định thị trường, bắt buộc phải đính kèm số hiệu thông tư, quyết định hoặc công văn của UBCKNN/Sở giao dịch trong mã nguồn.
