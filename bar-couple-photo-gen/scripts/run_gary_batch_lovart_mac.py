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
DEFAULT_QUALITY = "medium"
DEFAULT_NUM_IMAGES = 1

RESOLUTION_PROFILES = {
    "default": {
        "9x16": {"aspect_ratio": "9:16", "width": 1008, "height": 1792, "size_preset": "9:16"},
        "16x9": {"aspect_ratio": "16:9", "width": 1792, "height": 1008, "size_preset": "16:9"},
    },
    "2k": {
        "9x16": {"aspect_ratio": "9:16", "width": 2016, "height": 3584, "size_preset": "9:16（2K）"},
        "16x9": {"aspect_ratio": "16:9", "width": 2048, "height": 1152, "size_preset": "16:9（2K）"},
    },
}

QUALITY_MODELS = {
    "auto": "generate_image_gpt_image_2",
    "low": "generate_image_gpt_image_2_low",
    "medium": "generate_image_gpt_image_2_medium",
    "high": "generate_image_gpt_image_2_high",
}

QUALITY_LABELS = {
    "auto": "自动（auto）",
    "low": "低（low）",
    "medium": "中（medium）",
    "high": "高（high）",
}


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

SOFA_SCENES = [
    "高级酒店酒廊",
    "酒店大堂酒廊",
    "高级餐厅休息区",
    "私人会所休息区",
    "高级酒廊沙发区",
    "朋友聚会包间",
    "KTV包间沙发区",
]

COFFEE_SCENES = [
    "高级咖啡厅",
    "酒店大堂咖啡厅",
    "商场咖啡厅",
    "夜间咖啡厅",
    "咖啡厅包间",
    "复古咖啡馆",
    "书店咖啡厅",
    "临街咖啡厅",
    "酒店休息区咖啡厅",
]

COFFEE_CAMERA_ANGLES = [
    "从男主后方拍摄",
    "从男主侧后方拍摄",
    "从沙发斜后方拍摄",
    "从旁边朋友座位拍摄",
    "从桌边斜侧面拍摄",
    "从女主正前方略偏男主背后拍摄",
]

COFFEE_POSITIONS = [
    "男主背对镜头女主面对男主",
    "男主侧背对镜头女主坐在对面沙发",
    "男主靠近镜头只露出侧脸和肩膀女主在画面中心",
    "男主身体挡住一部分前景女主脸清楚可见",
]

COFFEE_INTERACTIONS = [
    "女主看着男主笑",
    "女主低头笑了一下",
    "女主手里拿着咖啡杯",
    "女主一只手放在桌边",
    "男主身体微微前倾像在说话",
    "男主手搭在沙发靠背",
    "男主侧身听女主说话",
    "两人靠近看手机但女主脸可见",
]

COFFEE_BACKGROUND_EVIDENCE = [
    "背景有其他客人",
    "咖啡师和吧台",
    "落地窗和路灯",
    "桌面咖啡杯",
    "蛋糕柜",
    "暖黄吊灯",
    "绿植和玻璃反光",
    "邻桌模糊人影",
]

COFFEE_LIGHTING = [
    "暖黄咖啡厅灯光混合手机直闪",
    "夜间室内暖光加窗外冷光",
    "吧台灯光和机顶闪光混合",
    "沙发区暗光加局部高光溢出",
    "咖啡厅低照度环境加手机夜拍噪点",
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

COFFEE_CANDID_CORE = (
    "使用图1和图2作为人物参考，保持两位人物的真实面貌、五官比例、发型、年龄感、体型和气质一致，"
    "不要美化成模特或网红脸。高级餐厅的真实抓拍照片，男主和女主在沙发上聊天，从男主后方拍摄，"
    "能清楚看到女主的脸，距离很近，表情放松，不看镜头，真实到像朋友圈原图的手机抓拍，"
    "像正在聊天或临时合影时被朋友随手拍下，背景里有其他人，主角不看镜头，动作不统一，"
    "表情自然松弛，人物都是普通人，人物在图片下三分之二位置，女生鼻子不要太高，不是模特，"
    "不精修，不夸张打扮，保持与参考图角色一致，不改变面貌，真实皮肤纹理和轻微瑕疵保留。"
    "业余手机摄影风格，构图歪斜，轻微运动模糊，局部失焦，真实感灯光，高光，直闪 ，"
    "机顶闪光人像，非摆拍，非商业感，非宣传照，强烈生活流纪实感，像朋友聚会时无意拍到的一张照片，画面合规。 "
    "负面提示词： 网红脸，磨皮，美颜，时尚大片，棚拍，专业打光，AI感过强，塑料皮肤，脸部过于完美，多余手指，肢体畸形 "
    "负面提示词： 摆拍，棚拍，商业摄影，时尚大片，杂志封面，网红风，网红脸，模特感，"
    "过度美颜，磨皮，滤镜感，塑料皮肤，过度锐化，人物过于完美，夸张姿势，不自然表情，刻意看镜头，"
    "电影感过强，CG感，3D感，动漫感，AI感过强，光线过于干净，背景虚假，人物重复，多余手指，"
    "手部畸形，肢体畸形，脸部结构错误"
)

COUPLE_PILLOW_PLAY_FIRST_FRAME_CORE = (
    "生成情侣打闹视频的首帧。高级酒店套房客厅里的真实情侣手机抓拍。"
    "使用图1和图2作为人物参考，严格保持两位人物的身份、真实面貌、五官比例、发型、年龄感、体型、"
    "自然气质和参考服装一致，不改变角色身份，不美化成模特或网红脸。图2为成年女主；图1为男友。"
    "画面采用第一人称男友POV，男主本人不得完整出镜，只允许画面边缘自然出现一只刚伸向抱枕的手或少量衣袖，"
    "不要出现男主的脸、头部、身体或第三人。\n"
    "女主衣着完整得体，侧身坐在高级酒店套房客厅的浅色沙发角落，怀里抱着一个柔软抱枕。"
    "她刚发现男友准备过来抢抱枕，一只手把抱枕抱紧，身体自然向沙发靠背一侧躲闪，"
    "另一只手抬向男友镜头，像笑着阻止男友靠近。她自然看向男友，不是面对摄影师摆拍；"
    "表情放松、调皮、忍不住想笑，眼睛微微弯起，嘴角自然上扬，像普通情侣即将开始打闹前被临时拍下的一瞬间。"
    "互动亲近轻松，只有自然情侣感，不性感、不挑逗、无性暗示。\n"
    "必须保留动作尚未完成的首帧状态：女主身体略微侧转，抱枕只遮挡躯干、不能遮挡脸，"
    "男友的手刚伸向抱枕但尚未碰到，双方之间保留自然距离。画面右侧留出适量动作空间，"
    "便于后续衔接女主侧身躲开、用抱枕反击并跑出画面的连续动作；不要直接表现击打、追逐或动作完成后的姿势。\n"
    "高级酒店套房客厅背景真实生活化：深色木质墙面、厚重窗帘、暖色落地灯、玻璃茶几和少量酒店陈设自然入镜。"
    "背景整体偏暗，环境灯光不均匀，不要明亮通透的日系阳光，不要白天客厅感。"
    "茶几边缘和玻璃反光可以进入前景，但不能遮挡女主；不要酒瓶堆积，不要杂乱派对场景。\n"
    "第一人称近距离手机广角，镜头位于沙发正前方略偏右，镜头高度接近女主坐姿胸口至肩膀，略微俯拍，"
    "距离约一米。近距离半身至四分之三身构图，女主主要位于画面下三分之二；不要全身远景，"
    "不要过度俯视，不要鱼眼畸变。业余手机摄影风格，构图轻微歪斜，机顶直闪，"
    "皮肤带真实闪光灯高光，局部高光轻微溢出，闪光衰减自然，背景保持偏暗。"
    "保留轻微夜拍颗粒、局部失焦和发丝边缘运动模糊，以及真实皮肤纹理、毛孔、轻微瑕疵和自然肤色。"
    "高清但不过度锐化，强烈生活流纪实感，像男友临时用手机拍下的一张朋友圈原图。"
    "非摆拍，非商业摄影，非精修，非宣传照，不要影楼布光，不要时尚大片，不要过强电影感，"
    "不要干净到失真的高级广告质感。\n"
    "负面提示词：未成年人，男主完整出镜，男主脸部，男主头部，第三人，多余人物，抱枕遮脸，"
    "动作已经完成，击打动作，追逐动作，性感，挑逗，性暗示，暴力感，摆拍，商业摄影，宣传照，"
    "影楼布光，专业打光，时尚大片，杂志封面，电影感过强，广告质感，明亮日系阳光，白天客厅，"
    "酒瓶堆积，派对杂乱，鱼眼畸变，过度俯视，全身远景，网红脸，模特脸，明星脸，过度美颜，磨皮，"
    "塑料皮肤，滤镜感，过度锐化，脸部过于完美，五官改变，身份不一致，夸张表情，不自然姿势，"
    "抱枕变形，多余手臂，多余手指，手部畸形，肢体畸形，脸部结构错误，人物重复，CG感，3D感，"
    "动漫感，AI感过强，水印，文字"
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


def png_dimensions(path):
    try:
        header = Path(path).read_bytes()[:24]
    except OSError:
        return None
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return None
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def select_current_downloads(downloaded, settings):
    expected = (settings["width"], settings["height"])
    matching = [
        item for item in downloaded
        if item.get("local_path") and png_dimensions(item["local_path"]) == expected
    ]
    if matching:
        return matching[-settings["num_images"]:]
    return downloaded[-settings["num_images"]:]


def artifact_urls(result):
    urls = set()
    for item in result.get("items") or []:
        if item.get("type") != "generator":
            continue
        for artifact in item.get("artifacts") or []:
            content = artifact.get("content")
            if content:
                urls.add(content)
    return urls


def recorded_output_paths(manifest_path):
    paths = set()
    if not manifest_path or not manifest_path.exists():
        return paths
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        for output_path in record.get("output_paths") or []:
            paths.add(str(Path(output_path).resolve()))
    return paths


def move_with_collision_guard(source, destination_dir):
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source.name
    counter = 1
    while destination.exists():
        destination = destination_dir / f"{source.stem}_{counter}{source.suffix}"
        counter += 1
    source.replace(destination)
    return destination


def archive_unselected_downloads(downloaded, selected, output_dir, records_dir, protected_paths):
    selected_paths = {
        str(Path(item["local_path"]).resolve())
        for item in selected
        if item.get("local_path")
    }
    archived = []
    archive_dir = records_dir / "historical_downloads"
    output_dir_resolved = output_dir.resolve()
    for item in downloaded:
        local_path = item.get("local_path")
        if not local_path:
            continue
        path = Path(local_path)
        resolved = str(path.resolve())
        if resolved in selected_paths or resolved in protected_paths:
            continue
        if not path.exists() or path.parent.resolve() != output_dir_resolved:
            continue
        archived.append(str(move_with_collision_guard(path, archive_dir)))
    return archived


def organize_existing_batch(batch_dir):
    records_dir = batch_dir / ".records"
    records_dir.mkdir(parents=True, exist_ok=True)
    manifest_candidates = [batch_dir / "manifest.jsonl", records_dir / "manifest.jsonl"]
    keep_paths = set()
    for manifest_path in manifest_candidates:
        keep_paths.update(recorded_output_paths(manifest_path))

    archived_images = []
    for path in batch_dir.glob("*.png"):
        if str(path.resolve()) not in keep_paths:
            archived_images.append(
                str(move_with_collision_guard(path, records_dir / "historical_downloads"))
            )

    moved_records = []
    for path in list(batch_dir.glob("*.json")) + list(batch_dir.glob("*.jsonl")):
        moved_records.append(str(move_with_collision_guard(path, records_dir)))

    shared_manifest = records_dir / "manifest.jsonl"
    if shared_manifest.exists():
        unique_lines = []
        seen_outputs = set()
        for line in shared_manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                unique_lines.append(line)
                continue
            output_key = tuple(record.get("output_paths") or [])
            if output_key and output_key in seen_outputs:
                continue
            if output_key:
                seen_outputs.add(output_key)
            unique_lines.append(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
        shared_manifest.write_text(
            "\n".join(unique_lines) + ("\n" if unique_lines else ""),
            encoding="utf-8",
        )

    return {
        "batch_dir": str(batch_dir),
        "kept_images": sorted(keep_paths),
        "archived_images": archived_images,
        "moved_records": moved_records,
    }


def generation_settings(
    aspect,
    quality=DEFAULT_QUALITY,
    num_images=DEFAULT_NUM_IMAGES,
    resolution_profile="default",
):
    return {
        **RESOLUTION_PROFILES[resolution_profile][aspect],
        "resolution_profile": resolution_profile,
        "quality": quality,
        "num_images": num_images,
        "preferred_model": QUALITY_MODELS[quality],
    }


def build_parameter_line(aspect, settings, coffee_environment=False):
    ratio = settings["aspect_ratio"]
    orientation = "横版" if aspect == "16x9" else "竖版"
    line = (
        f"生成{ratio}{orientation}手机照片，W {settings['width']} / H {settings['height']}，"
        f"质量：{QUALITY_LABELS[settings['quality']]}，只生成{settings['num_images']}张。"
    )
    if settings["resolution_profile"] == "2k":
        line += f"尺寸预设必须选择 Lovart 面板中的{settings['size_preset']}。"
    if aspect == "16x9":
        environment = "高级餐厅环境" if coffee_environment else "真实室内环境"
        line += f"画面保留更多{environment}，但人物仍是近距离抓拍，不要全身照。"
    return line


def build_photo_prompt(scene, interaction, aspect, settings):
    first_line = build_parameter_line(aspect, settings)
    return f"{first_line}\n{scene}的真实抓拍照片，{interaction}。\n{FIXED_SUFFIX}"


def build_sofa_prompt(scene, aspect, settings):
    if aspect == "16x9":
        composition = (
            "横图 16:9，近距离低机位拍摄，画面保留更多酒廊环境，但人物仍是近距离半身抓拍，不要全身照。"
        )
    else:
        composition = (
            "竖图 9:16，近距离低机位拍摄，镜头高度接近茶几，从人物正前方略偏右的位置拍摄，"
            "人物主要位于画面下三分之二。"
        )
    return (
        f"{build_parameter_line(aspect, settings)}\n"
        f"{scene}里的真实朋友圈抓拍照片，参考图1和图2的人物身份、面貌、服装、人物关系保持一致，不改变角色长相。"
        "男主和女生并肩坐在浅色沙发上，距离很近，像正在和朋友聊天时被随手拍下。"
        "男主坐在左侧，身体微微后靠，一只手自然搭在女生身后或沙发靠背上，另一只手朝画面外轻轻比划，像正在说话；"
        "男主看向画面左侧，不看镜头，表情自然沉稳。\n"
        "负面提示词：\n"
        "网红脸，模特感，明星脸，过度精修，磨皮，美颜滤镜，塑料皮肤，脸部过于完美，鼻子过高，五官过度立体，夸张妆容，"
        "时尚大片，杂志封面，棚拍，商业摄影，专业布光，电影感过强，光线过于干净，背景虚假，摆拍感，刻意看镜头，夸张姿势，"
        "不自然表情，人物重复，脸部结构错误，多余手指，手部畸形，肢体畸形，腿部畸形，比例错误，CG感，3D感，动漫感，AI感过强，过度锐化，低质量脸部\n\n"
        "女生坐在男主右侧，身体贴近男主，姿态放松，腿向镜头前方伸展，一只腿自然搭近酒桌或靠近茶几边缘，高跟鞋和腿部形成明显前景透视。"
        "镜头正对两人但人物不刻意看镜头，像朋友聚会中临时拍下的一张原图。女生表情松弛自然，不是模特感，不要网红脸，鼻子不要太高，"
        "五官保持普通真实，真实皮肤纹理、轻微瑕疵和面部细节保留。\n"
        f"{composition}"
        "前景有黑色酒桌、威士忌酒杯、白色杯子、玻璃反光；背景有灰色墙面、深色柜门、玻璃门、落地灯。"
        "业余手机摄影风格，近距离广角，轻微歪斜构图，轻微运动模糊，局部失焦，夜拍噪点，机顶直闪，人物皮肤有闪光灯高光，背景偏暗，高光轻微溢出。"
        "非摆拍，非商业摄影，非精修，强烈生活流纪实感，像朋友聚会时无意拍到的一张真实照片。"
    )


def build_coffee_prompt(aspect, settings):
    first_line = build_parameter_line(aspect, settings, coffee_environment=True)
    return f"{first_line}\n{COFFEE_CANDID_CORE}"


def build_couple_pillow_play_first_frame_prompt(aspect, settings):
    first_line = build_parameter_line(aspect, settings)
    if aspect == "16x9":
        aspect_instruction = (
            "横屏保留更多高级酒店套房客厅环境和画面右侧动作空间，但女主仍是近距离半身至四分之三身抓拍，"
            "不要缩小人物，不要全身远景。"
        )
    else:
        aspect_instruction = (
            "竖屏保持女主近距离半身至四分之三身构图，并在画面右侧保留足够的后续动作空间。"
        )
    return f"{first_line}\n{aspect_instruction}\n{COUPLE_PILLOW_PLAY_FIRST_FRAME_CORE}"


def build_prompt(scene, interaction, aspect, prompt_preset, settings, prompt_variables=None):
    if prompt_preset == "coffee_candid_universal":
        return build_coffee_prompt(aspect, settings)
    if prompt_preset == "couple_pillow_play_first_frame":
        return build_couple_pillow_play_first_frame_prompt(aspect, settings)
    if prompt_preset == "sofa":
        return build_sofa_prompt(scene, aspect, settings)
    return build_photo_prompt(scene, interaction, aspect, settings)


def choose_different_pair(previous=None, prompt_preset="photo"):
    scene_pool = SOFA_SCENES if prompt_preset == "sofa" else SCENES
    scene = random.choice(scene_pool)
    interaction = "沙发前景抓拍" if prompt_preset == "sofa" else random.choice(INTERACTIONS)
    if previous is None:
        return scene, interaction
    for _ in range(20):
        if (scene, interaction) != previous:
            return scene, interaction
        scene = random.choice(scene_pool)
        interaction = "沙发前景抓拍" if prompt_preset == "sofa" else random.choice(INTERACTIONS)
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
        has_explicit_targets = bool(args.target_vertical or args.target_horizontal)
        for aspect, target in aspect_targets:
            if target <= 0:
                if has_explicit_targets:
                    continue
                target = len(selected)
            for i in range(target):
                female_path = selected[i % len(selected)]
                if args.prompt_preset in {"coffee_candid_universal", "couple_pillow_play_first_frame"}:
                    prompt_variables = None
                    if args.prompt_preset == "coffee_candid_universal":
                        scene = "高级餐厅"
                        interaction = "从男主后方拍摄"
                    else:
                        scene = "高级酒店套房客厅"
                        interaction = "第一人称男友POV抢抱枕前的未完成动作"
                else:
                    previous = previous_by_female.get(female_path.name)
                    scene, interaction = choose_different_pair(previous, args.prompt_preset)
                    previous_by_female[female_path.name] = (scene, interaction)
                    prompt_variables = None
                tasks.append({
                    "aspect": aspect,
                    "female_path": female_path,
                    "scene": scene,
                    "interaction": interaction,
                    "prompt_variables": prompt_variables,
                })
        return tasks

    tasks = []
    for female_path in female_files:
        if args.prompt_preset in {"coffee_candid_universal", "couple_pillow_play_first_frame"}:
            prompt_variables = None
            if args.prompt_preset == "coffee_candid_universal":
                scene = "高级餐厅"
                interaction = "从男主后方拍摄"
            else:
                scene = "高级酒店套房客厅"
                interaction = "第一人称男友POV抢抱枕前的未完成动作"
        else:
            prompt_variables = None
            scene = random.choice(SOFA_SCENES if args.prompt_preset == "sofa" else SCENES)
            interaction = "沙发前景抓拍" if args.prompt_preset == "sofa" else random.choice(INTERACTIONS)
        tasks.append({
            "aspect": "9x16",
            "female_path": female_path,
            "scene": scene,
            "interaction": interaction,
            "prompt_variables": prompt_variables,
        })
    return tasks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-exe", default=sys.executable)
    parser.add_argument("--male-path", default=DEFAULT_MALE)
    parser.add_argument("--female-dir", default=DEFAULT_FEMALE_DIR)
    parser.add_argument("--female-path", default=None)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--batch-dir",
        default=None,
        help="将同一角色同一批次的多个 preset 直接保存到同一个日期批次目录",
    )
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--vertical-thread-id", default=None)
    parser.add_argument("--horizontal-thread-id", default=None)
    parser.add_argument("--max-network-retries", type=int, default=3)
    parser.add_argument("--max-generation-attempts", type=int, default=2)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--target-vertical", type=int, default=0)
    parser.add_argument("--target-horizontal", type=int, default=0)
    parser.add_argument("--female-count", type=int, default=0)
    parser.add_argument("--aspect-mode", choices=["vertical", "horizontal", "both"], default="vertical")
    parser.add_argument("--run-label", default="_gary_batch")
    parser.add_argument(
        "--prompt-preset",
        choices=["photo", "sofa", "coffee_candid_universal", "couple_pillow_play_first_frame"],
        default="photo",
    )
    parser.add_argument("--quality", choices=["auto", "low", "medium", "high"], default=DEFAULT_QUALITY)
    parser.add_argument("--num-images", type=int, choices=[1, 2, 4], default=DEFAULT_NUM_IMAGES)
    parser.add_argument("--resolution-profile", choices=["default", "2k"], default="default")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--dry-run", "--print-prompt", dest="dry_run", action="store_true")
    parser.add_argument(
        "--organize-batch-only",
        action="store_true",
        help="仅整理现有批次：根目录保留 manifest 记录的成品，历史图片和日志移入隐藏目录",
    )
    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    if args.organize_batch_only:
        if not args.batch_dir:
            parser.error("--organize-batch-only 必须同时指定 --batch-dir")
        print(json.dumps(organize_existing_batch(Path(args.batch_dir)), ensure_ascii=False, indent=2))
        return

    if args.dry_run:
        aspects = ["9x16", "16x9"] if args.aspect_mode == "both" else [
            "16x9" if args.aspect_mode == "horizontal" else "9x16"
        ]
        previews = []
        for aspect in aspects:
            settings = generation_settings(
                aspect,
                args.quality,
                args.num_images,
                args.resolution_profile,
            )
            variables = None
            if args.prompt_preset == "sofa":
                scene, interaction = random.choice(SOFA_SCENES), "沙发前景抓拍"
            elif args.prompt_preset == "coffee_candid_universal":
                scene, interaction = "高级餐厅", "从男主后方拍摄"
            elif args.prompt_preset == "couple_pillow_play_first_frame":
                scene, interaction = "高级酒店套房客厅", "第一人称男友POV抢抱枕前的未完成动作"
            else:
                scene, interaction = random.choice(SCENES), random.choice(INTERACTIONS)
            previews.append({
                "dry_run": True,
                "network_called": False,
                "uploads_performed": False,
                "prompt_preset": args.prompt_preset,
                "aspect": aspect,
                "settings": settings,
                "random_variables": variables,
                "prompt": build_prompt(
                    scene,
                    interaction,
                    aspect,
                    args.prompt_preset,
                    settings,
                    variables,
                ),
            })
        print(json.dumps(previews, ensure_ascii=False, indent=2))
        return

    load_lovart_env()

    output_root = Path(args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.batch_dir:
        log_dir = Path(args.batch_dir)
    elif args.target_vertical or args.target_horizontal or args.aspect_mode != "vertical":
        log_dir = output_root / f"{args.run_label}_{run_id}"
    else:
        log_dir = output_root / f"_gary_batch_{run_id}"
    log_dir.mkdir(parents=True, exist_ok=True)

    run_tag = f"{args.run_label}_{run_id}"
    if args.batch_dir:
        records_dir = log_dir / ".records"
        records_dir.mkdir(parents=True, exist_ok=True)
        summary_path = records_dir / f"{run_tag}_manifest.jsonl"
        manifest_path = records_dir / f"{run_tag}_run_manifest.json"
        current_path = records_dir / f"{run_tag}_current.json"
        batch_summary_path = records_dir / "manifest.jsonl"
    else:
        summary_path = log_dir / "manifest.jsonl"
        manifest_path = log_dir / "run_manifest.json"
        current_path = log_dir / "current.json"
        batch_summary_path = None

    def record_result(record):
        write_jsonl(summary_path, record)
        if batch_summary_path is not None:
            write_jsonl(batch_summary_path, record)

    female_dir = Path(args.female_dir)
    if args.female_path:
        female_path = Path(args.female_path)
        if not female_path.is_file() or female_path.parent != female_dir:
            raise LovartError(f"指定女主图必须是素材库当前层的图片：{female_path}")
        if female_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise LovartError(f"不支持的女主图片格式：{female_path}")
        female_files = [female_path]
    else:
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
        "vertical_thread_id": args.vertical_thread_id,
        "horizontal_thread_id": args.horizontal_thread_id,
        "male_path": args.male_path,
        "female_dir": args.female_dir,
        "female_path": args.female_path,
        "output_dir": args.output_dir,
        "batch_dir": args.batch_dir,
        "log_dir": str(log_dir),
        "total": len(tasks),
        "female_count": len(female_files),
        "target_vertical": args.target_vertical,
        "target_horizontal": args.target_horizontal,
        "aspect_mode": args.aspect_mode,
        "prompt_preset": args.prompt_preset,
        "prompt_language": "中文",
        "quality": args.quality,
        "num_images": args.num_images,
        "resolution_profile": args.resolution_profile,
        "aspect_settings": RESOLUTION_PROFILES[args.resolution_profile],
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
        prompt_variables = task.get("prompt_variables")
        settings = generation_settings(
            aspect,
            args.quality,
            args.num_images,
            args.resolution_profile,
        )
        prompt = build_prompt(
            scene,
            interaction,
            aspect,
            args.prompt_preset,
            settings,
            prompt_variables,
        )
        if args.batch_dir:
            aspect_output_dir = log_dir
        else:
            aspect_output_dir = log_dir / aspect if args.target_vertical or args.target_horizontal or args.aspect_mode != "vertical" else output_root
        aspect_output_dir.mkdir(parents=True, exist_ok=True)
        reused_thread_id = (
            args.horizontal_thread_id if aspect == "16x9" else args.vertical_thread_id
        )
        base = {
            "run_id": run_id,
            "index": index,
            "total": len(tasks),
            "aspect": aspect,
            "female_path": str(female_path),
            "female_name": female_path.name,
            "scene": scene,
            "interaction": interaction,
            "prompt_variables": prompt_variables,
            "generation_settings": settings,
            "reused_thread_id": reused_thread_id,
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
            record_result(record)
            log(f"[{index}/{len(tasks)}] 上传失败，跳过：{female_path.name}")
            write_json(current_path, {**record, "updated_at": now_iso()})
            continue

        success = False
        existing_urls = set()
        if reused_thread_id:
            try:
                baseline_result = run_agent(
                    args.python_exe,
                    ["result", "--thread-id", reused_thread_id, "--json"],
                    timeout=180,
                )
                existing_urls = artifact_urls(baseline_result)
            except Exception as exc:
                log(f"[{index}/{len(tasks)}] 读取线程基线失败，将停止以避免误认历史产物：{exc}")
                record = {
                    **base,
                    "status": "skipped",
                    "reason": "thread_baseline_failed",
                    "error": str(exc),
                    "finished_at": now_iso(),
                }
                record_result(record)
                write_json(current_path, {**record, "updated_at": now_iso()})
                continue
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
                            *(["--thread-id", reused_thread_id] if reused_thread_id else []),
                            "--prompt", prompt,
                            "--attachments", male_url, female_url,
                            "--prefer-models", json.dumps(
                                {"IMAGE": [settings["preferred_model"]]},
                                ensure_ascii=False,
                                separators=(",", ":"),
                            ),
                            "--json",
                            "--download",
                            "--output-dir", str(aspect_output_dir),
                        ],
                        timeout=900,
                    ),
                )
                all_downloaded = result.get("downloaded") or []
                new_downloaded = [
                    item for item in all_downloaded
                    if item.get("url") and item.get("url") not in existing_urls
                ]
                if not result.get("generation_succeeded") or not new_downloaded:
                    raise LovartError(
                        f"生成完成但无产物：{result.get('warning', '')} {result.get('agent_message', '')}"
                    )
                downloaded = select_current_downloads(new_downloaded, settings)
                if args.batch_dir:
                    protected_paths = recorded_output_paths(batch_summary_path)
                    archive_unselected_downloads(
                        all_downloaded,
                        downloaded,
                        aspect_output_dir,
                        records_dir,
                        protected_paths,
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
                record_result(record)
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
                    record_result(record)
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
    final_path = (
        records_dir / f"{run_tag}_final_summary.json"
        if args.batch_dir
        else log_dir / "final_summary.json"
    )
    write_json(final_path, final)
    write_json(current_path, {**final, "status": "finished", "updated_at": now_iso()})
    log(f"批量完成：成功 {final['success']}，跳过 {final['skipped']}")
    log(f"汇总：{final_path}")


if __name__ == "__main__":
    main()
