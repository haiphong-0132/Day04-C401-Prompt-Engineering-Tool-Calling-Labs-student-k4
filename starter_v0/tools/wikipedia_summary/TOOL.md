---
name: wikipedia_summary
description: "Dùng để tra cứu tóm tắt Wikipedia của một thực thể (người, địa danh, khái niệm). Tự động lấy đoạn mở đầu của bài viết."
---

# Wikipedia Summary Tool

Tool này lấy thông tin từ Wikipedia API (`https://en.wikipedia.org/api/rest_v1/page/summary/{title}`).
Rất hữu ích cho Research Agent để tra cứu khái niệm nhanh.

## Tham số
- `title` (string): Tiêu đề tiếng Anh của bài viết Wikipedia (ví dụ: 'Artificial_intelligence', 'Albert_Einstein').

## Lưu ý
Không cần API key. Nếu tiêu đề không chính xác, API có thể trả về lỗi 404. Lấy trường `extract` trong JSON.
