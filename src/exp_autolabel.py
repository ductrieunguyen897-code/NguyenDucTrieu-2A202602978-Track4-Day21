"""Topic F: Đánh giá phương pháp gợi ý 2D bounding box từ 3D box và điểm LiDAR.

So sánh 2 phương pháp auto-label 2D:
  1. Box từ 8 góc 3D box (box3d_corners_cam) chiếu lên ảnh.
  2. Box từ min-max hình chiếu các điểm LiDAR nằm trong 3D box.

Thí nghiệm khảo sát theo 3 mức độ che khuất (occlusion = 0, 1, 2)
và các mức lệch calibration yaw (0.0°, 1.0°, 2.0°).

Chạy từ gốc repo:
    python -m src.exp_autolabel --data-root data/kitti_mini --frames 000001 000011 000031
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from starter.datasets import load_frame
from starter.kitti_io import KittiObject
from starter.projection import (
    box3d_corners_cam,
    cam_to_image,
    perturb_extrinsic,
    velo_to_cam,
)

CLASSES = ("Car", "Van", "Truck", "Pedestrian", "Cyclist")


def points_in_box_mask(points_cam: np.ndarray, obj: KittiObject) -> np.ndarray:
    """Mask (N,) các điểm (trong camera frame) nằm trong 3D box của nhãn."""
    h, w, l = obj.dimensions
    c, s = np.cos(obj.rotation_y), np.sin(obj.rotation_y)
    R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    local = (points_cam - obj.location) @ R
    return (
        (np.abs(local[:, 0]) <= l / 2)
        & (local[:, 1] <= 0)
        & (local[:, 1] >= -h)
        & (np.abs(local[:, 2]) <= w / 2)
    )


def compute_iou(box_a: np.ndarray | list[float], box_b: np.ndarray | list[float]) -> float:
    """Tính Intersection over Union (IoU) giữa 2 bounding box dạng [x1, y1, x2, y2]."""
    xA = max(box_a[0], box_b[0])
    yA = max(box_a[1], box_b[1])
    xB = min(box_a[2], box_b[2])
    yB = min(box_a[3], box_b[3])

    inter_w = max(0.0, xB - xA)
    inter_h = max(0.0, yB - yA)
    inter_area = inter_w * inter_h

    area_a = max(0.0, box_a[2] - box_a[0]) * max(0.0, box_a[3] - box_a[1])
    area_b = max(0.0, box_b[2] - box_b[0]) * max(0.0, box_b[3] - box_b[1])
    union_area = area_a + area_b - inter_area

    if union_area <= 0:
        return 0.0
    return float(inter_area / union_area)


def clip_box(box: list[float] | np.ndarray, w: int, h: int) -> np.ndarray:
    """Kẹp bounding box vào biên ảnh [0, W-1] và [0, H-1]."""
    return np.array([
        max(0.0, min(float(w - 1), float(box[0]))),
        max(0.0, min(float(h - 1), float(box[1]))),
        max(0.0, min(float(w - 1), float(box[2]))),
        max(0.0, min(float(h - 1), float(box[3]))),
    ], dtype=np.float64)


def eval_frame(
    fr: dict,
    dataset_name: str,
    frame_id: str,
    yaw_deg: float = 0.0,
) -> list[dict]:
    """Đánh giá toàn bộ object trong frame theo 2 phương pháp tạo 2D box."""
    img_shape = fr["image"].shape
    h_img, w_img = img_shape[:2]

    # Lọc điểm hữu hạn
    pts_raw = fr["points"]
    finite_mask = np.isfinite(pts_raw).all(axis=1)
    pts = pts_raw[finite_mask]

    # Giả lập lệch yaw nếu có
    calib = perturb_extrinsic(fr["calib"], yaw_deg=yaw_deg) if yaw_deg != 0.0 else fr["calib"]

    # Điểm LiDAR ở rectified camera frame
    cam_pts = velo_to_cam(pts[:, :3], calib)

    rows = []
    for obj_idx, obj in enumerate(fr["labels"]):
        if obj.type not in CLASSES:
            continue

        dist_m = float(np.linalg.norm(obj.location))

        # --- Phương pháp 1: Chiếu 8 góc 3D box ---
        corners_3d = box3d_corners_cam(obj)
        uv_corners, _, mask_corners = cam_to_image(corners_3d, calib.P2, img_shape)
        if len(uv_corners) >= 2:
            raw_box_corners = [
                uv_corners[:, 0].min(),
                uv_corners[:, 1].min(),
                uv_corners[:, 0].max(),
                uv_corners[:, 1].max(),
            ]
            box_corners = clip_box(raw_box_corners, w_img, h_img)
            iou_corners = round(compute_iou(box_corners, obj.bbox), 4)
        else:
            iou_corners = 0.0

        # --- Phương pháp 2: Điểm LiDAR nằm trong 3D box ---
        in_3d = points_in_box_mask(cam_pts, obj)
        pts_in_box = cam_pts[in_3d]
        n_pts = len(pts_in_box)

        if n_pts > 0:
            uv_pts, _, mask_pts = cam_to_image(pts_in_box, calib.P2, img_shape)
            if len(uv_pts) > 0:
                raw_box_lidar = [
                    uv_pts[:, 0].min(),
                    uv_pts[:, 1].min(),
                    uv_pts[:, 0].max(),
                    uv_pts[:, 1].max(),
                ]
                box_lidar = clip_box(raw_box_lidar, w_img, h_img)
                iou_lidar = round(compute_iou(box_lidar, obj.bbox), 4)
            else:
                iou_lidar = 0.0
        else:
            iou_lidar = 0.0

        iou_diff = round(iou_lidar - iou_corners, 4)

        rows.append({
            "dataset": dataset_name,
            "frame": frame_id,
            "object_id": obj_idx,
            "type": obj.type,
            "occluded": int(obj.occluded),
            "truncated": round(float(obj.truncated), 2),
            "distance_m": round(dist_m, 2),
            "yaw_deg": yaw_deg,
            "n_lidar_points": n_pts,
            "iou_corners": iou_corners,
            "iou_lidar": iou_lidar,
            "iou_diff": iou_diff,
        })

    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Thí nghiệm đánh giá Auto-label 2D box cho Topic F")
    ap.add_argument("--data-root", default="data/kitti_mini", help="Đường dẫn thư mục dữ liệu")
    ap.add_argument("--frames", nargs="+", default=["000001", "000011", "000031"],
                    help="Danh sách các frame KITTI cần đánh giá")
    ap.add_argument("--yaw-levels", nargs="+", type=float, default=[0.0, 1.0, 2.0],
                    help="Các mức góc lệch yaw cần quét (độ)")
    ap.add_argument("--out", default="results/autolabel_iou_benchmark.csv",
                    help="Đường dẫn file kết quả CSV")
    ap.add_argument("--seed", type=int, default=42, help="Seed cố định")
    args = ap.parse_args()

    np.random.seed(args.seed)
    dataset_name = Path(args.data_root).name

    all_rows = []
    for frame_id in args.frames:
        fr = load_frame(args.data_root, frame_id)
        for yaw in args.yaw_levels:
            frame_rows = eval_frame(fr, dataset_name, frame_id, yaw_deg=yaw)
            all_rows.extend(frame_rows)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if all_rows:
        fieldnames = list(all_rows[0].keys())
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"Đã lưu kết quả ({len(all_rows)} dòng) -> {out_path}")
    else:
        print("Không tìm thấy đối tượng nào phù hợp.")


if __name__ == "__main__":
    main()

