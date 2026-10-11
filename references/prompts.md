# Prompt templates / 四联图片生成与编辑提示词

Replace all {{...}} placeholders with the actual slide brief. Use the **accepted upstream image as editing input**. Do not independently generate visually similar substitutes.

## FULL — full PPT slide with all text

> 为《{{演示主题}}》设计第 {{页码}} 页完整的 {{宽高/16:9}} PPT 图片。标题：{{标题}}。必须讲清楚的内容：{{事实、正文、公式、数据、层级}}。整体保持 {{配色、科技风、玻璃拟态、复杂图解等}} 的连续设计语言。版式复杂而专业，内容有明确层次和足够留白，所有文字清晰准确。每页风格一致，输出完整画布。不要加水印、无关字符或随机标签。

## CLEAN — edit full to remove text only

> 请直接编辑作为输入的完整 PPT 页，严禁重新设计和重绘布局。删除全部标题、正文、中英文词语、数字、公式、图例、坐标标签、页码、文字阴影与残影。不新增任何字符。除文字本身及其投影外，保留所有原像素的非文字设计元素：背景、光照、城市、天空、玻璃卡片、边框、箭头、图标、插画、3D 模型、连接线、装饰、比例与位置。只在原文字范围进行无痕修复，使材质自然连接。像素大小、裁切和构图必须与原图一致。如果用户要求零字符，则移除图标内部可识别的字母/符号。

## BACKGROUND — edit clean into background-only scene

> 请直接编辑输入的无文字原图，提取画面底层场景。保留原始取景、色彩、渐变、光影、天空、地平线、城市、地板网格、远景粒子与纹理。移除所有独立前景，包括卡片、界面板、按钮、光效主体、主插画、流程模块、图标、连线、箭头、时间轴及其附带阴影。所有前景被移除的位置都要使用同一背景场景自然修复，避免留下前景残影或涂抹块。不要添加文字。不要强行改白底（原始背景为白色的情况除外）。保持相同全画幅尺寸和透视。

## FOREGROUND — isolate text-free RGBA foreground

> 请以输入的 clean 无字设计页为唯一视觉基准，按原坐标提取所有独立非文字前景：玻璃卡片、主体插画、图标、连线、箭头、标记、时间轴、光晕、投影和半透明高光。移除整张场景背景和全部文字。前景必须是 RGBA，拥有真正的 Alpha 通道；纯背景部分透明度为 0，半透明玻璃与光晕保留渐变 Alpha。绝对不能使用白色/黑色/棋盘格模拟透明。保持每个物体原大小、位置、颜色、边缘、间距；输出仍为整页原始画布尺寸，不可裁切或重新排版。必要时先做遮罩再计算真实前景。

## MASK — preferred gray-scale semantic foreground matte

> 为输入 clean 生成逐像素对位的灰度蒙版，尺寸完全相同。白色 255 = 独立前景物体（卡片、图标、插画、连接线、箭头等）；黑色 0 = 只有背景场景；0-255 灰色 = 物体边缘、发光、软阴影、透明玻璃。不要写字或改变布局。掩膜应准确贴合原位置，禁止凭空创造新的物体。使用前复核遮罩语义与边缘，并检查是否遗漏微小图标或光晕。

## QA — compositing check

> 将 foreground 按原坐标叠在 background 上，并与 clean 对比。检查全局构图、图标位置、连线、玻璃边缘、光晕、模糊度、背景纹理和所有卡片。不得有白边、黑边、双重阴影、内容错位、漏元素、透明度伪造或文字残影。必须使用实际图像像素差分程序计算复合误差，不能仅凭生成器声称通过。

## Batch instruction

> 使用 ppt-layered-image-pack Skill，生成 {{N}} 页《{{主题}}》复杂演示 PPT 设计图片。按统一 {{风格}} 连续出图。每页必须输出 SXXX_full.png、SXXX_clean.png、SXXX_foreground.png（真实透明 RGBA）、SXXX_background.png（底层场景）。同页四图严格对齐并逐页检查 foreground+background≈clean。最终交付 PNG、合成检查报告和 ZIP。
