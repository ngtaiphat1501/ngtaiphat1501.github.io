# VLUX — Personal Portfolio (Nguyễn Phát Tài)

A single static page (`index.html`). No build step, no dependencies to install.

## Deploy on GitHub Pages
1. Create a repository named `ngtaiphat1501.github.io` (public).
2. Upload `index.html` and this README to the root of the `main` branch.
3. Settings → Pages → Build and deployment → Deploy from a branch → `main` / `(root)` → Save.
4. After a minute or two the site is live at https://ngtaiphat1501.github.io

## Edit content
All text lives in `index.html`: search for the section ids `about`, `expertise`, `work`, `journey`, `contact`.
Expertise descriptions are in the `X` object in the script at the bottom.

## Notes
- The tech stack is a draggable 3D tag sphere (plain JS, no library): move the mouse over it or drag to turn it, click a tag for details, filter by area. Edit the list in the `D` array in the script (name, area, `used` or `learn`, note). With `prefers-reduced-motion` it becomes a plain list.
- The background is an interactive particle field on a 2D canvas (no WebGL, no library): three depth layers with parallax, points linked by thin lines, and the cursor repels and connects nearby points. Click or tap sends a burst. Scrolling shifts the layers and each section changes light and tint. Tune particle count in `size()` (`W*H/13000`), line reach in `draw()` (`LD`), cursor radius (`150` / `200`).
- Extra interaction in the script: magnetic buttons and links, card spotlight, and a text-decode effect on the hero and headings. All are skipped with `prefers-reduced-motion`.
- With `prefers-reduced-motion` the background is a single static frame.
- Sound is opt-in (off by default, choice remembered). When on: a generative ambient soundtrack whose filter and note density change per section, short pentatonic plucks on hover and click (nav links rise up the scale), a soft whoosh between sections, and tech-stack tags chime when selected. Music, UI sounds and volume can be set separately. Everything is synthesized in the browser, there are no audio files. Edit the progression in `CH`, section moods in `MOOD`.
