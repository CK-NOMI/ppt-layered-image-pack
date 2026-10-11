---
name: ppt-layered-image-pack
description: Generate a four-image pack per PPT slide: a full text-rich design, a clean text-free design, a genuinely transparent RGBA foreground, and a complementary background-only scene. Supports AI PPT slide generation, image editing, text removal, cutout/alpha extraction, and verifying that the foreground composited over the background reconstructs the clean slide.
compatibility: Requires access to image generation/editing for slide designs; Python 3 with Pillow and NumPy for compositing and validation.
metadata:
  author: ChatGPT
  version: "1.0.0"
---

# PPT Layered Image Pack / PPT 四联图生成 Skill

## When to use / 触发条件

Activate this Skill when the user asks to generate a series of PPT design images, an editable-image PPT design workflow, or any slide/image package requiring text removal and separable background and foreground. Do not stop after making full-slide designs: **for each slide, produce all four versions** unless the user explicitly requests fewer.

## Output contract — exactly four images for every slide

| Suffix | What it contains | Required properties |
|---|---|---|
| _full.png | Original complete slide: text + graphics + scene | Full slide, opaque, correct title and content |
| _clean.png | The same image with ALL text and text shadows removed | All non-text details retained in exactly the same positions |
| _foreground.png | Non-text foreground graphics isolated from the scene | Real RGBA transparency, same full-canvas dimensions |
| _background.png | The underlying scene/background alone, with foreground removed | Opaque, naturally inpainted, no text or foreground objects |

Files are named S001_full.png, S001_clean.png, S001_foreground.png, S001_background.png, then S002_*, and so on.

**Hard invariants:**
- All four images share the same pixel width, height, crop, and coordinate system, normally 16:9.
- Foreground is not a white-background image. It has an actual per-pixel Alpha channel, including antialiased semi-transparent glow, shadow, and glass edges.
- Background is not a blank white sheet unless the original scene was white. It contains the scene behind the illustrated modules, with removed areas filled naturally.
- Foreground over background should reconstruct clean: alpha_composite(background, foreground) ≈ clean.
- The full slide serves as the visual source of truth; clean must be edited from it, not independently reimagined.

## Workflow

### 1. Plan the entire slide deck

From the user's brief, infer number of slides, topic, target audience, content, language, and visual style. Reuse stated preferences. Default to Chinese explanation with accurate English technical vocabulary; use a consistent professional 16:9 design system across the entire series. Keep substantial but readable information density.

Outline headings, labels, formulas, and data before rendering. Verify technical terminology and facts. Design cards and diagrams so that text can later be re-added by native PPT text boxes.

### 2. Generate full — text-rich complete designs

Generate each full page to a consistent design reference (same typography hierarchy, palette, glow, perspective, shapes, page margins and module styles). Check spelling, numbers, math and layout; fix inaccurate details instead of accepting hallucinated text. Every subsequent edit is derived from the accepted full version. Use the FULL prompt in references/prompts.md.

### 3. Edit full to clean — remove text only

Use image EDITING, with the actual full PNG as input. Remove ALL title and body text, Chinese/English strings, numerals, labels, formula typography, page number, chart captions and any shadows caused by the removed text.

Do not remove or change the non-text illustration, glass cards, icons, arrows, lights, gradients, city/background, borders, dimensions or layout. Seamlessly inpaint only the former text pixels. If the user requests no characters whatsoever, also clear character-like icon symbols. Reject clean outputs that look like a newly composed but merely similar slide. Use the CLEAN editing prompt in references/prompts.md.

### 4. Edit clean to background — scene alone

Use the actual clean PNG as the input image. Delete ALL independent foreground modules: cards, icons, floating panels, arrows, timelines, 3D figures, connector lines, extrinsic decorations, shadows and effects belonging to these objects.

Preserve the underlying sky/city/gradient/grid/floor/texture/ambient scene, camera position, ambient lighting and original canvas geometry. Inpaint regions concealed by removed foreground to match neighboring background. Keep background opaque and text-free. Use the BACKGROUND editing prompt in references/prompts.md.

### 5. Extract foreground from clean — real RGBA

**Prefer deterministic extraction, not a new text-to-image generation.** Obtain a semantic foreground mask aligned to clean: white for movable graphic objects, black for the scene, gray for antialiasing/glass/glow/soft shadows. Use clean and background as paired images. If supported, use segmentation plus manual mask refinement.

In a local Python environment, run:

    python scripts/build_complementary_layers.py --clean output/S001_clean.png --background output/S001_background.png --mask output/S001_mask.png --out output/S001_foreground.png

The mask is optional but automatic pixel-difference masking is only a fallback; inspect for leaked background, inaccurate shadows and cut-out halos.

The PNG must occupy the whole original slide canvas with transparent pixels wherever only the background is visible. Do not crop down to a bounding box; PowerPoint should place foreground and background both at slide origin (0,0). Use the MASK/FOREGROUND prompts in references/prompts.md and formulas in references/layers-and-qa.md.

If the user needs multiple independently movable modules, optionally also export additional elements/ PNGs for each card/icon/diagram; the main four-image pack is still mandatory.

### 6. Validate all four assets

For each slide:
1. Confirm four distinct PNG files and exact matching pixel dimensions.
2. Confirm full, clean and background are opaque; foreground has RGBA with truly transparent pixels.
3. Confirm clean, background and foreground have no labels or text.
4. Compare full and clean, checking whether ONLY the letter/number regions and their shadows changed.
5. Composite the transparent foreground onto the background and compare against clean with a real pixel-difference metric.
6. Inspect transparency around glass, shadows, glow, and connecting lines; no hard white/black edges.
7. Check that background has continuous scene texture behind removed foreground, rather than vestiges of cards or diagrams.

Use:

    python scripts/composite_preview.py --background output/S001_background.png --foreground output/S001_foreground.png --out output/preview/S001_recomposed.png
    python scripts/validate_pack.py --input output --max-mae 1.5

A low recomposition MAE does NOT guarantee a good semantic split: an overly opaque foreground can hide a wrong background. Verify foreground coverage and the background independently. When checks fail, repair background or mask and repeat; never claim pixel-perfect quality without evidence.

### 7. Deliver a complete pack

Expected directory:

    output/
      S001_full.png
      S001_clean.png
      S001_foreground.png
      S001_background.png
      S002_full.png
      S002_clean.png
      S002_foreground.png
      S002_background.png
      manifest.json
      QA_REPORT.json
      preview/

Package images and reports into a ZIP if file export is available. Provide download links only to files actually generated. Report the number of complete slide packs, image dimensions, Alpha transparency and recomposition QA outcome.

If the execution environment lacks image editing or local RGBA processing, state the limitation and provide as many genuine outputs as possible. Never substitute independently generated lookalikes or white-backed images for true complementary layers.

## Boundaries / 注意事项

- A white-background slide is NOT a transparent foreground.
- A pretty AI image is NOT by itself a set of independently editable PPT objects.
- Four raster PNGs are materials for a PPT pipeline, not a fully editable PPTX. For editable text create native PowerPoint text boxes; for independent module editing export separate RGBA elements or native shapes.
- Re-rendering a whole slide tends to drift. Keep full as a fixed visual reference and edit from the same accepted asset.
- Avoid fake alpha checkerboards and invented success claims.

## References

- [Prompt templates](references/prompts.md): full, clean, background, foreground, alpha mask and QA.
- [Layer math and QA](references/layers-and-qa.md): compositing formula, feasible alpha, semantic checks and limitations.
- [Manifest example](examples/manifest.example.json): output structure.

## Example user prompt

“阅读这个仓库的 SKILL.md，并按 ppt-layered-image-pack 为《LLM 与 Transformer》制作 5 页复杂科技风 PPT。每页生成 full、clean、foreground、background 四张同尺寸 PNG；无文字前景须有真正透明 Alpha，只有背景的图必须是互补图层；验证复合结果并压缩为 ZIP。”
