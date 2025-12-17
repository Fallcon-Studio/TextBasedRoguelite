# Development Journal

- 2025-12-15 05:13 UTC - Read the README to understand the text-based roguelite goals and created initial Python project scaffolding (src layout, packaging stub, gitignore) to start implementing the game.
- 2025-12-15 05:14 UTC - Implemented the first playable prototype with procedural locations, combat, events, and CLI options (seed, steps, auto). Ran a seeded auto-play run to verify the loop.

- 2025-12-17 02:19 UTC - Implemented frontier builder that stabilizes frontier size calculations and added placeholders for gatekeeper flow.

- 2025-12-17 02:29 UTC - Added a Tkinter GUI entry point with panels for journal logs, status, inventory, and frontier choices, and updated the CLI to launch the GUI for interactive runs while preserving auto-mode.

## Time and Date:
 - Tue Dec 16 20:44:44 CST 2025

## Changes made:
 - Added explicit time modifier tracking for combat, rest, and event outcomes, aggregating them during location resolution.
 - Introduced per-location zone time cost storage and event resolution guard to prevent multiple event triggers.

## Reason for changes:
 - Implement requested time tracking clarity and enforcement of single event resolution per location.

## Notes:
 - Zone time cost now derives from biome travel cost except rest locations which use zero, aligning decay processing.
