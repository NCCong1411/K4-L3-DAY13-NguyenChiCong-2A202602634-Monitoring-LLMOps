# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Chí Công
- **MSSV:** 2A202602634
- **Lớp:** K4-L3A
- **Repository URL:** [https://github.com/NCCong1411/K4-L3-DAY13-NguyenChiCong-2A202602634-Monitoring-LLMOps.git](https://github.com/NCCong1411/K4-L3-DAY13-NguyenChiCong-2A202602634-Monitoring-LLMOps.git)
- **Commit SHA cuối:** `0fc35418aedfaf8f3af546262234ed996b737735`
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602634`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence            | Đường dẫn                             |
| ------------------- | ------------------------------------- |
| Pytest cuối         | `evidence/01-pytest.png`              |
| Log validator       | `evidence/02-log-validator.png`       |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log      | `evidence/04-structured-log.png`      |
| PII redaction       | `evidence/05-pii-redaction.png`       |
| Trace list          | `evidence/06-trace-list.png`          |
| Trace waterfall     | `evidence/07-trace-waterfall.png`     |
| Trace metadata      | `evidence/08-trace-metadata.png`      |
| Prompt versions     | `evidence/09-prompt-versions.png`     |
| Prompt rollback     | `evidence/10-prompt-rollback.png`     |
| Dashboard runtime   | `evidence/11-dashboard-overview.png`  |
| Incident metric     | `evidence/12-incident-metric.png`     |
| Incident log        | `evidence/13-incident-log.png`        |
| Incident trace      | `evidence/14-incident-trace.png`      |

## 3. Kết quả kỹ thuật

| Nội dung                | Baseline          | Kết quả cuối      | Nhận xét                                       |
| ----------------------- | ----------------- | ----------------- | ---------------------------------------------- |
| `validate_logs.py`      | 30/100            | 100/100           | CP1 workload sau khi làm sạch baseline log     |
| `validate_dashboard.py` | HỢP LỆ: 6/6 panel | HỢP LỆ: 6/6 panel | CP2 dashboard contract                         |
| `pytest`                | 22 passed         | 23 passed         | CP2 checks passed                              |
| Số traces hợp lệ        |                   | 80 root traces    | Evidence 06, Langfuse Tracing lọc `isRootObservation:true` |
| Số PII leak             |                   | 0                 | `validate_logs.py`                             |
| Latency P95 / TTFT P95  |                   | 2664 ms / 51 ms   | Dashboard runtime, cửa sổ 60 phút              |
| Retrieval success rate  |                   | 100%              | Dashboard runtime                              |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware dùng `x-request-id` nếu có, nếu không sinh `req-<8-hex>`, bind vào context và trả lại qua response header.
- **Các metadata được ghi vào structured log:** `user_id_hash`, `session_id`, `feature`, `model`, `env` và `correlation_id`.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` chạy trước JSON renderer và file writer.
- **Cách kiểm chứng kết quả:** Chạy workload mới sau khi đổi tên log baseline; `validate_logs.py` đạt 100/100.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Dùng project Langfuse cá nhân `day13-k4-l3a-2A202602634`, lọc `isRootObservation:true`; evidence 06 hiển thị 80 root traces.
- **Cấu trúc root/retrieval/generation observations:** `lab-agent-run` → `retrieve-documents` → `generate-answer`.
- **Cách nối trace với log:** Dùng trường `correlation_id` có trong metadata trace và structured log.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** Version 1, label `baseline`.
- **Version/label candidate:** Version 2, label `candidate`.
- **Trace ID của mỗi version:** Baseline V1: `4c66ba9e9f2ccffe7fb2656930d4c568`; Candidate V2: `ccc92c16e36b1affce61bdb2edd45b49`; Production V2 sau promote: `06f1258b74f1be3467e5d1d65d7e5f77` (`prompt_name=day13-chat`, `prompt_label=production`, `prompt_version=2`).
- **Cách promote và rollback `production`:** Đã chuyển `production` sang V2, chạy workload với label production, sau đó chuyển `production` lại V1; evidence tại `evidence/10-prompt-rollback.png`.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Runtime dashboard ở `/dashboard`, đọc `data/logs.jsonl` trong cửa sổ 60 phút và tự refresh mỗi 30 giây. Sáu panel là latency/TTFT, traffic, errors/retrieval success, cost, tokens và quality.
- **SLO và lý do chọn:** `fast_successful_requests` đặt mục tiêu 99.5% request có latency không quá 3,000 ms trong 28 ngày; ngưỡng này khớp panel latency.
- **Cách tính error budget:** 100% - 99.5% = 0.5%, tương đương tối đa 5 request không đạt trên mỗi 1,000 request.
- **Ba alert và runbook tương ứng:** `high_p95_latency` (warning, 5m), `elevated_error_rate` (critical, 5m), `low_quality_proxy` (warning, 15m); gửi Slack `#llmops-alerts`, owner `llmops-oncall`, runbook tại `docs/alerts.md`.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`.
- **Khoảng thời gian điều tra:** 2026-09-29 10:54:36–10:54:47 UTC.
- **Triệu chứng từ metrics:** Latency P95 là 2,664 ms trong dashboard runtime; năm request challenge đều có latency xấp xỉ 2.65 giây, trong khi error rate là 0% và retrieval success là 100%.
- **Log line và correlation ID liên quan:** `response_sent` có `correlation_id=req-e199cbbb`, `latency_ms=2653`, `ttft_ms=50`, `tool_success=true`.
- **Trace ID và span gây ảnh hưởng:** Trace `ca72ac8723f095560914a5e1ce41e22f`; `retrieve-documents` (retriever) mất khoảng 2,502 ms, trong khi `generate-answer` chỉ khoảng 152 ms.
- **Root cause:** Retrieval/RAG bị chậm, làm tăng end-to-end latency; không phải lỗi generation hoặc request failure.
- **Fix action:** Đặt timeout và cache cho retrieval, giới hạn số document/top-k, sau đó chạy lại workload để xác nhận P95 giảm.
- **Preventive measure:** Theo dõi P95 latency và retrieval success bằng alert `high_p95_latency`; runbook yêu cầu lấy correlation ID rồi so sánh retrieval/generation spans trước khi mitigation.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Tách `retrieve-documents` thành observation loại `retriever` và `generate-answer` thành `generation`. Nhờ span tree, có thể so sánh trực tiếp thời gian retrieval và generation thay vì chỉ biết latency tổng của request.
- **Một lỗi/blocker đã gặp:** Lần đầu tải managed prompt từ Langfuse bị timeout trong giai đoạn TLS, khiến trace ghi `local-fallback` và không dùng được làm evidence prompt version.
- **Cách tìm nguyên nhân và xử lý:** Kiểm tra `prompt_source` trong trace, xác nhận key/base URL/prompt label đúng, rồi dùng timeout tải prompt có thể cấu hình trong `.env` và chạy lại workload. Trace mới ghi `prompt_source=langfuse`, version và label đúng.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics cho biết P95 latency tăng trong khoảng incident. Log lọc theo khoảng đó cung cấp `correlation_id=req-e199cbbb`. Trace cùng correlation ID cho thấy `retrieve-documents` khoảng 2,502 ms, còn `generate-answer` khoảng 152 ms, từ đó khoanh vùng retrieval/RAG là nguyên nhân.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt version/label cho phép truy xuất request đã dùng template nào và rollback `production` an toàn. Token/cost giúp theo dõi chi phí theo workload; SLO và alert giúp phát hiện triệu chứng trước khi điều tra trace.
- **Điều quan trọng nhất đã học:** Không kết luận nguyên nhân chỉ từ dashboard. Cần nối cùng một request qua metric, structured log và trace để có kết luận có thể kiểm chứng.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Fake LLM và quality proxy chỉ mô phỏng vận hành; chất lượng thực tế vẫn cần thêm feedback/evaluation của người dùng trong môi trường production.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
