# Procedural Text Roguelike

A fully procedural roguelike built entirely with text, UI elements, and system-driven gameplay. No graphics, sprites, or artwork are used. All gameplay is driven by mechanics, stats, and emergent interactions.

## Running the prototype

1. Ensure Python 3.11+ is available.
2. Install the project in editable mode (optional but recommended):
   ```bash
   pip install -e .
   ```
3. Launch a run:
   ```bash
   python -m roguelite.cli --seed 42 --steps 6 --auto
   ```
   - Omit `--auto` to make manual combat choices.
   - Adjust `--seed` for deterministic worlds.
   - Tune `--steps` to change the length of the route.

## Core Concept

The player explores a procedurally generated world composed of abstract locations, encounters, and events. Progression is driven by decision-making, resource management, and tactical combat described entirely through text. The goal is survival, mastery, and discovery rather than scripted narrative.

## Key Systems in the Prototype

- **Procedural world generation**: Runtime creation of nodes with flavored descriptions and encounter types.
- **Text-driven loop**: Every interaction is conveyed through narration, not visuals or ASCII art.
- **Turn-based combat**: Stat-driven skirmishes with attack, guard, and recovery actions. Enemies follow the same rules as the player.
- **Events and rests**: Non-combat encounters can reward, injure, or buff the player between fights.
- **Determinism options**: Seeds make routes and combat variance reproducible for testing or challenges.

## Development Philosophy

This project prioritizes clarity, correctness, and systemic depth over presentation. Every mechanic must be explainable in text and defensible in logic. If a feature cannot be expressed cleanly without visuals, it does not belong here.
