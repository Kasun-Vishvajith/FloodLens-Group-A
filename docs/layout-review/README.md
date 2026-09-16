# Layout verification

The shared layout is defined in `dist/layout.css`, loaded after the visual theme.

- Unified location/date filter panel with integrated quick ranges.
- Shared content edges, panel padding, grid gaps and aligned metric baselines.
- Balanced map, ranking, chart and episode columns; single-column narrow layouts.
- Route-specific filters: full-archive analysis, episode selection and provider forecasts do not expose irrelevant date controls. Explorer and project guide omit the district filter panel.
- Explorer search and coordinate controls use explicit responsive grids.
- Wide data tables and forecast strips scroll inside their panels.

`results.json` records real Chrome measurements for all eight routes at 1440, 1024, 768, 390 and 320 pixels. All 40 combinations passed document-width and paired-grid top-alignment checks. PNGs capture desktop and mobile views. These checks do not validate live API availability or every interactive workflow.

To repeat: serve the app on port 8000, start Chrome with remote debugging on port 9223, then run `node tools/layout-qa.mjs`.

## Apple Design revision

The user-supplied Apple Design guide informed `dist/apple.css` and `dist/interface.mjs`. The revision uses system fonts (no external font request), a translucent structural sidebar, opaque content cards, restrained teal actions, immediate press feedback and a native button-driven mobile menu. No custom drag gesture or spring dependency was introduced: maps, scrolling and sliders retain their native interactions. Reduced motion, reduced transparency and higher contrast have explicit styles.

`interactions.json` records Chrome checks for opening the menu, Escape dismissal and focus return, closing after route selection, and reduced motion/transparency rendering. Screenshots and layout measurements were regenerated for this revision.
