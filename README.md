# PPT Layered Image Pack / PPT 四联图层图片包

一个可复用的 Agent Skill：为每一页幻灯片生成四张彼此对应的 PNG，方便后续在 PowerPoint 中重新排版文字、背景与前景。

## 每页四张

| 文件名 | 内容 |
|---|---|
| `S001_full.png` | 完整设计（所有文字、背景与插图） |
| `S001_clean.png` | 仅去掉文字，其他设计保持一致 |
| `S001_foreground.png` | 无文字、无底层场景的透明 RGBA 前景 |
| `S001_background.png` | 只有底层场景，无前景模块与文字 |

**核心验收：** 将 `foreground` 原坐标叠加到 `background` 上，应尽量准确地复原 `clean`。白底照片不等于透明 PNG，独立生成的两张相似图也不等于互补图层。

## 给 AI 直接读取

**主 Skill：** [SKILL.md](SKILL.md)（建议 AI 先完整阅读它，再按需读取 `references/`）。

如果智能体支持打开 GitHub 网页，可直接发送：

> 阅读 https://github.com/CK-NOMI/ppt-layered-image-pack/blob/main/SKILL.md 以及其中引用的规则。用这个 Skill 制作 5 页《Transformer 原理》复杂 PPT，每页输出 full、clean、foreground、background 四种 PNG，严格保持一致尺寸和坐标，透明前景与纯背景互补，完成图层合成检查后交付。

## 项目结构

```text
SKILL.md
README.md
references/
  prompts.md
  layers-and-qa.md
examples/
  manifest.example.json
scripts/
  build_complementary_layers.py
  composite_preview.py
  validate_pack.py
```

## 安装为 Agent Skill

将仓库克隆到 Agent Skills 目录（具体路径依客户端而异；Codex 常见为 `~/.codex/skills/ppt-layered-image-pack/`）。

```bash
git clone https://github.com/CK-NOMI/ppt-layered-image-pack.git ~/.codex/skills/ppt-layered-image-pack
python -m pip install pillow numpy
```

## 本地分层与质量检查

```bash
python scripts/build_complementary_layers.py \
  --clean output/S001_clean.png \
  --background output/S001_background.png \
  --mask output/S001_mask.png \
  --out output/S001_foreground.png

python scripts/composite_preview.py \
  --background output/S001_background.png \
  --foreground output/S001_foreground.png \
  --out output/preview/S001_recomposed.png

python scripts/validate_pack.py --input output --max-mae 1.5
```

`--mask` 可省略，改由差分估计，但必须人工审核背景泄漏、透明玻璃与光晕边缘。自动合成接近不能单独证明图层语义正确，仍需人工检查。

**边界说明：** 图像生成/编辑能力取决于所用模型和工具；本 Skill 提供规范、流程及验证脚本，不会替 AI 自动取得图片编辑 API 或保证完美的像素级抠图。