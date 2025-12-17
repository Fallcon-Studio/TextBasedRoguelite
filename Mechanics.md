Text Roguelike — Core Design & System Specification

This document defines the authoritative rules and systems for the text-driven roguelike project. It is intended to be handed to other AI assistants or programmers and used as a single source of truth. All mechanics described here are explicit, deterministic, and designed to avoid ambiguity or hidden penalties.

1. Core Design Principles

GUI-first, text-driven: The game must be implemented with a lightweight GUI. No custom art assets are required. All information is presented via standard UI controls (panels, lists, tables, buttons). A terminal-only version is explicitly out of scope.

Explicit information: The player always knows exact costs, exact threats, and exact outcomes before committing.

No hidden timers: All time advancement and decay is declared up front.

Difficulty from pressure, not guessing: Challenge comes from time pressure, resource constraints, and irreversible consequences.

Fairness contract: If the player fails, they can always explain why.

2. Time Model (Authoritative)

2.1 Time

Time advances only when an action explicitly says it does.

There are no implicit or cleanup time ticks.

2.2 Zone Time Cost

Every zone lists a Time Cost.

This cost includes:

Travel

Combat

Event resolution

Rest resolution

Once the zone resolves, no additional time passes.

2.3 Combat & Events

Combat duration (number of turns) does not affect time.

Event options may add, reduce, or keep time at 0, but this is always explicit.

3. Decay System

3.1 Decay Stages

Each location exists in one of five stages:

Fresh

Unstable

Degraded

Critical

Removed (unreachable)

3.2 Decay Advancement

Locations advance through decay stages as time passes.

When a location reaches Removed, it is no longer reachable and is never shown.

3.3 Frontier State Display (Critical Rule)

At decision time T:

All frontier locations are displayed as their current, selectable state at the moment of choice.

Locations that are already Removed are not shown.

Locations do not decay while they are being resolved (combat/event/rest).

Time and decay advancement from a selection is applied after that zone is fully resolved (see Section 15). This guarantees:

No surprises mid-resolution

No locations decaying while the player is interacting with them

No unreachable choices displayed

4. Frontier Generation

4.1 Frontier Size

The number of available locations ranges from 1 to 7.

Average is 3–4.

4.2 Factors Affecting Frontier Size

Awareness: Higher awareness can reveal additional viable routes.

World Instability (W): Higher instability collapses routes.

Biome effects and other global conditions may apply ±1 adjustments.

Unreachable (Removed-on-arrival) locations are filtered out before display.

5. World Instability (W)

5.1 Definition

World Instability (W) is a global value from 0 to 10 representing how collapsed the world’s routes have become.

5.2 What Increases W

A location reaches Removed while unchosen: +1 W

A location degrades a stage while unchosen: +0.25 W

5.3 What Does NOT Affect W

Player stats

Combat length

Resting directly

Random counters

W is driven purely by observable decay outcomes.

6. Rest Zones

6.1 Entry Rules

Rest zones have 0 travel cost.

Entering a rest zone does not advance time or decay.

6.2 Rest Actions

Rest zones present multiple rest options.

Each option explicitly lists:

Time cost

HP gain

Stamina gain

Any decay modifiers

6.3 Decay Mitigation

Some rest options reduce location decay advancement only.

Example:

Time Cost: 3

Decay Effect: All locations decay by only 2 ticks

Important:

Time still advances fully

World Instability still updates as if full time passed

Only location decay is reduced

6.4 Biome-Specific Rest Examples

Plains

Rest 1: +9 stamina (Time 1)

Rest 2: +12 stamina, +5 HP (Time 2)

Rest 3: +15 stamina, +10 HP (Time 3, decay −1)

Swamp

Rest 1: +4 stamina (Time 1)

Rest 2: +8 stamina, +3 HP (Time 2)

No extended rest option

7. Combat System

7.1 Turn Structure

Player and enemies alternate turns.

Player chooses exactly one action per turn.

7.2 Resources

Stamina is the primary combat resource.

Actions consume stamina as listed.

7.3 Enemy Intents (Explicit)

Enemy intents are always shown.

Intents include exact damage, exact status effects, and exact values.

Example:

Heavy Strike — Deal 12 damage

No ambiguity is allowed.

8. Events

8.1 Explicit Costs

Every event option lists:

Time cost

Resource costs

Possible consequences

8.2 No Guessing

Events never require blind guessing.

The player knowingly accepts costs and risks.

9. Player Stats (Classless)

There are exactly four stats:

Health: Error tolerance

Stamina: Action economy

Skill: Combat efficiency

Awareness: Information quality and route discovery

No classes, no respecs, no hidden synergies.

10. Bosses, Exit, and Run End (Authoritative)

There is no fixed depth, no final room, and no guaranteed boss. Runs end when one of several end-condition tracks completes. These tracks operate in parallel and reflect player behavior over time.

A run may end via:

Forced boss encounter

Optional boss encounter

Escape (loss of choice)

Which ending occurs depends entirely on how the player managed time, decay, and threats.

21. End Condition Tracks & Boss Emergence (Critical)

This section defines all run-ending conditions, their triggers, priority rules, and interactions. No implementation may invent additional endings or override these rules.

21.1 The Hunter (Time Pressure Boss — Forced)

Purpose: Punishes excessive delay beyond normal action time.

Trigger Logic:

Each zone has an implicit Normal Time (baseline expected cost).

Any excess time spent beyond this normal value advances the Hunter by 1 tick per excess time.

Example: Zone normal time = 1, chosen option time = 3 → Hunter advances by 2.

Rest options always count full excess time (normal = 0).

Awareness & Visibility:

Low Awareness: vague narrative warnings only.

Medium Awareness: urgency warnings ("approaching", "soon").

High Awareness: Hunter is named explicitly and remaining ticks may be shown.

Resolution:

When the Hunter reaches the player:

The Hunter encounter replaces the entire frontier.

The run is immediately forced into the Hunter boss fight.

Priority Rule:

The Hunter always overwrites the Exit if both would occur on the same turn.

Exception:

If the Convergence spawns on the same turn the Hunter catches the player, both encounters are shown and the player may choose which boss to face.

21.2 The Exit (Loss-of-Choice Ending)

Purpose: Represents recognition and escape when no meaningful choices remain.

Eligibility Conditions (all must be true):

Frontier size == 1

World Instability (W) >= threshold

Awareness >= threshold

Rules:

The Exit only ever appears when it would be the sole remaining frontier option.

The player never chooses to delay the Exit; it appears only when choice is already gone.

If the Hunter triggers on the same turn, the Exit does not appear.

Outcome:

Selecting the Exit immediately ends the run.

21.3 The Gatekeeper (Decay Mitigation Consequence Boss)

Purpose: Punishes excessive decay mitigation that artificially delays collapse.

Trigger Logic:

Exit eligibility conditions are met except the world has been excessively stabilized via decay mitigation.

Rules:

The Gatekeeper replaces the Exit.

It never appears as a separate frontier option.

The player cannot avoid or bypass it once triggered.

Outcome:

The Gatekeeper encounter ends the run (win or lose).

21.4 The Convergence (Ignored Threat Boss — Universal Exception)

Purpose: Represents compounded consequences of ignored elite threats.

Trigger Logic:

Track elite encounters that decay to Removed while unchosen.

When the ignored-elite threshold is met, the Convergence becomes eligible to spawn.

Spawning Rules:

The Convergence never replaces an existing location.

It injects itself as an additional frontier option, similar to Awareness bonus nodes.

It may spawn:

During normal play

Alongside the Exit

Alongside the Hunter

Convergence spawn chance is influenced by Awareness.

Behavior:

The Convergence is a terminal boss encounter.

Choosing to fight it ends the run (win or lose).

It is optional if present.

It is subject to decay like any other zone and may disappear if ignored.

Special Exception Rule:

The Convergence is the only system allowed to violate frontier-size constraints.

21.5 End Condition Priority Summary

Hunter

Forced encounter

Overrides all normal play and the Exit

May coexist only with Convergence

Exit

Appears only when it is the sole option

Never appears if Hunter triggers

May coexist with Convergence

Gatekeeper

Replaces Exit only

Never appears independently

May coexist with Convergence

Convergence

Additive, never replacing

May appear in any frontier state

The sole universal exception

11. Meta-Progression

No permanent stat bonuses.

No power carryover between runs.

Optional unlocks are content only (new events, enemies, biomes).

Each run stands on its own.

12. UX & Text Rules

Mechanics before flavor.

Consistent terminology.

Hard word limits on descriptions.

Failure messages explain what happened and why.

If text obscures mechanics, it is incorrect.

13. Implementation Notes

All systems are deterministic and seedable.

All calculations should be inspectable in logs.

No system may contradict the explicit-information contract.

14. GUI Layout Specification (Required)

The game must be implemented as a lightweight GUI using standard UI controls only (panels, lists/tables, buttons). No custom art assets are required. The GUI exists to reduce reading friction and keep all mechanical information visible and explicit.

14.1 Window Layout

Single window with four regions:

A) Left — Player & World HUD (persistent)

Player

HP (current/max)

Stamina (current/max)

Stats: Health / Stamina / Skill / Awareness

World

Time (T)

World Instability (W, 0–10)

One-line reminder: “Frontier shows arrival state.”

Active Effects

List of statuses: name, duration, exact effect text

B) Center — Log (persistent, scrollable)

Timestamped log of outcomes and narration.

Two tabs or filters:

All

Mechanics-only (costs, damage, status changes, time advances, decay mitigation applied)

C) Right — Context Panel (mode-dependent)

Shows the current mode’s primary information (Frontier / Combat / Event / Rest).

D) Bottom — Action Bar (persistent)

Primary actions as buttons for the current mode.

Hotkeys shown on buttons (e.g., [1], [2], [3]).

Optional setting: “Require confirm for time-costing choices” (default off).

14.2 Mode: Frontier (Choose Next Zone)

Right Context Panel: Frontier List

Display as a table or list supporting 1–7 entries.

Each entry must include:

Name

Biome

Encounter Type (Enemy / Event / Rest)

Danger

Arrival Decay Stage (Fresh / Unstable / Degraded / Critical)

Time Cost (for selecting this zone; Rest entry shows 0 to enter)

Unreachable zones (Removed-on-arrival) are never shown.

Selection Details Box (below the list)

One-sentence (short) flavor description.

Any explicit previews needed for that node (if applicable).

Buttons

Go (commit to selected zone)

Enter Rest (if the selected node is a rest zone; 0 time)

14.3 Mode: Combat

Right Context Panel: Combat Breakdown

Enemy Roster

List enemies with:

Name / archetype

HP

Intent Display (explicit, non-negotiable)

For each enemy, show the next intent with exact values:

Exact damage numbers

Exact status applications (name, duration, value)

Any exact guard changes or other effects

Player Action Detail

Actions mirror the Action Bar, each showing exact effects and stamina costs:

Attack: stamina cost; exact damage outcome

Guard: stamina cost; exact guard gained

Recover: exact stamina/HP gained

Use Item: exact effect; charges

14.4 Mode: Event

Right Context Panel: Event Options

Event title + 1–2 sentence description.

Options displayed as rows/cards, each explicitly listing:

Time cost (exact)

Resource costs (exact)

Consequences/outcomes (explicit; no guessing)

On selection (and/or on confirm), show a one-line summary of what will be applied.

14.5 Mode: Rest

Step 1: Enter Rest Zone

0 time cost to enter.

Right Context Panel: Rest Menu

Present multiple rest options (biome/W dependent), each explicitly listing:

Time cost

HP gain

Stamina gain

Any decay modifier (e.g., “Location decay advances by only 2 ticks instead of 3.”)

On selection (and/or on confirm), show a one-line summary including:

Time +N

Location decay +M (if modified)

HP +X

Stamina +Y

14.6 Presentation Rules

Mechanics-first: keep mechanical fields in fixed, scannable positions.

Avoid wall-of-text: narration goes to the log; mechanics stay in HUD/context.

No ambiguity: the UI must never hide costs or intent values.

This document is the canonical reference for implementation and future refinement.

15. Authoritative Gameplay Loop (Execution Order)

This section defines the exact order of operations for a single decision cycle. Implementations must follow this order precisely.

15.1 Run Start

Initialize RNG with run seed.

Initialize player stats, HP, stamina.

Set Time = 0.

Set World Instability (W) = 0.

Generate initial frontier (Section 4) projected to arrival state at Time + zone cost.

15.2 Decision Cycle

Each cycle proceeds as follows:

Display Frontier

Show all reachable locations (not Removed) in their current state.

Each entry displays its declared time cost (and rest entry cost where applicable).

Player Selects Zone

Selection commits to resolving that zone.

Resolve Zone (no time/decay advances during resolution)

Enemy: resolve full combat (combat turns do not advance time).

Event: present options; player selects an option; apply immediate option outcomes.

Rest:

Enter rest zone (0 time).

Present rest options; player selects a rest action; apply immediate gains.

Compute Applied Time/Decay for This Selection

Determine the final time cost to apply for this selection:

For combat zones: use the zone’s declared time cost.

For events: apply the zone’s base time cost plus any explicit option time modifier.

For rest: use the chosen rest option’s time cost.

Determine decay advancement for this selection:

Normally equals the applied time cost.

If the chosen rest option includes decay mitigation, use the reduced decay advance value (time still advances fully).

Advance Time & Decay; Update W (after resolution)

Time += applied time cost.

All locations advance decay by the computed decay advancement.

World Instability (W) is updated based on decay outcomes:

Each stage degradation while unchosen: +0.25 W

Each removal while unchosen: +1 W

Cleanup

Apply XP, items, status removals if applicable.

No additional time or decay occurs here.

Generate New Frontier

Generate next frontier for the next decision point.

Repeat until run ends.

16. Combat Math & Resolution Rules

16.1 Core Values

Base Attack Cost: 2 stamina

Base Attack Damage: 6

Base Guard Cost: 2 stamina

Base Guard Value: 8

Recover Action: +4 stamina, +2 HP

16.2 Skill Scaling

Each point of Skill adds +1 damage to attacks.

Skill does not reduce stamina costs.

16.3 Guard Rules

Guard is a temporary buffer.

Damage is applied to Guard first, then HP.

Guard does not persist between turns unless explicitly stated.

16.4 Damage Application

Damage = (Base Damage + Skill bonus) − target guard.

Damage cannot be negative.

16.5 Stamina

Stamina regenerates only via Recover actions or explicit effects.

No passive regeneration.

17. Stat Definitions (Mechanical)

17.1 Health

Each Health point increases max HP by +5.

17.2 Stamina

Each Stamina point increases max stamina by +3.

17.3 Skill

Each Skill point increases attack damage by +1.

17.4 Awareness

Awareness governs information quality, planning precision, and route discovery. It never alters combat math or outcomes directly.

A) Frontier Detail Quality

At baseline, frontier entries show: biome, encounter type, danger, arrival decay stage, and time cost.

At higher Awareness levels, frontier entries additionally show:

Enemy archetypes present (no numeric values)

Environmental or biome-specific mechanical modifiers (if any)

B) Decay Precision Visibility

At baseline, decay is shown only as a stage (Fresh / Unstable / Degraded / Critical).

At higher Awareness levels, decay display becomes more precise:

Shows exact remaining time units until the next decay stage

Example: “Unstable — degrades in 1 time”

C) Frontier Size (existing effect)

Awareness increases frontier target size:

Awareness ≥2: +1 potential node

Awareness ≥4: +1 potential node

D) Event Option Access (rare, explicit)

Some events may include additional options that are only generated if Awareness meets a minimum threshold.

These options either exist or do not exist; the player is never told they "missed" an option.

This mechanic must be used sparingly.

Awareness provides better information and better choices, never hidden bonuses.

18. Decay Timing Defaults

Unless overridden by biome or zone type:

Fresh: 2 time units

Unstable: 1 time unit

Degraded: 1 time unit

Critical: 1 time unit

Removed thereafter

Decay mitigation reduces units advanced, not stage thresholds.

19. Frontier Generation Algorithm

Compute target frontier size (Section 4).

Generate candidate locations = target + 2.

Project each candidate to arrival state.

Filter removed-on-arrival locations.

Trim to target size.

20. Minimal Data Model (Reference)

20.1 Player

  {
  hp, max_hp,
  stamina, max_stamina,
  stats: { health, stamina, skill, awareness }
}

20.2 Location

{
  id,
  biome,
  encounter_type,
  danger,
  decay_stage,
  decay_timer,
  time_cost
}

20.3 Enemy

{
  archetype,
  hp,
  intents[]
}

20.4 Event Option

{
  time_cost,
  stamina_cost,
  hp_cost,
  outcomes[]
}

