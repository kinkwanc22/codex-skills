import argparse
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


DEFAULT_MALE = r"/Users/kin/工作用（同步）/图/人物设定/2896d6707751ecfc30a82a7e9bc680b61f8ccd0efbf28a005f3674f5036a6c0c (1).png"
DEFAULT_FEMALE_DIR = r"/Users/kin/工作用（同步）/图/人物设定/精品"
DEFAULT_OUTPUT_DIR = r"/Users/kin/工作用（同步）/图/长视频用图"
DEFAULT_PROJECT_ID = "70c9b703e8e7481487c4d452d64441dc"
AGENT = r"/Users/kin/.codex/skills/lovart-skill/agent_skill.py"


SCENES = [
    "高级酒廊",
    "高级餐厅",
    "半私密卡座",
    "包厢",
    "KTV包间",
    "酒店大堂酒廊",
    "私房菜餐厅",
    "夜宵店室内",
    "大排档室内",
    "朋友家客厅",
    "室内音乐酒馆",
    "小型聚会包间",
]

INTERACTIONS = [
    "女生从男生身后靠近，一只手自然搭在男生肩膀或手臂上，脸完整清楚露出来，朝镜头自然笑，表情带着暧昧的笑意",
    "女生从背后轻轻靠近男生，脸完整清楚可见，笑着看向镜头，和男生保持自然贴近",
    "女生靠在男生肩边看他手里的手机，脸完整清楚露出来，嘴角带笑，身体自然贴近",
    "女生轻轻拉着男生的袖子靠近他说话，男生侧头听着，气氛暧昧但自然",
    "女生从男生侧后方靠近，手搭在他的肩上低声说话，男生低笑着看向画面外",
    "女生坐在男生身后或侧后方，身体轻轻贴近他的肩膀笑，男生正在和画面外的人说话",
    "女生从后面松松环住男生的肩膀，笑着靠近他，男生侧头低笑不看镜头",
    "女生靠在男生身边，一只手自然搭在他的手臂上，像朋友聚会时突然贴近说话",
    "女生坐在男生侧后方探出头笑，脸完整清楚可见，手自然搭在男生肩上，男生拿着酒杯或手机，表情自然放松不看镜头",
    "女生从男生背后探出头笑，脸不要被男生、头发、手臂或构图遮挡，手自然搭在男生肩上，男生正侧头和图片外的人随口说话",
    "女生坐在男生旁边微微靠近他，一只手搭在他手臂上，脸完整清楚看向镜头笑，男生侧头看向画面外",
    "女生从侧后方轻轻环住男生肩膀，脸完整清楚露在男生旁边，朝镜头自然笑，男生低头看手机或酒杯不看镜头",
]

FIXED_SUFFIX = (
    "男生正在和图片外的人随口说话，不看镜头，表情自然，不是刻意摆拍。 使用图1和图2作为人物参考，"
    "保持两位人物的真实面貌、五官比例、发型、年龄感、体型和气质一致，不要美化成模特或网红脸。 "
    "两人的动作不完全统一，像朋友聚会或临时合影时被旁边朋友随手拍下的一瞬间。 场景是真实生活化背景。"
    "整体氛围像朋友圈原图、生活流纪实照片，不是商业摄影，不是宣传照。 业余手机摄影风格，轻微歪斜构图，"
    "人物在图片中间位置，手机直闪效果，机顶闪光人像质感，局部高光轻微溢出，背景有轻微失焦，"
    "人物边缘有一点点运动模糊，保留真实皮肤纹理、毛孔、轻微瑕疵和自然肤色。 画面不要过度锐化，"
    "不要精修，不要磨皮，不要滤镜感。人物都是普通人，不夸张打扮，女生鼻子不要过高，不要变成精致网红脸。 "
    "真实手机夜拍质感，轻微颗粒感可以保留，但不要严重脏噪点。整体像朋友随手拍到的一张真实照片，"
    "生活感强，非摆拍，非电影感，非AI精修感。 女生的脸必须完整清楚可见，不要被男生、头发、手臂或构图遮挡。 负面提示词： 网红脸，模特脸，过度美颜，磨皮，塑料皮肤，"
    "脸部过于完美，鼻子过高，夸张妆容，时尚大片，棚拍，专业打光，商业摄影，宣传照，杂志封面，"
    "电影感过强，CG感，3D感，动漫感，AI感过强，滤镜感，过度锐化，光线过于干净，背景虚假，刻意摆拍，"
    "夸张姿势，不自然表情，刻意直视镜头，人物重复，多余人物，多余手指，手部畸形，肢体畸形，"
    "脸部结构错误，五官变形，身份不一致，改变面貌，低清，严重噪点，画面脏污，水印，文字"
)


class LovartError(Exception):
    pass


def load_lovart_env():
    if os.environ.get("LOVART_ACCESS_KEY") and os.environ.get("LOVART_SECRET_KEY"):
        return
    if os.name != "nt":
        for key in ("LOVART_ACCESS_KEY", "LOVART_SECRET_KEY"):
            if os.environ.get(key):
                continue
            try:
                value = subprocess.run(
                    ["launchctl", "getenv", key],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=5,
                ).stdout.strip()
            except Exception:
                value = ""
            if value:
                os.environ[key] = value
        return
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            access_key, _ = winreg.QueryValueEx(key, "LOVART_ACCESS_KEY")
            secret_key, _ = winreg.QueryValueEx(key, "LOVART_SECRET_KEY")
        os.environ["LOVART_ACCESS_KEY"] = access_key
        os.environ["LOVART_SECRET_KEY"] = secret_key
    except OSError:
        return


def now_iso():
    return datetime.now().astimezone().isoformat()


def log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)


def run_agent(python_exe, args, timeout=None):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    cmd = [python_exe, AGENT, *args]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=timeout,
    )
    text = proc.stdout.strip()
    if proc.returncode != 0:
        raise LovartError(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise LovartError(f"Lovart JSON 解析失败：{text}") from exc


def with_network_retry(label, max_retries, fn):
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except Exception as exc:
            last_error = str(exc)
            log(f"{label} 网络/连接错误，第 {attempt}/{max_retries} 次：{last_error}")
            if attempt < max_retries:
                time.sleep(min(20 * attempt, 60))
    raise LovartError(last_error or f"{label} failed")


def upload_file(python_exe, max_network_retries, path):
    result = with_network_retry(
        "upload",
        max_network_retries,
        lambda: run_agent(python_exe, ["upload", "--file", str(path)], timeout=180),
    )
    if not result.get("url"):
        raise LovartError(f"上传无 URL：{path}")
    return result["url"]


def write_jsonl(path, obj):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def build_prompt(scene, interaction, aspect):
    if aspect == "16x9":
        first_line = "生成16:9横版手机照片，画面保留更多真实室内环境，但人物仍是近距离半身抓拍，不要全身照。"
    else:
        first_line = "生成9:16竖版手机照片。"
    return f"{first_line}\n{scene}的真实抓拍照片，{interaction}。\n{FIXED_SUFFIX}"


def choose_different_pair(previous=None):
    scene = random.choice(SCENES)
    interaction = random.choice(INTERACTIONS)
    if previous is None:
        return scene, interaction
    for _ in range(20):
        if (scene, interaction) != previous:
            return scene, interaction
        scene = random.choice(SCENES)
        interaction = random.choice(INTERACTIONS)
    return scene, interaction


def build_tasks(female_files, args):
    if args.target_vertical or args.target_horizontal or args.aspect_mode != "vertical":
        selected = female_files[: args.female_count] if args.female_count > 0 else female_files
        tasks = []
        previous_by_female = {}
        aspect_targets = []
        if args.aspect_mode in {"vertical", "both"}:
            aspect_targets.append(("9x16", args.target_vertical))
        if args.aspect_mode in {"horizontal", "both"}:
            aspect_targets.append(("16x9", args.target_horizontal))
        for aspect, target in aspect_targets:
            if target <= 0:
                continue
            for i in range(target):
                female_path = selected[i % len(selected)]
                previous = previous_by_female.get(female_path.name)
                scene, interaction = choose_different_pair(previous)
                previous_by_female[female_path.name] = (scene, interaction)
                tasks.append({
                    "aspect": aspect,
                    "female_path": female_path,
                    "scene": scene,
                    "interaction": interaction,
                })
        return tasks

    return [
        {
            "aspect": "9x16",
            "female_path": female_path,
            "scene": random.choice(SCENES),
            "interaction": random.choice(INTERACTIONS),
        }
        for female_path in female_files
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-exe", default=sys.executable)
    parser.add_argument("--male-path", default=DEFAULT_MALE)
    parser.add_argument("--female-dir", default=DEFAULT_FEMALE_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--max-network-retries", type=int, default=3)
    parser.add_argument("--max-generation-attempts", type=int, default=2)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--target-vertical", type=int, default=0)
    parser.add_argument("--target-horizontal", type=int, default=0)
    parser.add_argument("--female-count", type=int, default=0)
    parser.add_argument("--aspect-mode", choices=["vertical", "horizontal", "both"], default="vertical")
    parser.add_argument("--run-label", default="_gary_batch")
    args = parser.parse_args()
    load_lovart_env()

    output_root = Path(args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.target_vertical or args.target_horizontal or args.aspect_mode != "vertical":
        log_dir = output_root / f"{args.run_label}_{run_id}"
    else:
        log_dir = output_root / f"_gary_batch_{run_id}"
    log_dir.mkdir(parents=True, exist_ok=True)

    summary_path = log_dir / "manifest.jsonl"
    manifest_path = log_dir / "run_manifest.json"
    current_path = log_dir / "current.json"

    female_dir = Path(args.female_dir)
    female_files = [
        p for p in female_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    ]
    random.shuffle(female_files)
    if args.limit and args.limit > 0:
        female_files = female_files[: args.limit]
    if args.female_count and args.female_count > 0:
        female_files = female_files[: args.female_count]
    if not female_files:
        raise LovartError(f"女主素材库为空：{female_dir}")
    tasks = build_tasks(female_files, args)

    manifest = {
        "run_id": run_id,
        "started_at": now_iso(),
        "project_id": args.project_id,
        "male_path": args.male_path,
        "female_dir": args.female_dir,
        "output_dir": args.output_dir,
        "log_dir": str(log_dir),
        "total": len(tasks),
        "female_count": len(female_files),
        "target_vertical": args.target_vertical,
        "target_horizontal": args.target_horizontal,
        "aspect_mode": args.aspect_mode,
        "prompt_language": "中文",
        "max_network_retries": args.max_network_retries,
        "max_generation_attempts": args.max_generation_attempts,
    }
    write_json(manifest_path, manifest)

    log(f"批量开始：{len(tasks)} 个生成任务，{len(female_files)} 张女主图")
    log(f"日志目录：{log_dir}")

    male_url = upload_file(args.python_exe, args.max_network_retries, Path(args.male_path))
    log("男主图已上传")

    female_url_cache = {}
    for index, task in enumerate(tasks, start=1):
        female_path = task["female_path"]
        aspect = task["aspect"]
        scene = task["scene"]
        interaction = task["interaction"]
        prompt = build_prompt(scene, interaction, aspect)
        aspect_output_dir = log_dir / aspect if args.target_vertical or args.target_horizontal or args.aspect_mode != "vertical" else output_root
        aspect_output_dir.mkdir(parents=True, exist_ok=True)
        base = {
            "run_id": run_id,
            "index": index,
            "total": len(tasks),
            "aspect": aspect,
            "female_path": str(female_path),
            "female_name": female_path.name,
            "scene": scene,
            "interaction": interaction,
            "started_at": now_iso(),
        }
        write_json(current_path, {**base, "status": "running", "updated_at": now_iso()})

        log(f"[{index}/{len(tasks)}] 开始：{aspect} | {female_path.name} | {scene}")
        try:
            female_url = female_url_cache.get(str(female_path))
            if not female_url:
                female_url = upload_file(args.python_exe, args.max_network_retries, female_path)
                female_url_cache[str(female_path)] = female_url
        except Exception as exc:
            record = {
                **base,
                "status": "skipped",
                "reason": "upload_failed",
                "error": str(exc),
                "finished_at": now_iso(),
            }
            write_jsonl(summary_path, record)
            log(f"[{index}/{len(tasks)}] 上传失败，跳过：{female_path.name}")
            write_json(current_path, {**record, "updated_at": now_iso()})
            continue

        success = False
        for gen_attempt in range(1, args.max_generation_attempts + 1):
            try:
                result = with_network_retry(
                    "chat",
                    args.max_network_retries,
                    lambda: run_agent(
                        args.python_exe,
                        [
                            "chat",
                            "--project-id", args.project_id,
                            "--prompt", prompt,
                            "--attachments", male_url, female_url,
                            "--json",
                            "--download",
                            "--output-dir", str(aspect_output_dir),
                        ],
                        timeout=900,
                    ),
                )
                downloaded = result.get("downloaded") or []
                if not result.get("generation_succeeded") or not downloaded:
                    raise LovartError(
                        f"生成完成但无产物：{result.get('warning', '')} {result.get('agent_message', '')}"
                    )

                record = {
                    **base,
                    "status": "success",
                    "attempt": gen_attempt,
                    "thread_id": result.get("thread_id"),
                    "project_id": result.get("project_id"),
                    "output_paths": [item.get("local_path") for item in downloaded],
                    "urls": [item.get("url") for item in downloaded],
                    "finished_at": now_iso(),
                }
                write_jsonl(summary_path, record)
                write_json(current_path, {**record, "updated_at": now_iso()})
                log(f"[{index}/{len(tasks)}] 成功：{downloaded[0].get('local_path')}")
                success = True
                break
            except Exception as exc:
                error = str(exc)
                log(f"[{index}/{len(tasks)}] 生成失败 attempt {gen_attempt}/{args.max_generation_attempts}：{error}")
                if gen_attempt < args.max_generation_attempts:
                    time.sleep(10)
                else:
                    record = {
                        **base,
                        "status": "skipped",
                        "attempt": gen_attempt,
                        "reason": "generation_failed_twice",
                        "error": error,
                        "finished_at": now_iso(),
                    }
                    write_jsonl(summary_path, record)
                    write_json(current_path, {**record, "updated_at": now_iso()})

        if not success:
            log(f"[{index}/{len(tasks)}] 连续失败，自动换下一张")

    records = []
    if summary_path.exists():
        for line in summary_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))

    final = {
        "run_id": run_id,
        "finished_at": now_iso(),
        "total": len(tasks),
        "success": sum(1 for r in records if r.get("status") == "success"),
        "skipped": sum(1 for r in records if r.get("status") != "success"),
        "success_9x16": sum(1 for r in records if r.get("status") == "success" and r.get("aspect") == "9x16"),
        "success_16x9": sum(1 for r in records if r.get("status") == "success" and r.get("aspect") == "16x9"),
        "summary_path": str(summary_path),
        "manifest_path": str(manifest_path),
    }
    final_path = log_dir / "final_summary.json"
    write_json(final_path, final)
    write_json(current_path, {**final, "status": "finished", "updated_at": now_iso()})
    log(f"批量完成：成功 {final['success']}，跳过 {final['skipped']}")
    log(f"汇总：{final_path}")


if __name__ == "__main__":
    main()
