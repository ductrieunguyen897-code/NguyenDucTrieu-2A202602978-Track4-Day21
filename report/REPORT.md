# Báo cáo Day 6: Đánh giá Auto-label 2D Bounding Box từ LiDAR và 3D Box

> Thay **mọi** ô có chữ ĐIỀN nằm trong ngoặc vuông bằng nội dung của bạn, xoá luôn cả dấu ngoặc vuông. Lệnh `python tools/check_submission.py` sẽ báo FAIL nếu còn sót bất kỳ chỗ nào.

- **Họ tên:** Nguyễn Đức Triệu
- **MSSV:** 2A202602978 (phải trùng với MSSV trong tên repo `<HoVaTen>-<MSSV>-Track4-Day21`)
- **Lớp:** AI20K-T4
- **Link repo:** https://github.com/ductrieunguyen897-code/NguyenDucTrieu-2A202602978-Track4-Day21
- **Topic:** F — Auto-label
- **Dataset:** data/kitti_mini
- **Các frame đã dùng:** 000011, 000001, 000031 

> Hãy viết ngắn: mỗi mục từ 3 đến 8 dòng, ưu tiên số liệu và hình ảnh.

## 1. Claim

Một câu khẳng định kỹ thuật có thể kiểm chứng. Ví dụ: *"Lệch yaw 1° làm 12% điểm LiDAR rơi ra khỏi vật thể ở 30 m, phát hiện được bằng edge-alignment score với ngưỡng X."*

Đối với các vật thể có độ che khuất không quá 50% (occlusion ≤ 1 trong KITTI), 2D bounding box tạo từ min-max hình chiếu các điểm LiDAR nằm trong 3D box đạt IoU trung bình với nhãn ground-truth 2D cao hơn so với 2D box tạo từ hình chiếu 8 góc của 3D box (tránh được việc box bị phình to do hiệu ứng phối cảnh 3D sang 2D); tuy nhiên ưu thế này mất đi khi vật thể bị che khuất trên 50% (occlusion = 2) do điểm LiDAR chỉ thu được bề mặt phản xạ nhìn thấy, dẫn đến box dự đoán bị co hẹp so với thực tế.

## 2. Evidence

Bảng hoặc plot số liệu, kèm ảnh/video demo. Ghi rõ đường dẫn file trong `results/`.

| Cấu hình / mức perturb | Metric 1 | Metric 2 | Ghi chú |
|---|---|---|---|
| [ĐIỀN] | | | |

![demo](../results/figures/[ĐIỀN].png)

## 3. Failure case

Nêu khi nào hệ thống hoặc phương pháp fail, vì sao fail, và liên hệ tới lớp nào trong 6 lớp debug: I/O, Geometry, Time, Preprocess, Model, Metric.

![failure](../results/figures/fail_[ĐIỀN].png)

[ĐIỀN]

## 4. Khuyến nghị nếu triển khai thật

Use-case cụ thể (ADAS / robot / drone), trade-off và bước tiếp theo.

[ĐIỀN]

## 5. Cách chạy lại

Các lệnh tái tạo lại toàn bộ kết quả từ repo sạch.

```bash
[ĐIỀN]
```

## 6. Khai báo sử dụng AI

Ghi rõ đã dùng công cụ AI nào, dùng vào việc gì, và bạn đã tự kiểm chứng kết quả đó bằng cách nào. Nếu không dùng AI, ghi "Không sử dụng". Xem quy định ở `RULES.md` mục 2.

| Công cụ | Dùng cho việc gì | Bạn đã kiểm chứng thế nào |
|---|---|---|
| [ĐIỀN] | | |
