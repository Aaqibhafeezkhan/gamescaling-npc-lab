"""Collect every finished evaluation into one comparison table.

    python ue5/tools/summarize.py

Reads every eval.json under output/ue5-eval/ -- both the `colmap-<session>` runs
(features, matching and mapping together) and the `map-<session>-<arm>` runs (only
the mapper, on a filtered match graph) -- and prints a markdown table plus a JSON
copy, so the numbers quoted in documents come from files rather than memory.

The `arm` column matters: the same session appears several times with different
match graphs, and comparing them is the whole point. Numbers are only ever attached
to the directory they were written in, never matched across arms by session name.
"""

import json
from pathlib import Path

COLUMNS = [
    ("session", "会话"),
    ("arm", "匹配图"),
    ("registered_of_truth", "注册/真值"),
    ("coverage", "覆盖率"),
    ("ate_rmse_m", "ATE RMSE (m)"),
    ("ate_relative_percent", "相对误差 (%)"),
    ("points3d", "三维点"),
    ("label_recall", "标牌重建率"),
    ("label_plane_median_m", "地图误差中位 (m)"),
    ("depth_ratio", "深度/轴距"),
    ("vo_ate_m", "VO ATE (m)"),
    ("vo_rigid_ate_m", "VO 米制 ATE (m)"),
]

SIDECARS = [
    ("landmark_eval.json", "label_recall"),
    ("depth_points_check.json", "depth_ratio"),
    ("vo_eval.json", "vo_ate_m"),
]


def sidecar(directory, name):
    for candidate in (directory / name, directory / "best" / name):
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    return None


def enrich(row, directory, session):
    landmarks = sidecar(directory, "landmark_eval.json")
    if landmarks:
        row["label_recall"] = landmarks.get("label_recall")
        row["label_plane_median_m"] = landmarks.get(
            "perpendicular_to_label_plane_m", {}).get("median")

    depth = sidecar(directory, "depth_points_check.json")
    if depth:
        row["depth_ratio"] = depth.get("measured_over_axis_median")

    vo = sidecar(directory, "vo_eval.json")
    if vo:
        row["vo_ate_m"] = vo.get("ate_rmse_m")
        row["vo_rigid_ate_m"] = vo.get("ate_rigid_rmse_m")
    return row


def arm_of(directory):
    """Describe the matching graph a run used, from its directory name."""
    name = directory.name
    if name.startswith("map-"):
        # map-<session>-<arm>; the session itself may contain dashes. A mapper run may
        # record a clearer label of its own.
        summary = directory / "summary.json"
        if summary.exists():
            label = json.loads(summary.read_text(encoding="utf-8")).get("arm")
            if label:
                return label
        return name.rsplit("-", 1)[-1]
    if name.startswith("colmap-"):
        # Older runs predate the "matching" field of summary.json; the field was
        # backfilled from the database itself (exhaustive writes a row for every pair).
        summary = directory / "summary.json"
        if summary.exists():
            matching = json.loads(summary.read_text(encoding="utf-8")).get("matching")
            if matching:
                return matching
        return "colmap (未记录)"
    return name


def main() -> int:
    root = Path("output/ue5-eval")
    candidates = []
    for pattern in ("colmap-*/eval.json", "map-*/eval.json"):
        candidates += sorted(root.glob(pattern))

    rows = []
    for eval_path in candidates:
        data = json.loads(eval_path.read_text(encoding="utf-8"))
        directory = eval_path.parent
        row = dict(data)
        row["arm"] = arm_of(directory)
        row["eval_path"] = str(eval_path)
        rows.append(enrich(row, directory, data.get("session")))

    if not rows:
        print("no eval.json files yet; run run_colmap.py and evaluate_slam.py first")
        return 1

    order = {"city-04": 0, "city-02": 1, "city-03": 2, "city-lap2": 3}
    rows.sort(key=lambda row: (order.get(row.get("session"), 99), row.get("arm", "")))

    header = "| " + " | ".join(label for _, label in COLUMNS) + " |"
    divider = "|" + "|".join("---" for _ in COLUMNS) + "|"
    lines = [header, divider]
    for row in rows:
        cells = []
        for key, _ in COLUMNS:
            value = row.get(key, "")
            if value is None:
                value = "-"
            if isinstance(value, float):
                value = f"{value:.4g}"
            cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")

    table = "\n".join(lines)
    print(table)

    dense = dense_table(root)
    payload = table + "\n"
    if dense:
        payload += "\n## 稠密地图（深度融合）\n\n" + dense + "\n"
        payload += ("\ncolmap 的厚度在原生米制地图上计算；标牌评分在融合完成后做 Sim(3) 对齐，"
                    "米制刚体对齐结果另见 dense_eval.json。真值融合行是算法上限对照。\n"
                    "同帧 gt 对照只使用 COLMAP 实际融合的帧；旧版 VO 的真值对齐发生在融合前，已单独标注。\n")
        print("\n" + dense)

    out = root / "comparison.md"
    out.write_text(payload, encoding="utf-8")
    (root / "comparison.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\n{len(rows)} runs written to {out}")
    return 0


DENSE_COLUMNS = [
    ("session", "会话"),
    ("run", "运行"),
    ("pose_source", "位姿来源"),
    ("frames", "融合帧/真值"),
    ("coverage", "覆盖率"),
    ("voxel_m", "体素边长 (m)"),
    ("voxels", "体素数"),
    ("observations_per_voxel", "每体素观测"),
    ("thickness", "表面厚度中位 (m)"),
    ("label_recall", "标牌命中 (0.5 m)"),
    ("plane", "标牌平面误差中位 (m)"),
    ("alignment", "位姿对齐 RMSE (m)"),
    ("truth_usage", "真值使用范围"),
]


def dense_table(root):
    """Dense maps are scored by their own tool, so they get their own table."""
    rows = []
    paths = sorted(root.glob("dense-*/dense_eval.json"))
    control = root / 'regression/city-lap2-gt-matched/dense_eval.json'
    if control.exists():
        paths.append(control)
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        frames = data.get('frames_of_truth')
        coverage = data.get('coverage')
        if frames is None:
            # Historical reports predate coverage fields. Only backfill counts,
            # never infer accuracy or associate results across matching arms.
            truth_path = Path('output/ue5-datasets') / data['session'] / 'poses.jsonl'
            if truth_path.exists():
                total = sum(bool(line.strip()) for line in truth_path.read_text(encoding='utf-8').splitlines())
                frames = f"{data['frames_used']}/{total}"
                coverage = round(data['frames_used'] / total, 4) if total else None
        usage = data.get('ground_truth_usage')
        if usage is None:
            usage = 'oracle fusion reference' if data.get('pose_source') == 'gt' else 'legacy: truth alignment before fusion'
        usage = {
            'oracle fusion reference': '真值融合上限',
            'post-fusion evaluation only': '仅融合后评测',
            'legacy: truth alignment before fusion': '旧版：融合前真值对齐',
        }.get(usage, usage)
        matched = data.get('matched_frame_control')
        matched_source = matched.get('pose_source', 'colmap') if isinstance(matched, dict) else 'colmap'
        rows.append({
            "session": data.get("session"),
            "run": path.parent.name.removeprefix('dense-' + str(data.get('session')) + '-'),
            "pose_source": (f'gt（{matched_source.upper()} 同帧）' if matched
                            else data.get("pose_source")),
            "voxels": data.get("voxels"),
            "voxel_m": data.get('voxel_m'),
            "frames": frames,
            "coverage": coverage,
            "truth_usage": usage,
            "observations_per_voxel": data.get("observations_per_voxel"),
            "thickness": (data.get("surface_thickness_m") or {}).get("median"),
            "label_recall": data.get("label_recall_0_5_m"),
            "plane": (data.get("perpendicular_to_label_plane_m") or {}).get("median"),
            "alignment": (data.get("pose_alignment") or {}).get("rmse_m"),
        })
    if not rows:
        return ""
    rows.sort(key=lambda row: (row["session"] or "", row["pose_source"] or ""))
    header = "| " + " | ".join(label for _, label in DENSE_COLUMNS) + " |"
    divider = "|" + "|".join("---" for _ in DENSE_COLUMNS) + "|"
    lines = [header, divider]
    for row in rows:
        cells = []
        for key, _ in DENSE_COLUMNS:
            value = row.get(key, "")
            if value is None:
                value = "-"
            cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
