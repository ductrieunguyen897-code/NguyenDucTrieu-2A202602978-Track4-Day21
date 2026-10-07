"""Vẽ đồ thị kết quả thí nghiệm Auto-label cho Topic F.

Chạy từ gốc repo:
    python -m src.plot_autolabel
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Đọc kết quả benchmark
csv_path = Path("results/autolabel_iou_benchmark.csv")
if not csv_path.exists():
    raise FileNotFoundError(f"Chưa có file {csv_path}. Hãy chạy python -m src.exp_autolabel trước.")

df = pd.read_csv(csv_path, dtype={"frame": str})

# Thiết lập font và style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# =========================================================================
# Subplot 1: So sánh IoU giữa 2 phương pháp theo Mức độ che khuất (Occlusion)
# =========================================================================
df_base = df[df["yaw_deg"] == 0.0]
# Chỉ lấy các mức occlusion 0, 1, 2 (bỏ qua mức 3 không xác định)
df_occ = df_base[df_base["occluded"].isin([0, 1, 2])]
occ_group = df_occ.groupby("occluded")[["iou_corners", "iou_lidar"]].mean().reset_index()

x = np.arange(len(occ_group))
bar_width = 0.35

rects1 = ax1.bar(
    x - bar_width / 2,
    occ_group["iou_corners"],
    bar_width,
    label="Box từ 8 góc 3D",
    color="#4C72B0",
    edgecolor="black",
    linewidth=0.8,
)
rects2 = ax1.bar(
    x + bar_width / 2,
    occ_group["iou_lidar"],
    bar_width,
    label="Box từ điểm LiDAR",
    color="#DD8452",
    edgecolor="black",
    linewidth=0.8,
)

# Hiển thị giá trị trên đỉnh cột
for rect in rects1:
    h = rect.get_height()
    ax1.annotate(f"{h:.2f}",
                 xy=(rect.get_x() + rect.get_width() / 2, h),
                 xytext=(0, 3), textcoords="offset points",
                 ha="center", va="bottom", fontsize=9, fontweight="bold")
for rect in rects2:
    h = rect.get_height()
    ax1.annotate(f"{h:.2f}",
                 xy=(rect.get_x() + rect.get_width() / 2, h),
                 xytext=(0, 3), textcoords="offset points",
                 ha="center", va="bottom", fontsize=9, fontweight="bold")

ax1.set_xlabel("Mức độ che khuất (0: Nhìn rõ, 1: Che ≤ 50%, 2: Che > 50%)", fontsize=11)
ax1.set_ylabel("IoU trung bình với nhãn 2D Ground-Truth", fontsize=11)
ax1.set_title("So sánh IoU theo Mức độ che khuất (Yaw = 0°)", fontsize=12, fontweight="bold")
ax1.set_xticks(x)
ax1.set_xticklabels([f"Occlusion {int(o)}" for o in occ_group["occluded"]])
ax1.set_ylim(0, 1.15)
ax1.legend(loc="upper right", frameon=True)
ax1.grid(axis="y", linestyle="--", alpha=0.5)

# =========================================================================
# Subplot 2: Sự suy giảm IoU của điểm LiDAR khi Drift Calibration (Yaw sweep)
# =========================================================================
yaw_df = df.groupby(["frame", "yaw_deg"])["iou_lidar"].mean().reset_index()

markers = {"000001": "s", "000011": "o", "000031": "^"}
colors = {"000001": "#C44E52", "000011": "#55A868", "000031": "#8172B3"}

for frame, g in yaw_df.groupby("frame"):
    m = markers.get(frame, "o")
    c = colors.get(frame, "blue")
    ax2.plot(
        g["yaw_deg"],
        g["iou_lidar"],
        marker=m,
        markersize=7,
        linewidth=2,
        label=f"Frame {frame}",
        color=c,
    )

ax2.set_xlabel("Góc lệch calibration Yaw (độ)", fontsize=11)
ax2.set_ylabel("IoU trung bình của Box LiDAR", fontsize=11)
ax2.set_title("Độ nhạy của Auto-label LiDAR trước Lệch Yaw", fontsize=12, fontweight="bold")
ax2.set_ylim(0, 1.05)
ax2.set_xticks([0.0, 1.0, 2.0])
ax2.legend(loc="upper right", frameon=True)
ax2.grid(True, linestyle="--", alpha=0.5)

fig.tight_layout()

out_path = Path("results/figures/autolabel_iou_comparison.png")
out_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out_path, dpi=150)
print(f"-> Đã lưu biểu đồ: {out_path}")

