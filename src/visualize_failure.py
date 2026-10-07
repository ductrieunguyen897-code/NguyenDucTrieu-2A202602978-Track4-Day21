"""Tạo ảnh minh hoạ Failure Case cho Topic F: Vật bị che khuất nặng (Occlusion > 50%).

Chạy từ gốc repo:
    python -m src.visualize_failure
"""
from pathlib import Path

import cv2
import numpy as np

from starter.datasets import load_frame
from starter.projection import box3d_corners_cam, cam_to_image, velo_to_cam
from src.exp_autolabel import compute_iou, points_in_box_mask


def main() -> None:
    fr = load_frame("data/kitti_mini", "000011")
    img = fr["image"].copy()
    h_img, w_img = img.shape[:2]
    calib = fr["calib"]

    pts = fr["points"][np.isfinite(fr["points"]).all(axis=1)]
    cam_pts = velo_to_cam(pts[:, :3], calib)

    # Object 1 là Pedestrian bị che khuất mức 2 (occlusion = 2) ở cự ly 13.4m
    obj = fr["labels"][1]
    gt_bbox = [int(round(v)) for v in obj.bbox]

    # 1. 2D box từ 8 góc 3D
    corners = box3d_corners_cam(obj)
    uv_c, _, _ = cam_to_image(corners, calib.P2, (h_img, w_img))
    box_c = [
        int(round(uv_c[:, 0].min())),
        int(round(uv_c[:, 1].min())),
        int(round(uv_c[:, 0].max())),
        int(round(uv_c[:, 1].max())),
    ]
    iou_c = compute_iou(box_c, obj.bbox)

    # 2. 2D box từ điểm LiDAR trong 3D box
    in_3d = points_in_box_mask(cam_pts, obj)
    pts_in = cam_pts[in_3d]
    uv_p, _, _ = cam_to_image(pts_in, calib.P2, (h_img, w_img))
    box_p = [
        int(round(uv_p[:, 0].min())),
        int(round(uv_p[:, 1].min())),
        int(round(uv_p[:, 0].max())),
        int(round(uv_p[:, 1].max())),
    ]
    iou_p = compute_iou(box_p, obj.bbox)

    # Tạo panel crop phóng to (crop vùng xung quanh 2 người đi bộ)
    crop_x1 = max(0, gt_bbox[0] - 120)
    crop_y1 = max(0, gt_bbox[1] - 40)
    crop_x2 = min(w_img, gt_bbox[2] + 60)
    crop_y2 = min(h_img, gt_bbox[3] + 40)

    detail = img[crop_y1:crop_y2, crop_x1:crop_x2].copy()

    # Vẽ các điểm LiDAR lên detail crop
    for pt in uv_p:
        px = int(round(pt[0])) - crop_x1
        py = int(round(pt[1])) - crop_y1
        cv2.circle(detail, (px, py), 2, (0, 255, 255), -1)  # vàng

    # Tọa độ tương đối trên crop
    gt_c = (gt_bbox[0] - crop_x1, gt_bbox[1] - crop_y1, gt_bbox[2] - crop_x1, gt_bbox[3] - crop_y1)
    c_c = (box_c[0] - crop_x1, box_c[1] - crop_y1, box_c[2] - crop_x1, box_c[3] - crop_y1)
    p_c = (box_p[0] - crop_x1, box_p[1] - crop_y1, box_p[2] - crop_x1, box_p[3] - crop_y1)

    # Vẽ GT (Xanh lá)
    cv2.rectangle(detail, (gt_c[0], gt_c[1]), (gt_c[2], gt_c[3]), (0, 255, 0), 2)
    # Vẽ 3D Corner (Xanh dương)
    cv2.rectangle(detail, (c_c[0], c_c[1]), (c_c[2], c_c[3]), (255, 100, 0), 2)
    # Vẽ LiDAR Box (Đỏ)
    cv2.rectangle(detail, (p_c[0], p_c[1]), (p_c[2], p_c[3]), (0, 0, 255), 2)

    # Phóng to vùng detail để dễ quan sát (scale 2.5x)
    detail_scaled = cv2.resize(detail, (0, 0), fx=2.5, fy=2.5, interpolation=cv2.INTER_LINEAR)

    # Thêm bảng chú giải (Legend) trên detail
    cv2.putText(detail_scaled, f"GT BBox: [{gt_bbox[0]},{gt_bbox[1]},{gt_bbox[2]},{gt_bbox[3]}]",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
    cv2.putText(detail_scaled, f"3D Box Corners: IoU = {iou_c:.3f}",
                (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 150, 0), 2)
    cv2.putText(detail_scaled, f"LiDAR Points Box: IoU = {iou_p:.3f} (FAIL)",
                (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
    cv2.putText(detail_scaled, "Cause: Occluded > 50% by pedestrian in front",
                (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    # Tạo ảnh context toàn cảnh có vẽ ô đỏ chỉ vị trí zoom
    context = img.copy()
    cv2.rectangle(context, (crop_x1, crop_y1), (crop_x2, crop_y2), (0, 0, 255), 2)
    cv2.putText(context, "Failure Case: Pedestrian (occ=2)",
                (crop_x1 - 50, crop_y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Resize context cho vừa chiều cao với detail_scaled
    target_h = detail_scaled.shape[0]
    target_w = int(context.shape[1] * (target_h / context.shape[0]))
    context_resized = cv2.resize(context, (target_w, target_h))

    # Ghép ngang: Bên trái là ảnh toàn cảnh, bên phải là ảnh zoom chi tiết
    canvas = np.hstack([context_resized, detail_scaled])

    out_path = Path("results/figures/fail_01_occlusion_pedestrian.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), canvas)
    print(f"-> Đã lưu ảnh Failure Case: {out_path}")


if __name__ == "__main__":
    main()

