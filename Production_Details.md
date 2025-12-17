Text Roguelike — Core Design \& System Specification



This document defines the authoritative rules and systems for the text-driven roguelike project. It is intended to be handed to other AI assistants or programmers and used as a single source of truth. All mechanics described here are explicit, deterministic, and designed to avoid ambiguity or hidden penalties.



1\. Core Design Principles



GUI-first, text-driven: The game must be implemented with a lightweight GUI. No custom art assets are required. All information is presented via standard UI controls (panels, lists, tables, buttons). A terminal-only version is explicitly out of scope.



Explicit information: The player always knows exact costs and exact threats before committing. Outcomes are fully explicit once they are presented, but undiscovered content (e.g., future events within a location) is not previewed in advance.



No hidden timers: All time advancement and decay is declared up front.



Difficulty from pressure, not guessing: Challenge comes from time pressure, resource constraints, and irreversible consequences.



Fairness contract: If the player fails, they can always explain why.



2\. Time Model (Authoritative)



2.1 Time



Time is integer-based only and never fractional.



Time advances only after a zone is fully resolved.



There are no implicit, cleanup, or per-turn ticks.

2.2 Zone Time Cost



Every zone lists a Time Cost.



This cost includes:



Travel



Combat



Event resolution



Rest resolution



Once the zone resolves, time is advanced once by the final applied amount.



2.3 Combat \& Events



Combat length (number of turns) does not affect time.



Event options may add, reduce, or keep time at 0; this is always explicit.



3\. Decay System



3.1 Decay Stages



Each location exists in one of five stages, each with a variable duration rolled immediately upon entering the stage:



Secure — 3–6 time units



Solid — 2–4 time units



Unstable — 1–4 time units



Critical — 1–2 time units



Removed — unreachable



All rolls are seeded and deterministic per run.



3.2 Decay Advancement



Locations advance decay only when time advances.



When a stage timer reaches 0, the location advances to the next stage and immediately rolls a new duration.



When a location reaches Removed, it is immediately unreachable and never shown again.



Instability Influence:



At low World Instability (W), decay rolls cluster near the midpoint.



At high W, rolls bias toward extremes (very short or very long), reducing predictability rather than simply accelerating decay.



Awareness \& Decay Visibility:



At low Awareness, the player sees decay stage only.



As Awareness increases, the player receives increasingly precise hints about remaining duration.



At sufficiently high Awareness, the exact remaining decay time is displayed.



3.3 Frontier State Display (Critical Rule)



At decision time T:



All frontier locations are displayed as their current, selectable state at the moment of choice.



Locations that are already Removed are not shown.



Locations do not decay while they are being resolved (combat/event/rest).



Time and decay advancement from a selection is applied after that zone is fully resolved (see Section 15). This guarantees:



No surprises mid-resolution



No locations decaying while the player is interacting with them



No unreachable choices displayed



4.2 Factors Affecting Frontier Size



Awareness: Increases the number of visible frontier locations (exact formula TBD).



World Instability (W): Reduces viable routes as instability increases (exact formula TBD).



Biome effects: Certain biomes may modify frontier size within that biome (e.g., Desert biome: −1 frontier option).



4\. Frontier Generation



4.1 Frontier Size



Base frontier size is 4.



Final frontier size is clamped between 1 and 7.



Frontier size is influenced by Awareness, World Instability (W), biome effects, and global modifiers.



4.2 Factors Affecting Frontier Size



Awareness: Increases the number of visible frontier locations (exact formula TBD).



World Instability (W): Reduces viable routes as instability increases (exact formula TBD).



Biome effects: Certain biomes may modify frontier size within that biome (e.g., Desert biome: −1 frontier option).



4.3 Frontier Generation Order



Frontier generation follows this exact order:



Calculate target frontier size.



Generate candidate locations.



Filter candidates that should not appear (e.g., would decay before arrival, insufficient Awareness, biome restrictions).



If remaining valid candidates < target size, repeat steps 2–3.



Display resulting frontier to the player.



Unchosen locations persist across frontier refreshes until they decay or are resolved.



4.4 Encounter Visibility Rule



All frontier locations explicitly list encounter category:



Normal Enemy



Elite Enemy



Boss Encounter



Event



Rest



Unreachable (Removed-on-arrival) candidates are filtered out before display.



5\. World Instability (W)



5.1 Definition



World Instability (W) is a global value from 0–10 representing loss of structural predictability, not difficulty.



W is not a difficulty scaler.



W is not a punishment meter.



W is irreversible during a run. It can be slowed, but never reduced.



W is currently capped at 10.



High W does not mean the player has played “badly”; it indicates a late-stage or heavily neglected world state.



5.2 What Increases W



World Instability increases only through explicit, observable decay outcomes that occur while locations are unchosen:



A location degrades to the next decay stage while unchosen: +0.25 W



A location reaches Removed while unchosen: +1 W



If a location is chosen and resolved by the player, it cannot contribute to W.



5.3 What Does NOT Affect W



The following never affect World Instability:



Player stats



Combat length or turn count



Resting directly



Hidden or abstract random counters



While decay stage transitions and durations are stochastic (seeded), World Instability increases deterministically based on visible decay results.



5.4 Effects of World Instability



World Instability does not directly alter combat values or player stats. Instead, it influences world structure and volatility:



Frontier pressure: Higher W reduces viable route density, shrinking average frontier size.



Decay volatility: Higher W increases the likelihood of extreme decay duration rolls (very short or very long), and reduces middle-range outcomes.



World Instability does not gate the appearance of the Exit or Gatekeeper directly; it affects them only indirectly by influencing how quickly the frontier collapses.



5.5 Threshold Behaviors (Provisional)



The following threshold behaviors are placeholders intended to reserve design space and communicate intent. They are not final balance rules and may change as the rest of the system solidifies.



These behaviors are cumulative once reached.



W ≥ 3: Volatility becomes noticeable.



W ≥ 6: Route collapse becomes frequent.



Exact numerical effects, formulas, and UI surfacing for these thresholds are intentionally undefined at this stage.



World Instability is understood to influence many systems conceptually (including frontier size and decay volatility), but only the effects explicitly listed elsewhere in this document are currently authoritative.



6\. Rest Zones



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



Decay Mitigation:



Appears rarely.



Is a flat value when present.



Only available in safer or special biomes.



Each rest option has a fixed mitigation amount.



Decay mitigation affects location decay only, never time or W.



Rest zones are removed from the frontier once resolved, like all other zones.



Example:



Time Cost: 3



Decay Effect: All locations decay by only 2 ticks



Important:



Time still advances fully



World Instability still updates as if full time passed



Only location decay is reduced



6.4 Biome-Specific Rest Examples (These are placeholder numbers.)



Plains



Rest 1: +9 stamina (Time 1)



Rest 2: +12 stamina, +5 HP (Time 2)



Rest 3: +15 stamina, +10 HP (Time 3, decay −1)



Swamp



Rest 1: +4 stamina (Time 1)



Rest 2: +8 stamina, +3 HP (Time 2)



No extended rest option



7\. Combat System



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



7.4 Player Actions (Current):



Attack: Deal a fixed amount of damage to a selected enemy, reduced by block.



Defend: Gain block to reduce incoming damage.



Recover: Restore a portion of stamina.



Use Item: Consume a selected consumable for its effect.



Damage is deterministic (no ranges). Placeholder base attack damage: 6.



Enemy intents are always explicit, showing exact damage and effects.



Combat never directly modifies time.





8\. Events



8.1 Explicit Costs



Every event option lists:



Time cost



Resource costs



Possible consequences



8.2 No Guessing



Events never require blind guessing.



The player knowingly accepts costs and risks.



9\. Player Stats (Classless)



There are exactly four stats:



Health — error tolerance; fixed starting value per run (exact value TBD). Does not permanently increase; may have temporary run-based modifiers.



Stamina — action economy; capped by the stat, recovered through rest, time, and Recover action.



Skill — currently affects attack damage; may be renamed if this remains its sole function.



Awareness — increases visible frontier options, improves decay-time clarity, and may unlock hidden zones or event options at thresholds.



No classes, no respecs, no hidden synergies.



10\. Meta-Progression \& Observer Loop



The game is a roguelite. Each run is an observation deployment.



Meta-progression measures observer knowledge, not power.



Knowledge is gained based on what was observed and recovered during a run.



Unlocks expand content possibilities only (biomes, enemies, events, items).



No permanent stat bonuses.



Observation data is transmitted continuously:



Escape or boss resolution → full data retained



Death → partial data retained (category-based; exact rules TBD)



Meta-progression is open-ended until all data thresholds are met.



Death → partial data retained



11\. Run-Ending Entities (Overview)



There is no fixed depth or scripted final room. Endings emerge from system pressure and failsafes.



11.1 The Hunter (Pursuit Failsafe)



Triggered by exceeding a zone’s Time Cost (normal time).



Advances once per unit of excess time spent.



Progress threshold for catching the player is TBD.



Hunter progress is communicated via escalating narrative warnings in Frontier mode.



When it catches the player, it overwrites all other options.



Only exception: Convergence may coexist.



Ends the run.



Trigger Logic:



Each zone has an implicit Normal Time (baseline expected cost).



Any excess time spent beyond this normal value advances the Hunter by 1 tick per excess time.



Example: Zone normal time = 1, chosen option time = 3 → Hunter advances by 2.



Rest options always count full excess time (normal = 0).



Awareness \& Visibility:



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



11.2 The Gatekeeper (Decay Mitigation Consequence Boss)



Purpose: Punishes excessive decay mitigation that artificially delays collapse.



Trigger Logic:



Frontier size == 1 (Exit condition met)



Excessive decay mitigation has occurred during the run. Threshold is explicit and deterministic (exact value TBD).



Rules:



The Gatekeeper replaces the Exit.



Its appearance is based only on decay mitigation, not on World Instability or Awareness.



It never appears as a separate frontier option.



The player cannot avoid or bypass it once triggered.



Outcome:



The Gatekeeper encounter ends the run (win or lose).



11.3 The Convergence (Ignored Threat Boss — Universal Exception)



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



It is subject to decay like any other zone. If it decays away, it may later reappear in a future frontier with increased strength based on additional elites absorbed while absent. While the Convergence exists in the frontier, no new elite encounters may spawn.



Special Exception Rule:



The Convergence is the only system allowed to violate frontier-size constraints.



Elites that decay are recorded.



Once a threshold number of elites decay (placeholder: 3), the Convergence becomes eligible to spawn.



When spawned, it:



Is a Boss Encounter



Suppresses elite spawning while present



Has decay like a normal zone



Absorption Rules:



All decayed elites are added to the Convergence.



Convergence gains stats and some/all abilities from absorbed elites.



If not defeated, it may decay away and later reappear stronger.



Elites cannot spawn while Convergence exists, and Convergence cannot spawn while an elite exists.



Ends the run if fought.



11.4 The Exit (Loss-of-Choice Ending)



Purpose: Represents forced withdrawal when no meaningful choices remain.



Trigger Condition:



Frontier size == 1



This is the only condition required. The Exit appears regardless of World Instability or Awareness values.



Rules:



The Exit only ever appears when it would be the sole remaining frontier option.



The player never chooses to delay or ignore the Exit.



If the Hunter triggers on the same turn, the Exit does not appear.



Outcome:



Selecting the Exit immediately ends the run.



11.5 Summary

Exit:



Appears only when it is the sole option



Never appears if Hunter triggers



May coexist with Convergence



Gatekeeper:



Replaces Exit only



Never appears independently



May coexist with Convergence



Convergence:



Additive, never replacing



May appear in any frontier state



The sole universal exception



Hunter:


Appears after enough "extra time passes"



Removes all other zones with the exception of The Convergence if it exists.

Ends the run.



12.1 Deployment Model



Each run begins as a new deployment into a collapsing region.



The Observer’s role is to observe and record, not to stabilize or save the region.



A run ends when the observation instance becomes invalid or terminal (escape, boss resolution, or death).



12.2 Data Persistence (Critical)



Observation data is transmitted continuously during a run.



Data types:



Transmitted immediately: route viability, decay timing, biome behavior, enemy sightings.



Buffered locally: fine detail, elite composition, anomaly resolution.



On run end:



Escape or boss resolution: full dataset retained.



Death: transmitted data retained; buffered data is lost.



This explains why:



Death still unlocks some progression.



Successful runs unlock more progression.



No corpse retrieval or resurrection is required.



12.3 Identity \& Continuity



The game does not explicitly define whether the Observer is the same individual across runs.



Continuity exists at the role and program level, not the body level.



The player always inhabits the role of “the Observer.”



This avoids resurrection handwaving while preserving player continuity.



12.4 Purpose of Boss Resolution



Boss encounters represent terminal observations:



Hunter: Confirms maximum viable observation time.



Gatekeeper: Confirms effects of artificial decay delay.



Convergence: Confirms consequences of ignored elite threats.



Defeating or dying to a boss ends the run because the observation hypothesis for that instance is complete. Further exploration would not yield new data.



12.5 Persistent Progression Rules



Between runs, the following may unlock:



New biomes



New event categories



New enemy archetypes



New decay behaviors



New observer contracts or focus parameters



Restrictions:



No permanent stat bonuses.



No power carryover between runs.



Unlocks expand what can be observed, not player strength.



Each run stands on its own mechanically, but contributes to long-term understanding.



13. UX \& Text Rules



Mechanics before flavor.



Consistent terminology.



Hard word limits on descriptions.



Failure messages explain what happened and why.



If text obscures mechanics, it is incorrect.



14. Implementation Notes



All systems are deterministic and seedable.



All calculations should be inspectable in logs.



No system may contradict the explicit-information contract.



15. GUI Layout Specification (Required)



The game must be implemented as a lightweight GUI using standard UI controls only (panels, lists/tables, buttons). No custom art assets are required. The GUI exists to reduce reading friction and keep all mechanical information visible and explicit.



15.1 Window Layout



Single window with four regions:



A) Left — Player \& World HUD (persistent)



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



Hotkeys shown on buttons (e.g., \[1], \[2], \[3]).



Optional setting: “Require confirm for time-costing choices” (default off).



15.2 Mode: Frontier (Choose Next Zone)



Right Context Panel: Frontier List



Display as a table or list supporting 1–7 entries.



Each entry must include:



Name



Biome



Encounter Category (Normal / Elite / Boss / Event / Rest)



Danger



Arrival Decay Stage (Fresh / Unstable / Degraded / Critical)



Time Cost (for selecting this zone; Rest entry shows 0 to enter)



Unreachable zones (Removed-on-arrival) are never shown.



Selection Details Box (below the list)



One-sentence (short) flavor description.



Any explicit previews needed for that node (if applicable).



Buttons



Go (commit to selected zone)







15.3 Mode: Combat



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



15.4 Mode: Event



Right Context Panel: Event Options



Event title + 1–2 sentence description.



Options displayed as rows/cards, each explicitly listing:



Time cost (exact)



Resource costs (exact)



Consequences/outcomes (explicit; no guessing)



On selection (and/or on confirm), show a one-line summary of what will be applied.



15.5 Mode: Rest



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



15.6 Presentation Rules



Mechanics-first: keep mechanical fields in fixed, scannable positions.



Avoid wall-of-text: narration goes to the log; mechanics stay in HUD/context.



No ambiguity: the UI must never hide costs or intent values.



This document is the canonical reference for implementation and future refinement.



16\. Authoritative Gameplay Loop (Execution Order)



This section defines the exact order of operations for a single decision cycle. Implementations must follow this order precisely.



16.1 Run Start



Initialize RNG with run seed.



Initialize player stats, HP, stamina.



Set Time = 0.



Set World Instability (W) = 0.



Generate initial frontier (Section 4) projected to arrival state at Time + zone cost.



16.2 Decision Cycle



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



Advance Time \& Decay; Update W (after resolution)



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



17 Combat Math \& Resolution Rules



17.1 Core Values



Base Attack Cost: 2 stamina



Base Attack Damage: 6



Base Guard Cost: 2 stamina



Base Guard Value: 8



Recover Action: +4 stamina, +2 HP



17.2 Skill Scaling



Each point of Skill adds +1 damage to attacks.



Skill does not reduce stamina costs.



17.3 Guard Rules



Guard is a temporary buffer.



Damage is applied to Guard first, then HP.



Guard does not persist between turns unless explicitly stated.



17.4 Damage Application



Damage = (Base Damage + Skill bonus) − target guard.



Damage cannot be negative.



17.5 Stamina



Stamina regenerates only via Recover actions or explicit effects.



No passive regeneration.



18\. Stat Definitions (Mechanical)



18.1 Health



Each Health point increases max HP by +5.



18.2 Stamina



Each Stamina point increases max stamina by +3.



18.3 Skill



Each Skill point increases attack damage by +1.



18.4 Awareness



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



19\. Decay Timing Defaults (Deprecated)



This section is deprecated.



Decay timing is governed exclusively by Section 3: Decay System, which defines variable, stage-based decay durations influenced by World Instability.



No fixed per-stage decay durations exist unless explicitly defined by a biome or special zone effect.



20\. Frontier Generation Algorithm



Compute target frontier size (Section 4).



Generate candidate locations = target + 2.



Project each candidate to arrival state.



Filter removed-on-arrival locations.



Trim to target size.



21\. Minimal Data Model (Reference)



21.1 Player



&nbsp; {

&nbsp; hp, max\_hp,

&nbsp; stamina, max\_stamina,

&nbsp; stats: { health, stamina, skill, awareness }

}



21.2 Location



{

&nbsp; id,

&nbsp; biome,

&nbsp; encounter\_type,

&nbsp; danger,

&nbsp; decay\_stage,

&nbsp; decay\_timer,

&nbsp; time\_cost

}



21.3 Enemy



{

&nbsp; archetype,

&nbsp; hp,

&nbsp; intents\[]

}



21.4 Event Option



{

&nbsp; time\_cost,

&nbsp; stamina\_cost,

&nbsp; hp\_cost,

&nbsp; outcomes\[]

}



\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_



2.1 I think time is integer based and never fractional. 3.1 This should be rolled immediately. 3.2 This must be missing, we decided on awareness partially obscuring exact remaining duration. So like with base awareness you will see the categories of decay only, and after a small threshold you will gain increasingly more observational hints regarding remaining time until it just explicitly displays it. 4.1 Clearly we need to go over this in detail, this question alone is multiple questions in itself. I'll try to clarify a little bit. 4.1.a Base size would be 4. 4.1.b Awareness contribution, I'm not sure what linear vs stepwise means so I can't answer this. 4.2.b Again I am not sure what linear or threshold-based reduction from W would mean. Also, as a note for 4.1, isn't decay rate also somehow effecting it? 4.2 This should the order of operations, A. Calculate frontier size. B. generate candidates. C. Filter zones that do not meet requirements (i.e. would be decayed upon arrival, not enough awareness, or other reasons to not show the zone.) D. Zones left are calculated to see if acceptable options == frontier size (if not steps B - D are repeated.) E. Options are displayed to the user. 4.3 Yes, unchosen locations are guaranteed to persist until they decay. New choices are only generated if there are empty slots due to the normal clearing procedure (which always necessitates at least one new zone to be generated unless frontier size shrunk), previous choice decay, or frontier size increasing. 4.4 Biomes can change the frontier size of choices selected when inside the biome. For example, if you choose to go to the abandoned camp, and it is in the desert biome, your frontier IN the desert biome would be -1. 5.5.1 W is capped at 10 I guess? I'm not really sure, we haven't discussed what W is much or how it affects the world exactly. It influences a lot but right now this is very fluid and conceptual. Nothing, not even the document, is solidified and definite right now. 5.5.2 W is one of the ways frontier size is affected. I do not have the exact calculation yet. 5.5.2 these threshold behaviors are placeholders for one thing, but yes they would be cumulative. 6.1 Rest zones are not biome specific, however, the rest options they give can be influenced by the biome they are in. More dangerous biomes like swamps and deserts will have less rest options or they will be less valuable where as safer rest spots like forest clearings and city rest spots will have more rest options or more valuable rests. 6.2 Decay mitigation is a flat value, when it shows up. It is rare and only shows up at rest spots in safer biomes, or possibly even special biomes only, I'm not sure yet. 6.3 There will be a set amount of decay mitigation for each type of rest event that allows it. 6.4 Rest zones, like all zones, will be removed from the frontier through the normal procedure loop when they are "Solved" or "Mapped" and a zone is "Solved" or "Mapped" when the player has gone there and resolved the event (either fight, event, rest, or nothing). This will remove that location from the frontier regardless of it's current decay. 7.1 The player actions are actions that the player will be able to use in battle. They should include: Attack (attempt to deal damage to the selected target. Mechanically deals damage to the selected enemy calculating block as necessary.), Defend (attempt to reduce damage taken this turn. Mechanically adds block to the player.), Recover (try to catch your breath. Mechanically recovers some stamina.), Use item (attempt to use some sort of consumable. Mechanically consume a selected consumable for an effect.) These are as fluid as anything else and are subject to change. 7.2 Stamina does not have a precise ruleset yet. Right now it's conceptual, using items, taking actions in combat, and attacking / defending takes stamina. 7.3 Damage should be the same each time. Basic attack is 6 damage (Placeholder numbers) not a range. 7.4 No 8.1 There may be some RNG, but I think for the most part, if not entirely, outcomes should be deterministic and trackable. This makes the game be about strategy more than randomness. 9.1.a Health does not have a current starting value. It should likely never increase, but be recoverable. There may be some ways to temporarily increase max hp, but they would not persist outside of the run loop. The starting HP would always be the same. 9.1.b Stamina amounts would have a cap based on the stat, regen would be through time, resting, and the recover option in battle. 9.1.c Right now skill effects one thing, the amount of damage you deal with attacks. But I am not sure I like this. One thing for sure, if it does turn out all it does is increase attack damage then it needs to have a different name than "skill". 9.1.d Awareness increases frontier zones shown, and past certain thresholds can unlock hidden zones or event options. These have not been clarified what they are exactly yet. 9.2 stats will increase through leveling, items, and some special events may give buffs to the stats as well. However, stats and level reset at the start of every run. They are supposed to be more of a measure of getting used to that area, not overall meta progression. 10.1 This has not been decided. 10.2 This would be category-based I think, but may be removed entirely from the final product. Needs further review. 10.3 Meta-progression is open-ended and based on how well each run did and how many pieces of "data" you were able to return. 12.1 "Normal time" is the zone's "time cost" 12.2 this is undecided. 12.3 Hunter progress is communicated through narrative warnings in the frontier mode. 13.1 This will be threshold based as well. Once you pass the threshold you will encounter the gatekeeper. The only way around this is if you fight a different boss to exit. 14.1 Absorbing Elites means this, as elites decay they will be stored in a database, once a certain number of elites, we'll say 3 for now, have decayed, The Convergence starts being able to spawn. The Convergence will have a portion of the stats added and some or all of the abilities of the elites that decayed to create it. Also, any decayed elites get added to The Convergence, no matter which time it has shown up. 14.2 Yes, The Convergence will be able to spawn once it's threshold is passed. Once it spawns it will be a "boss encounter" but it will have decay like any other normal zone. It will stick around until it decays. If you do not kill the Convergence it can spawn again, probably after a delay but this has not been decided, and will absorb any elites that decay in that time. The only time the Convergence cannot spawn is when there is an actively spawned Elite. And Elites cannot spawn when the Convergence is spawned. 16. The frontier section of the gui should allow users to select each possible zone and see the information about it only traveling there if they click the "go" or "travel" button.

