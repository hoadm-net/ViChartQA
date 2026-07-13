# 06 — Chiến lược công bố & thời hạn

## Hệ thống review

Các hội nghị *ACL chính (ACL, EMNLP, NAACL, EACL) dùng ACL Rolling Review (ARR) — nộp vào một chu kỳ ARR, sau đó cam kết (commit) bài đã review vào một hội nghị cụ thể.

## Xếp hạng venue (CORE)

| Hội nghị | Xếp hạng CORE | Đạt mục tiêu A*? |
|---|---|---|
| ACL | A* | ✅ |
| EMNLP | A* | ✅ |
| NAACL | A | ❌ |
| EACL | A | ❌ |

Chỉ ACL và EMNLP đạt A* trong dòng *ACL. Bài phải được cam kết vào ACL hoặc EMNLP.

## Các chu kỳ ARR

| Chu kỳ ARR | Hạn nộp | Hội nghị nhận cam kết | Xếp hạng | Khả thi |
|---|---|---|---|---|
| Tháng 3/2026 | 16/03/2026 | — | — | Đã đóng |
| Tháng 5/2026 | 25/05/2026 | EMNLP 2026, AACL 2026 | A* (EMNLP) | Đã đóng |
| Tháng 8/2026 | 03/08/2026 | EACL 2027 (chu kỳ duy nhất cho EACL 2027) | A | Loại — quá gấp, không đạt A* |
| Tháng 10/2026 | 12/10/2026 | Nhiều khả năng NAACL 2027 (chưa xác nhận chính thức) | A nếu đúng NAACL | Không phải lựa chọn A* mặc định |
| *(chưa công bố)* | *(ACL thường dùng chu kỳ ~tháng 12–1)* | ACL 2027 | A* | Cơ hội A* thực tế duy nhất — CFP chưa mở, cần theo dõi |

## Ba phương án

1. **Chờ chu kỳ ARR dẫn tới ACL 2027** (dự kiến ~12/2026–1/2027, theo pattern ACL 2026 hạn 05/01/2026) — con đường A* rõ ràng nhất, buffer ~4–5 tháng sau lịch 7 tuần ở [docs/05](05-timeline-and-roles.md).
2. **Nộp chu kỳ 10/2026 vào NAACL 2027** nếu đúng là venue nhận cam kết — chấp nhận hạng A thay vì A*.
3. **Kết hợp:** nộp chu kỳ 10/2026 (an toàn thời gian) + song song chuẩn bị bản mở rộng nhắm ACL 2027.

Theo dõi [aclrollingreview.org/dates](https://aclrollingreview.org/dates) và CFP ACL 2027 định kỳ trước khi chốt.

## Kênh phụ

VLSP (workshop tiếng Việt, CFP dự kiến Q3/2026) — không phải A*, dùng để công bố sớm bản resource paper rút gọn hoặc đề xuất shared task, chạy song song không trì hoãn timeline ARR.

## Yêu cầu định dạng bài báo A*

Chuẩn bị dần trong lúc annotation/fine-tune:

- Data Statement / Ethics Considerations — từng nguồn dữ liệu, điều khoản sử dụng, đối xử annotator. Bắt đầu từ [docs/02](02-dataset-design.md#nguồn-dữ-liệu).
- Limitations section — quy mô, phạm vi miền, khả năng khái quát hoá.
- Reproducibility checklist — hyperparameter, phần cứng, license backbone.
- Dataset card (Hugging Face Datasets) — taxonomy, chart type, domain, split sizes.

## Gói công bố kèm bài báo

- Dataset trên Hugging Face Hub (ảnh + JSON theo [docs/02](02-dataset-design.md#schema-dữ-liệu-đề-xuất)).
- Model checkpoint (LoRA adapter tối thiểu) kèm model card.
- Code fine-tune + eval harness trên GitHub.

## Checklist trước khi nộp ARR

- [ ] Xác nhận venue commitment chính xác của chu kỳ định nộp
- [ ] Quyết định rõ giữa 3 phương án ở trên
- [ ] Data Statement/Ethics Considerations hoàn chỉnh
- [ ] Limitations section trung thực
- [ ] Dataset + model sẵn sàng publish
- [ ] Số liệu trong bài đối chiếu lại với log thí nghiệm thực tế
