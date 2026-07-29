# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 16:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team: Group 04 - Research Group
- Members: ToanTQ & Group Members
- Provider/model: OpenRouter / `openai/gpt-4o-mini`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent hỗ trợ tìm kiếm tin tức đa kênh, tra cứu bài báo khoa học, tra cứu bách khoa toàn thư Wikipedia đa ngôn ngữ, tóm tắt thông tin và thực hiện quy trình đăng/gửi bản tin an toàn (Telegram/Twitter) có qua bước xác nhận người dùng.

**Link dùng thử (truy cập được trong showdown):**

> Streamlit UI (Localhost / Private Network):
> URL: http://localhost:8501

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại người dùng để làm rõ thông tin thiếu hoặc xác nhận Yes/No trước hành động nhạy cảm | không |
| `wikipedia_search` | Tra cứu bài viết và tóm tắt nội dung trên Wikipedia theo ngôn ngữ (`en`, `vi`) | Có (Tool mới của nhóm) |
| `lookup` | Tra cứu tin tức trực tuyến theo từ khóa, chủ đề (topic) và khoảng thời gian (timeframe) | không |
| `read_url` | Đọc và trích xuất nội dung nguyên văn từ một liên kết URL | không |

## A3. Câu hỏi mẫu để thử

1. "Tóm tắt giúp mình bài viết Wikipedia tiếng Việt về Việt Nam trong 3 kết quả."
2. "Tìm cho tôi tin tức về trí tuệ nhân tạo tuần này."
3. "Đăng giúp mình bản tin tổng hợp này lên Telegram." *(Kiểm tra tính năng hỏi xác nhận Yes/No)*
4. "Tìm trên Wikipedia giúp mình." *(Kiểm tra khả năng hỏi làm rõ thông tin thiếu query)*

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| Tra cứu Wikipedia đơn giản | `wikipedia_search(query='GPT-4', lang='en', limit=3)` | v0 bị thiếu `lang` và `limit` mặc định; v3 bổ sung đầy đủ tham số chuẩn schema. | `runs/v3_B_group_openrouter_20260729T164345936429.json` |
| Tra cứu Wikipedia tiếng Việt thiếu query | Turn 1: `clarify(response_type='text')`<br>Turn 2: `wikipedia_search(query='Việt Nam', lang='vi', limit=3)` | v0 đoán đại từ khóa; v1+ ép buộc hỏi lại người dùng bằng `clarify` khi thiếu query. | `runs/v3_B_group_openrouter_20260729T164345936429.json` |
| Đăng tin nhạy cảm | `clarify(response_type='yes_no', question='...')` | v0 tự động gửi ngay; v2+ ép hỏi xác nhận Yes/No trước khi thực hiện side-effect. | `runs/v2_B_base_openrouter_20260729T161702266207.json` |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

Dữ liệu rút ra từ các file `runs/*.json` nằm trong thư mục `starter_v0/runs`. Bảng dưới đây tóm tắt các thay đổi prompt/tool, giả thuyết, và các metric quan trọng (case accuracy) dựa trên run files đã tạo.

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---:|---:|---:|---|
| v0 | Baseline initial prompt | Baseline model capability | Case Accuracy | N/A | 0.70 | `runs/v0_B_base_openrouter_20260729T150657706198.json` |
| v1 | Thêm rule cấm tự ý đăng bài, bắt buộc clarify khi thiếu thông tin | Ép agent hỏi xác nhận & làm rõ thông tin giúp tăng độ chính xác routing/boundary | Case Accuracy | 0.70 | 0.85 | `runs/v1_B_base_openrouter_20260729T160705911237.json` |
| v2 | Bổ sung mapping rule cho `lookup` (query + topic + timeframe) và thứ tự Yes/No trước Text | Cấu trúc tham số lookup chính xác hơn và đúng quy trình confirmation boundary | Case Accuracy | 0.85 | 0.90 | `runs/v2_B_base_openrouter_20260729T161702266207.json` |
| v3 | Cập nhật `system_prompt.md` & `tools.yaml` để bắt buộc truyền `lang`, `limit`, và explicit `summary` cho `wikipedia_search` (gồm special-case: khi user nhắc "Wikipedia" chỉ dùng `wikipedia_search`) | Ép truyền đủ tham số và quy tắc mapping/ngôn ngữ giúp giảm sai sót argument; tuy nhiên một lỗi multi-turn (query canonicalization) còn tồn tại và cần sửa tiếp | Case Accuracy | 0.90 | 0.90 | `runs/v3_B_group_openrouter_20260729T165857032171.json` |

## B2. Failure analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | unexpected_tool_call | `send_telegram(...)` | Agent tự ý gửi bài khi yêu cầu ngoài phạm vi | Cập nhật prompt từ chối thẳng và không gọi tool gửi bài |
| R10_missing_handle | missing_tool_call | `lookup(handle='samaltman')` | Agent tự đoán handle khi người dùng không cung cấp | Thêm rule trong `system_prompt.md` cấm đoán tài khoản, phải gọi `clarify` |
| W01_wikipedia_basic | wrong_arg_value | `wikipedia_search(query='GPT-4', summary=True)` | Thiếu `lang` ('en') và `limit` (3), truyền nhầm `summary` | Bổ sung schema trong `tools.yaml` & ép rule default args trong `system_prompt.md` |
| W02_wikipedia_lang_vi | wrong_arg_value | `wikipedia_search(query='Việt Nam', lang='vi')` | Omit giá trị `limit: 3` mặc định | Khai báo `required: [query, lang, limit]` trong `tools.yaml` |
| M04_wikipedia_missing_then_provide | missing_info / wrong_arg_value | `wikipedia_search(query='sóng hấp dẫn', lang='en', limit=3)` | User provided subject in Vietnamese then requested English results; agent did not canonicalize/translate the query to the target language (expected 'gravitational waves') | Added Translation/Canonicalization rule to `system_prompt.md`: when wikipedia_search.lang differs from the subject language, translate or canonicalize the query into the target language before calling the tool; if uncertain, call `clarify(response_type='text')` |

## B3. Team eval cases

List the 10 cases added to `data/eval_group.json`:

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| W01_wikipedia_basic | Single-turn: routing wikipedia_search với query từ chủ đề người dùng | `wikipedia_search(query="GPT-4", lang="en", limit=3)` | PASS |
| W02_wikipedia_lang_vi | Single-turn: mapping ngôn ngữ 'vi' khi có yêu cầu tiếng Việt | `wikipedia_search(query="Việt Nam", lang="vi", limit=3)` | PASS |
| W03_wikipedia_limit_arg | Single-turn: trích xuất giới hạn số lượng bài viết (limit=1) | `wikipedia_search(query="Machine Learning", lang="en", limit=1)` | PASS |
| W04_wikipedia_missing_query | Single-turn: thiếu chủ đề phải gọi clarify(response_type="text") | `clarify(response_type="text")` | PASS |
| W05_wikipedia_unnecessary | Single-turn: câu hỏi meta về agent không được gọi tool | `answer_without_tool` | PASS |
| M01_wikipedia_carry_lang | Multi-turn: giữ ngữ cảnh ngôn ngữ 'vi' và giới hạn limit=2 qua các lượt | `wikipedia_search(query="ChatGPT", lang="vi", limit=2)` | PASS |
| M02_wikipedia_clarify_then_search | Multi-turn: làm rõ chủ đề ở turn 2 và tham số ở turn 3 | `wikipedia_search(query="quantum computing", lang="en", limit=1)` | PASS |
| M03_wikipedia_limit_change | Multi-turn: giữ chủ đề và điều chỉnh limit từ 5 xuống 2 | `wikipedia_search(query="trí tuệ nhân tạo", lang="vi", limit=2)` | PASS |
| M04_wikipedia_missing_then_provide | Multi-turn: bổ sung thông tin thiếu theo từng lượt chat | `wikipedia_search(query="gravitational waves", lang="en", limit=3)` | FAIL (observed in v3; fixed by prompt edit, re-run planned) |
| M05_wikipedia_no_tool_meta | Multi-turn: hỏi về khả năng truy cập Wikipedia không gọi tool | `answer_without_tool` | PASS |

## B4. Live chat evidence

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| Turn 1: "Tìm bài Wikipedia về ChatGPT" | v3 | `wikipedia_search(query="ChatGPT", lang="en", limit=3)` | `transcripts/m01_session.json` | Trả về thông tin tra cứu thành công |
| Turn 2: "Bằng tiếng Việt nhé" | v3 | `wikipedia_search(query="ChatGPT", lang="vi", limit=3)` | `transcripts/m01_session.json` | Cập nhật tham số `lang='vi'` chính xác |
| Turn 3: "Cho 2 kết quả thôi" | v3 | `wikipedia_search(query="ChatGPT", lang="vi", limit=2)` | `transcripts/m01_session.json` | Kết hợp đầy đủ context các turn trước |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên | `tools/wikipedia.py` | Tra cứu bài viết Wikipedia đa ngôn ngữ, lấy tóm tắt ngắn qua MediaWiki API | HTTP 403 do MediaWiki chặn bot -> Thêm `User-Agent` header chuẩn |
| Optional built-in | `tools/lookup.py` | Tìm kiếm tin tức theo topic và timeframe | Kết quả trả về trống nếu query quá hẹp |
| Bonus: tool mới thứ 4 trở đi | N/A | N/A | N/A |

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?**: Các quy tắc xử lý hội thoại đa lượt (multi-turn context carryover), quy tắc ưu tiên xác nhận Yes/No trước khi xin thông tin chi tiết, và cấm tự ý phỏng đoán (guessing) khi thông tin bị thiếu.
- **Which fixes belonged in `tools.yaml`?**: Việc định nghĩa rõ ràng danh sách tham số `required` (`query`, `lang`, `limit`), mô tả chi tiết kiểu dữ liệu và giá trị mặc định (`default`) cho từng tham số của tool.
- **Which failure needed manual review instead of automatic grading?**: Các lỗi 403 Client Error (HTTPForbidden) phát sinh từ API phía bên ngoài (MediaWiki API). Mặc dù agent routing và trích xuất tham số đúng (Routing PASS), nhưng tool execution thất bại do thiếu HTTP Header `User-Agent`.
- **What would you improve next?**: Thêm cơ chế tự động thử lại (retry mechanism) với fallback ngôn ngữ khi không tìm thấy kết quả trên Wikipedia tiếng Việt, đồng thời tích hợp thêm bộ nhớ đệm (caching) kết quả tra cứu.