---
name: bar-couple-photo-gen
description: Generate 9:16 photorealistic candid man-woman interaction images with a fixed male lead identity and a user-provided female lead. Use when the user asks to create images with a fixed male character, replace only the female character, generate dating/couple/bar/social interaction photos, produce GPT Image 2 / image2 high-fidelity portrait consistency prompts, or says they only want to input the female role for different man-woman interaction images.
---

# Bar Couple Photo Generator

Use this skill to generate vertical 9:16 realistic lifestyle images with a fixed male lead and a variable female lead. The default style is candid smartphone nightlife photography: direct phone flash, casual friend snapshot, realistic skin texture, non-commercial, non-cinematic, non-AI-polished.

For the current user's recurring Gary/female-lead series, preserve the tested prompt structure: change only the `{scene}` and `{ambiguous_interaction}` blocks when requested, keep the fixed texture/identity/negative wording stable, and avoid full-body compositions. The strongest tested look is close, imperfect, handheld indoor/nightlife framing where the woman is near the man and the man is not posing for the camera.

## Fixed Male Lead

Use `assets/fixed-male-lead.png` as the fixed male identity reference.

For this user's Gary/Lovart workflow, use these synced Windows reference paths by default:

- Fixed male lead: `D:\工作用（同步）\图\人物设定\2896d6707751ecfc30a82a7e9bc680b61f8ccd0efbf28a005f3674f5036a6c0c (1).png`
- Female reference library: `D:\工作用（同步）\图\人物设定\精品`

Preserve the male lead's real facial identity, facial proportions, short black hairstyle, mature understated temperament, age impression, body type, and natural skin texture. Do not beautify him into a model, celebrity, influencer, or fashion editorial face.

## Inputs

Require only one of these female-lead inputs:

- A female reference image.
- A text description of the female character's appearance, age impression, hair, body type, outfit, temperament, and desired vibe.

If the user also gives a specific interaction scene, use it. Otherwise choose one plausible casual social interaction from the interaction bank.

## Default Output

Generate one vertical 9:16 photorealistic image unless the user asks for multiple variants. Prefer GPT Image 2 / image2 high-fidelity portrait consistency. Treat reference images as identity references, not edit targets. Do not generate full-body compositions unless the user explicitly asks. Prefer waist-up, half-body, close three-quarter, or tight social-photo framing with natural cropping. Slightly cut-off hands, shoulders, drinks, or table edges are acceptable when they make the photo feel like a real phone snapshot.

## Prompt Assembly

When generating, assemble the prompt with:

1. **Identity roles:** Fixed male lead from this skill; female lead from the user's current input.
2. **Interaction:** One natural couple/social interaction.
3. **Setting:** Real-life nightlife or social venue unless the user specifies another setting.
4. **Camera style:** Amateur smartphone photo, direct phone flash, slight handheld tilt, central composition, natural handheld crop, mild background defocus, slight motion blur.
5. **Realism constraints:** ordinary people, real skin, no beauty filter, no commercial polish.
6. **Negative prompt:** Use the fixed negative list in this skill and append any user-specific avoid items.

For Gary series variations:

- Keep the first line: `生成9:16竖版手机照片。`
- Replace only the scene phrase (for example: `酒吧`, `高级酒廊`, `高级餐厅`, `半私密卡座`, `包厢`, `KTV包间`, `朋友家客厅`, `酒店大堂酒廊`, `夜宵店/大排档室内`, `私房菜餐厅`) and the ambiguous interaction phrase.
- Keep the fixed identity, texture, and negative prompt wording unchanged unless the user explicitly asks to change them.
- Favor indoor or semi-indoor night scenes with mixed ambient light plus phone flash.
- Do not ask for full-body framing. Use close waist-up or half-body candid framing by default.
- If saving locally in this user's workflow, save outputs to `D:\工作用（同步）\图\长视频用图`.

## Interaction Bank

Use these only when the user does not specify an interaction:

- Woman hugs the man from behind while laughing toward the camera; man talks to someone outside frame and does not look at camera.
- Woman leans on the man's shoulder in a crowded bar booth; man turns slightly sideways mid-conversation.
- Woman pulls the man's sleeve while laughing; man holds a drink and looks off-frame naturally.
- Woman stands close beside the man with one arm loosely around his waist; both look caught mid-moment, not posed.
- Woman leans close beside the man while laughing toward the camera; man smiles lightly while looking away.
- Woman rests her chin near the man's shoulder from behind; man is relaxed and not directly posing.
- Woman raises a glass near the man; they are close together but with imperfect, spontaneous body language.

## Ambiguous Indoor Interaction Bank

Use these when the user asks for a more ambiguous/flirtatious but non-explicit indoor mood. Keep it natural, not erotic, not staged, and not full-body.

- In a private restaurant booth, the woman leans from behind near the man's shoulder with her face visible; one hand rests naturally on his shoulder or forearm; the man turns slightly and smiles low, not looking at the camera.
- In an upscale lounge booth, the woman loosely hugs the man from behind and laughs near his cheek; the man is mid-conversation with someone off-frame.
- At a dim restaurant table, the woman leans over the man's shoulder to look at something on his phone; their faces are close, and the man smiles while looking down.
- In a KTV/private room sofa corner, the woman rests her chin near the man's shoulder with a teasing smile; the man holds a glass and glances away.
- In a hotel lobby lounge, the woman lightly pulls the man's sleeve while leaning close; he turns sideways mid-sentence, relaxed and not posing.
- In a late-night indoor food stall or private dining room, the woman sits close beside him with one arm behind his back; both look caught mid-moment with imperfect body angles.

## Fixed Style Prompt

Use this style block in every image prompt:

```text
Photorealistic candid vertical 9:16 smartphone snapshot, real nightlife/social venue, casual friend gathering, not a staged shoot. Slightly tilted handheld composition, subjects near the center, direct phone flash / on-camera flash portrait look, mild local highlight clipping, realistic flash falloff, warm mixed ambient background light, mild background defocus, slight edge and hair motion blur. Natural skin texture, visible pores, minor blemishes, natural skin tone, ordinary-person realism. Looks like an original phone gallery social photo, strong life documentary feeling. No beauty filter, no retouching, no skin smoothing, no over-sharpening, no cinematic color grade, no commercial-photo polish.
```

Use natural social-photo framing. The image should usually be waist-up, half-body, close three-quarter, or a tight seated/booth crop. Avoid full-body shots by default. Do not force both characters' entire bodies into frame; tighter crops usually look more realistic for this series.

## Fixed Negative Prompt

```text
influencer face, model face, celebrity face, excessive beauty retouching, skin smoothing, plastic skin, waxy skin, overly perfect face, nose too high, nose too sharp, exaggerated makeup, fashion editorial, studio shoot, professional lighting, commercial photography, advertising photo, promotional photo, magazine cover, strong cinematic look, CG look, 3D look, anime look, obvious AI look, filter look, over-sharpened, overly clean lighting, fake background, staged pose, exaggerated pose, unnatural expression, everyone deliberately staring into camera, duplicated people, extra people, extra faces, extra fingers, malformed hands, deformed limbs, wrong facial structure, distorted facial features, inconsistent identity, changed face, low resolution, severe noise, dirty artifacts, watermark, text
```

## Generation Workflow

1. If the user provides a female reference image, use it as the female identity reference.
2. If the user provides only text, describe the female lead explicitly in the prompt and keep her ordinary, natural, and consistent with the user's description.
3. Use `assets/fixed-male-lead.png` as the male identity reference.
4. Use the built-in `image_gen` tool by default. If the user explicitly asks for CLI/API/model control, follow the system imagegen skill fallback rules.
5. Prompt for GPT Image 2 / image2 high-fidelity portrait consistency. Ask for vertical 9:16 output in the prompt.
6. Save project-bound final outputs under the current thread's `outputs` directory when possible; for the current user's Gary series, prefer `D:\工作用（同步）\图\长视频用图` when available. Otherwise show the generated image inline and report where it was saved.

## Prompt Template

```text
Use GPT-Image-2 / image2 high-fidelity portrait identity consistency. Use the fixed male lead reference from this skill as the man. Use the user-provided female character as the woman. Generate a new photorealistic candid vertical 9:16 image, not an edit of the source references.

For the Gary series, use this Chinese structure when the user wants to vary only scene and flirtatious interaction:

生成9:16竖版手机照片。
{scene}的真实抓拍照片，{ambiguous_interaction}。使用图1和图2作为人物参考，保持两位人物的真实面貌、五官比例、发型、年龄感、体型和气质一致，不要美化成模特或网红脸。两人的动作不完全统一，像朋友聚会或临时合影时被旁边朋友随手拍下的一瞬间。场景是真实生活化背景。整体氛围像朋友圈原图、生活流纪实照片，不是商业摄影，不是宣传照。业余手机摄影风格，轻微歪斜构图，人物在图片中间位置，手机直闪效果，机顶闪光人像质感，局部高光轻微溢出，背景有轻微失焦，人物边缘有一点点运动模糊，保留真实皮肤纹理、毛孔、轻微瑕疵和自然肤色。画面不要过度锐化，不要精修，不要磨皮，不要滤镜感。人物都是普通人，不夸张打扮，女生鼻子不要过高，不要变成精致网红脸。真实手机夜拍质感，轻微颗粒感可以保留，但不要严重脏噪点。整体像朋友随手拍到的一张真实照片，生活感强，非摆拍，非电影感，非AI精修感。
负面提示词：网红脸，模特脸，过度美颜，磨皮，塑料皮肤，脸部过于完美，鼻子过高，夸张妆容，时尚大片，棚拍，专业打光，商业摄影，宣传照，杂志封面，电影感过强，CG感，3D感，动漫感，AI感过强，滤镜感，过度锐化，光线过于干净，背景虚假，刻意摆拍，夸张姿势，不自然表情，刻意直视镜头，人物重复，多余人物，多余手指，手部畸形，肢体畸形，脸部结构错误，五官变形，身份不一致，改变面貌，低清，严重噪点，画面脏污，水印，文字

Do not add full-body wording to this template. If a scene tends to produce standing full-body images, add only a minimal crop constraint such as `近距离半身抓拍，不要全身照，人物可以被自然裁切。`

Female lead:
{female_lead_description_or_reference_role}

Scene and interaction:
{interaction_scene}

Identity preservation:
Preserve the fixed male lead's real facial identity, facial proportions, short black hairstyle, mature understated age impression, body type, and temperament. Preserve the female lead's described/reference facial identity, hairstyle, age impression, body type, outfit direction, and temperament. Keep both people ordinary and natural. Do not beautify either person into a model, influencer, celebrity, or AI-polished face. Keep the woman's nose natural, not too high or sharp, unless the user specifically describes otherwise.

Style:
{fixed_style_prompt}

Negative prompt:
{fixed_negative_prompt}
```
