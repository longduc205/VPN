---
name: frontend-design
description: Use when the user requests building web components, pages, artifacts, or applications, or when styling, polishing, or beautifying any web UI to ensure a highly distinctive design that avoids generic AI aesthetics.
---

# Frontend Design

## Overview
Guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Emphasizes bold aesthetic direction, creative typography, custom color strategies, fluid motion, unexpected spatial composition, and atmospheric backgrounds.

## When to Use
- When building React components, HTML/CSS layouts, dashboards, landing pages, websites, or web applications.
- When styling, polishing, or beautifying any user interface.
- When the design feels bland, template-like, or overly conforming to standard AI aesthetic defaults.

### When NOT to Use
- For backend-only logic, CLI scripts, or tasks with no frontend interface.
- When strictly restricted to pre-existing rigid design guidelines that allow no styling modifications.

## Core Pattern
Instead of using standard defaults, make intentional, bold choices for all design layers:

| Layer | Generic / AI Slop | Distinctive / Production-Grade |
| :--- | :--- | :--- |
| **Typography** | Inter, Roboto, Arial, System defaults | Custom display fonts paired with refined body fonts, high contrast scale |
| **Color & Theme** | Purple gradients on white, safe teal on white, even distribution | OKLCH, tinted neutrals, bold contrast ratios, committed color strategies |
| **Background** | Plain solid white/dark backgrounds | Atmospheric meshes, noise textures, geometric patterns, depth overlays |
| **Layout** | Uniform card grids, standard sidebars, predictability | Asymmetric compositions, overlaps, grid-breaking elements, diagonal flows |
| **Motion** | Rigid or no transitions, sudden modal pops | CSS-only staggered loading animations, smooth easing transitions |

## Implementation Guidelines

### 1. Design Thinking & Tone
Before writing code, commit to a BOLD, unforgettable aesthetic direction. Choose a distinct tone (e.g., brutally minimal, retro-futuristic, editorial, luxurious, playful) and execute it with absolute precision.

### 2. Typography
Avoid generic fonts like `Arial` and `Inter` for headings. Opt for beautiful, unexpected, and characterful web fonts (e.g., from Google Fonts or custom font faces) that fit your chosen aesthetic.

### 3. Color Strategy
Commit to a cohesive color palette using CSS variables. Use tinted neutrals instead of absolute `#000` or `#fff`. Use a dominant color with sharp, calculated accents rather than timid, evenly distributed palettes.

### 4. Backgrounds & Atmospheric Details
Add texture and depth rather than relying on plain backgrounds:
- Use gradient meshes or custom SVG backgrounds.
- Incorporate subtle noise overlays, grain textures, or delicate grid lines.
- Use layered transparencies (`backdrop-filter`) and drop shadows with color tinting.

### 5. Layout & Spatial Composition
Break the grid! Introduce:
- Asymmetric element alignments.
- Overlapping layers and negative space.
- Diverse padding and margins to create spatial rhythm.

### 6. Fluid Motion
Bring the interface to life with tailored motion:
- Prefer lightweight CSS animations/transitions.
- Use staggered delays for initial page loads (`animation-delay`).
- Define custom bezier curves for smooth acceleration and deceleration.

## Common Mistakes
- **The SaaS/AI Template Cliché**: Endless grids of identical cards with small icons, descriptions, and a top-right gradient.
- **Generic Font Selection**: Automatically defaulting to Inter or Roboto because they are "safe."
- **Flat Aesthetics**: No depth, zero ambient shadows, and solid, untinted backgrounds.
