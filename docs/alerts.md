# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: HighResponseLatencyP95
- Severity: warning
- Duration: 5m
- Kênh thông báo: Slack (#alerts-llmops-k4-l3a)
- SLI/SLO liên quan: `primary_slo.fast_successful_requests` (latency_ms <= 3000ms)
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: Người dùng cảm thấy độ trễ cao, phản hồi chatbot bị treo hoặc quá chậm (> 3s).
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Latency trên dashboard để xác định thời điểm bắt đầu tăng và giá trị P50/P95/P99.
  2. Lọc `data/logs.jsonl` tìm các log sự kiện `response_sent` có `latency_ms > 3000`, trích xuất `correlation_id`.
  3. Mở Langfuse trace tương ứng với `correlation_id` để kiểm tra span waterfall xem độ trễ nằm ở span `retrieval` hay `generation`.
- Mitigation tạm thời:
  - Nếu span `retrieval` bị chậm: kiểm tra tình trạng vector store / RAG, kích hoạt fallback retrieval hoặc kiểm tra incident cờ `rag_slow`.
  - Nếu span `generation` bị chậm: kiểm tra tải model upstream hoặc kích hoạt rate limit tạm thời.
- Owner: LaiBaQuan-02495

## Alert 2

- Tên: HighAPIErrorRate
- Severity: critical
- Duration: 3m
- Kênh thông báo: Slack (#alerts-llmops-k4-l3a)
- SLI/SLO liên quan: Guardrail `error_rate_pct_max` (<= 2%)
- Điều kiện và thời gian duy trì: `error_rate_pct > 2%` liên tục trong 3 phút.
- Ảnh hưởng tới người dùng: Người dùng nhận lỗi 500 khi gửi tin nhắn, chatbot không trả lời được.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors trên dashboard để kiểm tra tỷ lệ lỗi và phân bố theo `error_type`.
  2. Lọc `data/logs.jsonl` theo `event == "request_failed"`, kiểm tra `payload.detail` và `error_type` (ví dụ `RuntimeError: Vector store timeout`).
  3. Tìm `correlation_id` của request lỗi và đối chiếu trace trên Langfuse để xem điểm ném exception.
- Mitigation tạm thời:
  - Nếu lỗi do tool/vector database (`tool_fail`): kích hoạt graceful degradation trả về câu trả lời tổng quát từ fallback documents thay vì trả về lỗi 500 cho người dùng.
  - Tắt cờ sự cố nếu đang bị ảnh hưởng bởi incident test (`/incidents/tool_fail/disable`).
- Owner: LaiBaQuan-02495

## Alert 3

- Tên: DegradedAnswerQuality
- Severity: warning
- Duration: 10m
- Kênh thông báo: Slack (#alerts-llmops-k4-l3a)
- SLI/SLO liên quan: Guardrail `quality_score_avg_min` (>= 0.75) và `retrieval_success_rate_pct_min` (>= 90%)
- Điều kiện và thời gian duy trì: `mean(quality_score) < 0.75` hoặc `tool_success_rate_pct < 90%` liên tục trong 10 phút.
- Ảnh hưởng tới người dùng: Chất lượng câu trả lời bị suy giảm, câu trả lời không liên quan hoặc chỉ chứa nội dung fallback do không tìm thấy tài liệu phù hợp.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel Quality trên dashboard và so sánh với threshold 0.75.
  2. Lọc `data/logs.jsonl` tìm các request có `quality_score < 0.7` để xem `feature`, `message_preview` và `answer_preview`.
  3. Mở Langfuse trace để kiểm tra version prompt đang chạy (`prompt_version`, `prompt_label`) và kết quả retrieval docs.
- Mitigation tạm thời:
  - Nếu chất lượng giảm sau khi release prompt candidate mới: thực hiện rollback prompt label `production` về version ổn định trước đó trên Langfuse.
  - Kiểm tra corpus dữ liệu xem có bị thiếu index hoặc query mới không khớp từ khóa hay không.
- Owner: LaiBaQuan-02495

