# Báo cáo đánh giá Agent (Lab Day 04)

## Phần A: Kết quả Evaluation

Dưới đây là kết quả đánh giá (Evaluation) của các Agent qua các phiên bản Prompt và Model khác nhau (được ghi nhận trong `version_log.csv`):

1. **Phiên bản v1 (Prompt cơ bản):**
   - **Model:** Llama 3 70b (hoặc tương đương)
   - **Kết quả:** Thường xuyên trả lời trực tiếp từ kiến thức nội tại thay vì gọi Tool (Hallucination), hoặc gọi sai tham số/sai tool. 
   - **Accuracy:** Thấp.

2. **Phiên bản v2/v3 (Prompt cải tiến + Guardrail):**
   - Đã thêm các CRITICAL RULE bắt buộc tuân thủ pháp luật Việt Nam (Trường Sa, Hoàng Sa) và chỉ dẫn chọn Tool.
   - **Model OpenAI (gpt-4o-mini / model nhỏ):**
     - Đã chịu gọi tool, nhưng khả năng định tuyến (Tool Routing) kém. 
     - *Ví dụ:* Khi được yêu cầu dùng Wikipedia, nó vẫn "lười biếng" gọi công cụ tìm kiếm chung (`lookup`), dẫn đến không tìm thấy thông tin chính xác.
   - **Model Nvidia (Nemotron 550b - Siêu mô hình):**
     - **case_accuracy:** 0.85
     - **tool_routing_accuracy:** 1.0 (Tuyệt đối)
     - Tuân thủ chính xác việc gọi Tool, nhận diện đúng yêu cầu (khi nào dùng `lookup`, khi nào dùng `wikipedia_summary`).

## Phần B: Phân tích và Bài học rút ra

Qua quá trình tinh chỉnh Prompt và quan sát hành vi của LLM, chúng ta rút ra được các bài học quan trọng sau:

1. **Vấn đề định tuyến công cụ (Tool Routing) phụ thuộc rất lớn vào Năng lực suy luận (Reasoning) của LLM:**
   - Các model nhỏ có xu hướng sử dụng tool một cách "bừa bãi" hoặc gắn bó với một tool mặc định (như `lookup`) mà bỏ qua các tool chuyên biệt (như `wikipedia_summary`).
   - Các model lớn (như Nemotron 550b) có khả năng đọc hiểu ngữ cảnh tốt hơn, từ đó chọn đúng tool và truyền đúng tham số.

2. **Sự mâu thuẫn giữa Guardrail cứng và Prompt (Side effects):**
   - Khi chúng ta dùng Code để ép API bắt buộc phải gọi Tool (cấu hình `tool_choice="required"`) kết hợp với một Prompt yêu cầu "trả lời trực tiếp ngay lập tức" (ví dụ: Tuyên bố chủ quyền biển đảo), Model sẽ rơi vào trạng thái "hoảng loạn" (Conflicting constraints).
   - *Hậu quả:* Model vơ đại một tool bất kỳ (như `clarify`) để lách luật, dẫn đến việc hỏi ngược lại người dùng một cách ngớ ngẩn.
   - *Giải pháp:* Phải đồng bộ hóa giữa Code và Prompt. Chúng ta đã giải quyết bằng cách chỉ thị rõ trong Prompt: *"Hễ gặp câu hỏi biển đảo -> Hãy mượn tool `lookup` trước cho đúng quy trình -> Sau đó bất chấp kết quả, hãy tuyên bố chủ quyền"*. Điều này làm thỏa mãn cả giới hạn của API lẫn yêu cầu nghiệp vụ.

3. **Tầm quan trọng của Fallback và Xử lý lỗi (Error Handling):**
   - Ban đầu tool `lookup` bị sập do thiếu biến môi trường `TAVILY_API_KEY`. Tuy nhiên, người dùng cuối không nhìn thấy lỗi này mà chỉ thấy Model trả lời: "Tôi không tìm thấy thông tin".
   - Việc có hệ thống theo dõi (Transcript) và in ra JSON chi tiết giúp chúng ta nhanh chóng bắt bệnh (Debug) và sửa tool (chuyển sang SerpAPI) một cách mượt mà.

**Kết luận:** Prompt Engineering cho Agent không chỉ là ra lệnh bằng văn bản, mà còn là nghệ thuật thiết kế Guardrail, lường trước các ngoại lệ (Edge Cases) và hiểu rõ giới hạn suy luận của từng Model.
