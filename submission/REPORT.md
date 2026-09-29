# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Lại Bá Quân
- **MSSV:** 2A202602495
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/vxtor012/K4-L3-DAY13-LaiBaQuan-02495-Monitoring-LLMOps
- **Commit SHA cuối:** `eb43d245f174a4d7ba7a640ad4227273d00838ae`
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-02495`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence            | Đường dẫn                           |
| ------------------- | --------------------------------------- |
| Pytest cuối        | `evidence/01-pytest.txt`              |
| Log validator       | `evidence/02-log-validator.txt`       |
| Dashboard validator | `evidence/03-dashboard-validator.txt` |
| Structured log      | `evidence/04-structured-log.txt`      |
| PII redaction       | `evidence/05-pii-redaction.txt`       |
| Trace list          | `evidence/06-trace-list.txt`          |
| Trace waterfall     | `evidence/07-trace-waterfall.txt`     |
| Trace metadata      | `evidence/08-trace-metadata.txt`      |
| Prompt versions     | `evidence/09-prompt-versions.txt`     |
| Prompt rollback     | `evidence/10-prompt-rollback.txt`     |
| Dashboard runtime   | `evidence/11-dashboard-overview.txt`  |
| Incident metric     | `evidence/12-incident-metric.txt`     |
| Incident log        | `evidence/13-incident-log.txt`        |
| Incident trace      | `evidence/14-incident-trace.txt`      |

## 3. Kết quả kỹ thuật

| Nội dung                 | Baseline     | Kết quả cuối | Nhận xét                                                                                 |
| ------------------------- | ------------ | --------------- | ------------------------------------------------------------------------------------------ |
| `validate_logs.py`      | 30/100       | 100/100         | Đạt tuyệt đối 4 tiêu chí: schema, correlation ID, enrichment context, PII scrubbing |
| `validate_dashboard.py` | 6/6 panel    | 6/6 panel       | Hợp lệ dashboard contract 6 panel                                                        |
| `pytest`                | 22 passed    | 26 passed       | Bổ sung các unit test cho CCCD, Credit Card, Correlation ID & Log Enrichment             |
| Số traces hợp lệ       | 0            | 19+ traces      | Tạo trực tiếp trên project Langfuse cá nhân day13-k4-l3a-02495                       |
| Số PII leak              | 0            | 0               | Không có rò rỉ PII nguyên văn                                                        |
| Latency P95 / TTFT P95    | 480ms / 50ms | 945ms / 50ms    | Thỏa mãn threshold SLO (P95 <= 3000ms)                                                   |
| Retrieval success rate    | 100%         | 100%            | Toàn bộ truy xuất tài liệu thành công                                               |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong `app/middleware.py`, middleware `CorrelationIdMiddleware` xóa context cũ bằng `clear_contextvars()` trước mỗi request để tránh context leakage giữa các request đồng thời. Tiếp đó trích xuất header `x-request-id`, nếu không có sẽ tự sinh ID chuẩn `req-<8-hex>` qua `f"req-{uuid.uuid4().hex[:8]}"`. ID này được bind vào contextvars qua `bind_contextvars(correlation_id=correlation_id)`, lưu vào `request.state.correlation_id` và trả ngược về client trong header `x-request-id` cùng `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** Ngay đầu endpoint `/chat` (`app/main.py`), các metadata ngữ cảnh được bind qua `bind_contextvars` gồm: `user_id_hash` (băm SHA256 lấy 12 ký tự), `session_id`, `feature`, `model`, `env`. Nhờ đó mọi log sau đó (`request_received`, `response_sent`, `request_failed`) đều tự động chứa đầy đủ các trường enrichment này.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor `scrub_event` được đăng ký vào pipeline `structlog` (`app/logging_config.py`) trước `JsonlFileProcessor` và `JSONRenderer`. Hàm `scrub_event` duyệt đệ quy tất cả các trường dữ liệu (ngoại trừ các key định danh hệ thống như `ts`, `level`, `service`, `correlation_id`, `user_id_hash`) và áp dụng regex (`app/pii.py`) để che các dạng PII gồm Email, Số điện thoại Việt Nam, CCCD 12 số, Thẻ tín dụng/ngân hàng thành `[REDACTED_<NAME>]` trước khi dữ liệu được serialize và ghi ra file/stdout.
- **Cách kiểm chứng kết quả:** Chạy `python scripts/validate_logs.py` đạt điểm số 100/100; toàn bộ 26/26 unit tests trong `python -m pytest` vượt qua kiểm tra, đảm bảo không có rò rỉ dữ liệu nhạy cảm và correlation ID được lan truyền xuyên suốt.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Dùng cặp API Key `LANGFUSE_PUBLIC_KEY` (`pk-lf-bfb6e4df...`) và `LANGFUSE_SECRET_KEY` thuộc đúng project cá nhân `day13-k4-l3a-02495` trên Langfuse Cloud (`https://cloud.langfuse.com`). Toàn bộ trace được gắn tag `["lab", feature, "claude-sonnet-4-5"]`, `environment="dev"`, `user_id` băm theo học viên, và hiển thị rõ tên project cá nhân trên giao diện Langfuse.
- **Cấu trúc root/retrieval/generation observations:** Mỗi request sinh ra trace có cấu trúc cây phân cấp (waterfall):
  - Root observation: `lab-agent-run` (loại `AGENT`, `capture_input=False`, `capture_output=False` để ngăn rò rỉ PII) đo lường toàn bộ thời gian xử lý request.
  - Child observation 1: `retrieval` (loại `RETRIEVER`, `capture_input=False`, `capture_output=False`) đo thời gian truy xuất tài liệu từ knowledge base, ghi nhận doc_count.
  - Child observation 2: `generation` (loại `GENERATION`, `capture_input=False`, `capture_output=False`) ghi nhận model `claude-sonnet-4-5`, usage tokens (`input`, `output`, `total`), chi phí `cost_usd`, và liên kết managed prompt qua `propagate_attributes(prompt=prompt.managed_prompt)`.
- **Cách nối trace với log:** Trong `app/middleware.py`, mỗi request sinh một `correlation_id` (định dạng `req-<8-hex>`). ID này được truyền vào `LabAgent.run(..., correlation_id=...)` và lưu vào metadata của trace (`metadata={"correlation_id": correlation_id}`). Khi có log bất thường trong `data/logs.jsonl`, chỉ cần lấy `correlation_id` tìm kiếm trên Langfuse để mở chính xác trace của request đó.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1 (label: `baseline`, ban đầu gắn cả `production`). Template: `Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}`.
- **Version/label candidate:** Version 2 (label: `candidate`). Template: `Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}\nPlease provide a concise answer based strictly on the retrieved docs.`.
- **Trace ID của mỗi version:**
  - Version 1 (`baseline`): `3925b7ba6df3514a07e6a75f6ac153e1` (và `06868b6a9879f3a8680bf9e98b4eed4f` sau rollback).
  - Version 2 (`candidate`): `9abad7c461856b4e6b46dadfdcc1eb58` (và `5575e5e9c1564661cc59d5f69d3d8f6c` khi promote).
- **Cách promote và rollback `production`:**
  - Promote: Cập nhật nhãn `production` sang Version 2 bằng lệnh `client.update_prompt(name='day13-chat', version=2, new_labels=['candidate', 'production'])` và cập nhật Version 1 còn nhãn `['baseline']`.
  - Rollback: Khi cần khôi phục version ổn định, cập nhật nhãn `production` về lại Version 1 bằng lệnh `client.update_prompt(name='day13-chat', version=1, new_labels=['baseline', 'production'])` và Version 2 về nhãn `['candidate']`. Cả hai lần đều được xác minh runtime qua trace log phản ánh đúng `prompt_version`.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dựng đúng 6 panel theo chuẩn `config/dashboard.yaml` sử dụng nguồn dữ liệu từ `data/logs.jsonl` với time range 60 phút, tự động refresh 30 giây:
  1. Latency percentiles and TTFT (P50, P95, P99, TTFT P95 - đơn vị ms, threshold P95 <= 3000ms).
  2. Request traffic (count, rate_per_minute - đơn vị req/phút, threshold >= 1).
  3. Error rate and retrieval success (error_rate_pct, count_by_value, tool_success_rate_pct - đơn vị %, threshold error rate <= 2%).
  4. Cost over time (sum_by_minute, total - đơn vị USD, threshold total <= 2.5$).
  5. Input and output tokens (tokens_in, tokens_out, sum_by_field - đơn vị tokens, threshold <= 50,000).
  6. Quality proxy (mean quality score - đơn vị 0.0 - 1.0, threshold mean >= 0.75).
- **SLO và lý do chọn:**
  - Primary SLO: `fast_successful_requests` với SLI: `event == "response_sent" and latency_ms <= 3000` trên tổng số `event == "request_received"` trong chu kỳ 28 ngày.
  - Mục tiêu: 99.5%.
  - Lý do chọn: Baseline bình thường có latency P95 ~400ms. Khi xảy ra sự cố suy giảm dịch vụ (như vector store timeout/chậm trong kịch bản `rag_slow`), latency tăng thêm 2.5s chạm ngưỡng ~2900 - 3100ms. Ngưỡng 3000ms giúp phát hiện chính xác sự cố suy thoái hiệu năng mà không gây ra báo động giả (alert fatigue).
- **Cách tính error budget:**
  - Error budget = 100% - 99.5% = 0.5% tổng số requests trong 28 ngày.
  - Ví dụ hệ thống nhận 100,000 requests trong 28 ngày, error budget cho phép tối đa 500 requests bị chậm (> 3000ms) hoặc thất bại. Khi số lượng vi phạm vượt quá 500, error budget bị cạn kiệt, kích hoạt quy trình đóng băng release và tập trung sửa chữa hạ tầng.
- **Ba alert và runbook tương ứng:**
  - Alert 1: `HighResponseLatencyP95` (Warning, condition: `p95(latency_ms) > 3000` trong 5 phút, kênh Slack, runbook: `docs/alerts.md#alert-1`) phát hiện suy giảm độ trễ phản hồi người dùng.
  - Alert 2: `HighAPIErrorRate` (Critical, condition: `error_rate_pct > 2%` trong 3 phút, kênh Slack, runbook: `docs/alerts.md#alert-2`) phát hiện tỷ lệ lỗi HTTP 500 tăng cao.
  - Alert 3: `DegradedAnswerQuality` (Warning, condition: `mean(quality_score) < 0.75 or tool_success_rate_pct < 90%` trong 10 phút, kênh Slack, runbook: `docs/alerts.md#alert-3`) phát hiện chất lượng câu trả lời bị suy giảm hoặc truy xuất tài liệu RAG thất bại.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** `2026-09-29 09:12:25Z – 09:12:40Z`
- **Triệu chứng từ metrics:** Độ trễ P95 tăng vọt từ ~168ms lên 3,455ms, vi phạm nghiêm trọng ngưỡng SLO (`p95 <= 3000ms`), trong khi error rate vẫn ở mức 0% và retrieval success rate đạt 100%. Các request trong kịch bản challenge đều bị chậm bất thường.
- **Log line và correlation ID liên quan:**
  - `correlation_id`: `req-a4c32886`
  - Log line trích xuất từ `data/logs.jsonl`:
    ```json
    {"service": "api", "latency_ms": 3455, "ttft_ms": 50, "tokens_in": 36, "tokens_out": 124, "cost_usd": 0.001968, "quality_score": 0.9, "tool_name": "retrieval", "tool_success": true, "payload": {"answer_preview": "Starter answer. You should improve this output logic and add better quality chec..."}, "event": "response_sent", "user_id_hash": "b2f6ef5394be", "feature": "monitoring", "env": "dev", "session_id": "k4-l3a-challenge-s01", "model": "claude-sonnet-4-5", "correlation_id": "req-a4c32886", "level": "info", "ts": "2026-09-29T09:12:29.026151Z"}
    ```
- **Trace ID và span gây ảnh hưởng:**
  - Trace ID: `c21a8411b84a0daf36243a5ef947029c` (thuộc project Langfuse `day13-k4-l3a-02495`).
  - Span gây ảnh hưởng: Child span `retrieval` (loại `RETRIEVER`) có thời gian thực thi lên tới 2.501s (chiếm 94.2% tổng thời gian request 3.456s), trong khi span `generation` chỉ mất 0.153s.
- **Root cause:** Thành phần truy xuất dữ liệu RAG (`retrieve()`) bị nghẽn độ trễ do incident `rag_slow` gây ra (mô phỏng vector store bị trễ 2.5s khi truy vấn tài liệu cho feature `monitoring`).
- **Fix action:**
  1. Tắt incident cờ `rag_slow` bằng lệnh `python scripts/inject_incident.py --disable`.
  2. Trong môi trường thực tế: Kiểm tra kết nối và chỉ mục của Vector Database (Pinecone/Milvus/Qdrant), scale-up tài nguyên read replica, hoặc kích hoạt semantic cache cho các truy vấn phổ biến.
- **Preventive measure:**
  1. Thiết lập timeout chặt chẽ cho bước retrieval (ví dụ: timeout 1.5s). Nếu quá thời gian, tự động fallback sang kết quả cache hoặc bộ tài liệu mặc định thay vì để toàn bộ request bị chậm kéo dài.
  2. Cấu hình Circuit Breaker cho vector store để cô lập lỗi khi database quá tải.
  3. Bật alert `HighResponseLatencyP95` (đã định nghĩa trong `config/alert_rules.yaml`) để đội On-call nhận thông báo ngay khi P95 vượt 3s liên tục trong 5 phút.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Đặt processor `scrub_event` trong `structlog.configure` trước `JsonlFileProcessor` và `JSONRenderer`. Quyết định này tuân thủ nguyên tắc Defense in Depth: ngay cả khi code logic của endpoint quên làm sạch dữ liệu đầu vào người dùng, toàn bộ log record vẫn được làm sạch tự động trước khi ghi ra đĩa hoặc serialize thành chuỗi JSON, đảm bảo không thể rò rỉ PII ra môi trường lưu trữ.
- **Một lỗi/blocker đã gặp:** Khi chạy `validate_logs.py` lần đầu sau khi sửa code, validator vẫn báo lỗi cũ do script đọc toàn bộ file `data/logs.jsonl` bao gồm các dòng log cũ được ghi từ trước khi triển khai PII scrubbing và enrichment.
- **Cách tìm nguyên nhân và xử lý:** Đọc kỹ hướng dẫn trong `docs/CHECKPOINTS.md` và `docs/GUIDE.md`: thực hiện sao lưu file log cũ thành `data/logs_baseline.jsonl` làm bằng chứng baseline, sau đó xóa `data/logs.jsonl`, khởi động lại API server và chạy lại workload để tạo log hoàn toàn mới.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  1. *Metrics*: Cung cấp góc nhìn vĩ mô (Aggregated View) để nhận biết triệu chứng (symptom) và khoảng thời gian xảy ra sự cố (ví dụ P95 latency vượt 3s lúc 09:12Z).
  2. *Logs*: Cung cấp góc nhìn vi mô (Event View) có ngữ cảnh, giúp lọc ra request cụ thể bị ảnh hưởng trong khoảng thời gian đó và lấy được `correlation_id` (ví dụ `req-a4c32886`).
  3. *Traces*: Cung cấp góc nhìn phân tán (Execution Waterfall View), dùng `correlation_id` mở trace waterfall để khoanh vùng chính xác span nào gây chậm (ví dụ span `retrieval` mất 2.5s trong khi span `generation` chỉ mất 0.15s).
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - *Prompt Versioning & Rollback*: Đảm bảo khả năng tái hiện (reproducibility) và an toàn khi thử nghiệm prompt mới; nếu prompt mới gây suy giảm chất lượng, có thể rollback nhãn `production` tức thì trên Langfuse về version trước mà không cần redeploy mã nguồn.
  - *Token & Cost Monitoring*: Giúp phát hiện sớm các hiện tượng chi phí bùng nổ (cost spike do prompt injection hoặc output token tăng đột biến), kiểm soát ngân sách vận hành mô hình.
  - *SLO & Error Budget*: Cung cấp thước đo chất lượng định lượng với người dùng, làm cơ sở quyết định khi nào được phép release tính năng mới và khi nào phải đóng băng để khắc phục sự cố.
- **Điều quan trọng nhất đã học:** Kỹ năng xây dựng hệ thống quan sát toàn diện (Observability) cho ứng dụng AI/LLM: từ việc thiết kế structured logging an toàn PII, gắn kết luồng Correlation ID, đến việc xây dựng cây quan sát cha-con (root, retrieval, generation) trên Langfuse để điều tra sự cố hiệu năng một cách có căn cứ khoa học.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Hệ thống hiện tại đang sử dụng Fake LLM và RAG giả lập trong khuôn khổ phòng lab; trong môi trường production thực tế, cần tích hợp thêm semantic cache cho RAG và streaming TTFT thực tế qua Server-Sent Events (SSE).

## 9. Checklist trước khi nộp

- [X] Kết quả và evidence thuộc commit SHA cuối.
- [X] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [X] Incident evidence nối đúng metric → log → trace.
- [X] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [X] Repository chạy lại được theo README.
- [X] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [X] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
