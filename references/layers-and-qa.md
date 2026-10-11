# Layer compositing and quality assurance / 图层互补技术说明

## Why all images must share a single edit chain

Independent text-to-image attempts drift in pixel geometry, object proportions, glows and gradients. Use one accepted full slide as the source: full → clean → background, then clean + background + aligned foreground mask → foreground.

## Alpha compositing

For each RGB pixel in [0,255]:

    C = alpha * F + (1-alpha) * B

C is the clean slide, B the background, F the isolated foreground RGB. For alpha > 0:

    F = [ C - (1-alpha)*B ] / alpha

To avoid impossible RGB channels outside [0,255], the minimum physically feasible alpha is the maximum over the channels:

- If C > B: alpha_min = (C-B)/(255-B), denominator only if > 0.
- If C < B: alpha_min = (B-C)/B, denominator only if > 0.

A provided semantic alpha mask should usually dominate. The provided build script raises opacity to alpha_min where necessary and clamps/rounds the computed foreground RGB. This yields close numerical recomposition, **but does not prove good foreground/background separation**.

If the edited background differs from clean even where there are no real foreground objects, the method can hide that mismatch in an erroneously widespread foreground. Reject this result even if the recomposition error is low.

## What belongs in foreground

- Independent glassmorphism panels, cards, diagram nodes, UI icons, connectors, arrows and timelines
- Floating holograms and 3D structures
- Their luminous halo, cast shadow, soft particles and edge effects
- Semi-transparent parts of each object, accurately matted

The continuous underlying scene — sky, horizon, city, diffuse ambient gradient, stage grid or distant scenery — belongs to background. User-specified alternative boundaries take priority, but must remain complementary.

## Quality checks

1. Same 16:9 canvas (or user-specified dimensions) and exact same width and height across the four PNGs.
2. Foreground has real per-pixel RGBA Alpha and non-zero fully transparent area. No opaque simulated checkerboard.
3. Full, clean and background are fully opaque.
4. Recompose mean absolute RGB error (MAE, range 0..255) is preferably below 1.5.
5. Look at Alpha coverage. If foreground unexpectedly spans >90% of the image, check for leaked background.
6. Inspect whether all original non-text elements survived full → clean at their original coordinates.
7. Inspect background removal and inpainting: scene continuity under modules and absence of UI remnants.
8. Inspect foreground edges, glass translucency, shadow feathering and glow; no hard white or black outlines.
9. Confirm clean, background and foreground have no text or stray characters.
10. Review QA_REPORT.json and manually verify any warnings.

The provided scripts perform structural and numerical checks; text removal and scene semantics still require human inspection.

## PPT integration

Place background and foreground images at the same slide origin (0,0), both at 100% slide width/height. Put background at the rear and foreground above. Then add native PowerPoint text boxes on top if text editing is required.

For movable individual graphics beyond the single composite foreground image, export optional separate RGBA objects (elements/) and/or recreate vectors as SVG/native PowerPoint shapes. Four whole-slide PNGs alone are not a fully editable PPTX.
