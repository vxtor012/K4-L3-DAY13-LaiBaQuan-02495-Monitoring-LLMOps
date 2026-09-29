# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Lại Bá Quân
- **MSSV:** 02495
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/vxtor012/K4-L3-DAY13-LaiBaQuan-02495-Monitoring-LLMOps
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-02495`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đạt tuyệt đối 4 tiêu chí: schema, correlation ID, enrichment context, PII scrubbing |
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | Hợp lệ dashboard contract |
| `pytest` | 22 passed | 26 passed | Bổ sung các unit test cho CCCD, Credit Card, Correlation ID & Log Enrichment |
| Số traces hợp lệ | | | |
| Số PII leak | 0 | 0 | Không có rò rỉ PII nguyên văn |
| Latency P95 / TTFT P95 | | | |
| Retrieval success rate | | | |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong `app/middleware.py`, middleware `CorrelationIdMiddleware` xóa context cũ bằng `clear_contextvars()` trước mỗi request để tránh context leakage giữa các request đồng thời. Tiếp đó trích xuất header `x-request-id`, nếu không có sẽ tự sinh ID chuẩn `req-<8-hex>` qua `f"req-{uuid.uuid4().hex[:8]}"`. ID này được bind vào contextvars qua `bind_contextvars(correlation_id=correlation_id)`, lưu vào `request.state.correlation_id` và trả ngược về client trong header `x-request-id` cùng `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** Ngay đầu endpoint `/chat` (`app/main.py`), các metadata ngữ cảnh được bind qua `bind_contextvars` gồm: `user_id_hash` (băm SHA256 lấy 12 ký tự), `session_id`, `feature`, `model`, `env`. Nhờ đó mọi log sau đó (`request_received`, `response_sent`, `request_failed`) đều tự động chứa đầy đủ các trường enrichment này.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor `scrub_event` được đăng ký vào pipeline `structlog` (`app/logging_config.py`) trước `JsonlFileProcessor` và `JSONRenderer`. Hàm `scrub_event` duyệt đệ quy tất cả các trường dữ liệu (ngoại trừ các key định danh hệ thống như `ts`, `level`, `service`, `correlation_id`, `user_id_hash`) và áp dụng regex (`app/pii.py`) để che các dạng PII gồm Email, Số điện thoại Việt Nam, CCCD 12 số, Thẻ tín dụng/ngân hàng thành `[REDACTED_<NAME>]` trước khi dữ liệu được serialize và ghi ra file/stdout.
- **Cách kiểm chứng kết quả:** Chạy `python scripts/validate_logs.py` đạt điểm số 100/100; toàn bộ 26/26 unit tests trong `python -m pytest` vượt qua kiểm tra, đảm bảo không có rò rỉ dữ liệu nhạy cảm và correlation ID được lan truyền xuyên suốt.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
- **Cấu trúc root/retrieval/generation observations:**
- **Cách nối trace với log:**
- **Prompt name:**
- **Version/label baseline:**
- **Version/label candidate:**
- **Trace ID của mỗi version:**
- **Cách promote và rollback `production`:**

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
- **SLO và lý do chọn:**
- **Cách tính error budget:**
- **Ba alert và runbook tương ứng:**

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
