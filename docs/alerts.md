# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: high_p95_latency
- Severity: warning
- Duration: 5m
- Kênh thông báo: Slack `#llmops-alerts`
- SLI/SLO liên quan: fast_successful_requests, P95 latency <= 3000 ms
- Điều kiện và thời gian duy trì: P95 `latency_ms` > 3000 ms trong 5 phút.
- Ảnh hưởng tới người dùng: phản hồi chậm, đặc biệt ở tail latency.
- Ba bước kiểm tra đầu tiên: kiểm tra panel latency; lọc log `response_sent` chậm để lấy `correlation_id`; mở trace cùng correlation ID và so sánh retrieval/generation spans.
- Mitigation tạm thời: giảm traffic không thiết yếu hoặc tắt feature gây chậm sau khi xác nhận nguyên nhân.
- Owner: llmops-oncall

## Alert 2

- Tên: elevated_error_rate
- Severity: critical
- Duration: 5m
- Kênh thông báo: Slack `#llmops-alerts`
- SLI/SLO liên quan: error_rate_pct <= 2%
- Điều kiện và thời gian duy trì: error rate > 2% trong 5 phút.
- Ảnh hưởng tới người dùng: request thất bại hoặc không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên: kiểm tra panel errors; lọc `request_failed` và `error_type`; dùng `correlation_id` để mở trace và xác định span lỗi.
- Mitigation tạm thời: rollback cấu hình hoặc tắt feature lỗi sau khi xác nhận nguyên nhân.
- Owner: llmops-oncall

## Alert 3

- Tên: low_quality_proxy
- Severity: warning
- Duration: 15m
- Kênh thông báo: Slack `#llmops-alerts`
- SLI/SLO liên quan: quality_score average >= 0.75
- Điều kiện và thời gian duy trì: trung bình `quality_score` < 0.75 trong 15 phút.
- Ảnh hưởng tới người dùng: câu trả lời có thể không hữu ích dù request vẫn thành công.
- Ba bước kiểm tra đầu tiên: kiểm tra panel quality; lọc log response có quality thấp; mở trace cùng `correlation_id` để kiểm tra retrieval, generation và prompt version.
- Mitigation tạm thời: rollback label prompt `production` về version đã xác nhận hoặc giảm feature bị ảnh hưởng.
- Owner: llmops-oncall
