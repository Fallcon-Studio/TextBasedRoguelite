"""Game loop and mechanics for the text-based roguelite."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List

from .entities import Combatant, Stats, describe_combatants
from .enemies import EnemyTemplate, pick_enemy_template
from .items import Consumable, Item, best_item, roll_consumable_drop, roll_item_drop
from .events import EventOption, EventScenario, resolve_event
from .world import Exit, Location, WorldGraph, generate_world


@dataclass
class GameSettings:
    seed: int | None
    steps: int = 6
    auto: bool = False


class Game:
    """Coordinates the run through the generated world."""

    def __init__(self, settings: GameSettings):
        self.settings = settings
        self.rng = random.Random(settings.seed)
        self.player = Combatant(
            name="Drifter",
            stats=Stats(health=12, stamina=8, skill=4, awareness=4),
        )
        self.world: WorldGraph = generate_world(settings.seed, settings.steps)
        self.current_location_id = self.world.start
        self.route_taken: List[str] = []
        self.journal: List[str] = []
        self.experience: int = 0
        self.level: int = 1
        self.xp_to_next: int = 5

    def describe_status_effects(self, context: str) -> None:
        if not self.player.statuses:
            return
        notes: List[str] = []
        if self.player.has_status("scouted"):
            notes.append("scouted (+guard/+awareness)")
        if self.player.has_status("inspired"):
            notes.append("inspired (+skill/+awareness)")
        if self.player.has_status("cursed"):
            notes.append("cursed (-skill/-guard)")
        self.log(f"Statuses for this {context}: {', '.join(notes)}")

    def grant_status(self, name: str, duration: int, source: str) -> None:
        previous = self.player.statuses.get(name)
        self.player.add_status(name, duration)
        label = f"{name} for {self.player.statuses[name]} encounters ({source})."
        if previous:
            self.log(f"Status refreshed: {label}")
        else:
            self.log(f"Status gained: {label}")

    def decay_statuses(self, context: str) -> None:
        expired = self.player.tick_statuses()
        if expired:
            faded = ", ".join(expired)
            self.log(f"Statuses fade after the {context}: {faded}.")

    def log(self, entry: str) -> None:
        self.journal.append(entry)
        print(entry)

    def award_experience(self, amount: int, reason: str) -> None:
        self.experience += amount
        self.log(f"You gain {amount} insight from {reason} (total {self.experience}).")
        self.maybe_level_up()

    def maybe_level_up(self) -> None:
        while self.experience >= self.xp_to_next:
            self.experience -= self.xp_to_next
            self.level += 1
            self.log(f"Insight crystallizes. You reach level {self.level}!")
            self.offer_talent_choice()
            self.xp_to_next = 5 + (self.level - 1) * 3

    def offer_talent_choice(self) -> None:
        options = {
            "health": ("Bolster vitality (+3 health)", lambda: self.apply_stat_gain("health", 3)),
            "stamina": (
                "Deepen stamina reserves (+2 stamina)",
                lambda: self.apply_stat_gain("stamina", 2),
            ),
            "skill": ("Sharpen skill (+1 skill)", lambda: self.apply_stat_gain("skill", 1)),
            "awareness": (
                "Widen awareness (+1 awareness)",
                lambda: self.apply_stat_gain("awareness", 1),
            ),
        }

        if self.settings.auto:
            pick = min(options.keys(), key=lambda k: getattr(self.player.stats, k))
            desc, action = options[pick]
            action()
            self.log(f"Auto-pick talent: {desc}.")
            return

        self.log("Choose how to grow from your experience:")
        keys = list(options.keys())
        for idx, key in enumerate(keys, start=1):
            self.log(f" {idx}. {options[key][0]}")
        prompt = "Select growth option: "
        while True:
            try:
                choice = int(input(prompt))
            except ValueError:
                print("Enter a listed number.")
                continue
            if 1 <= choice <= len(keys):
                _, action = options[keys[choice - 1]]
                action()
                self.log(f"You feel stronger: {options[keys[choice - 1]][0]}.")
                return
            print("Invalid selection.")

    def apply_stat_gain(self, key: str, amount: int) -> None:
        current = getattr(self.player.stats, key)
        setattr(self.player.stats, key, current + amount)
        if key in {"health", "stamina"}:
            cap = self.player.stats.awareness + (10 if key == "health" else 6)
            setattr(self.player.stats, key, min(getattr(self.player.stats, key), cap))

    def add_item_to_inventory(self, item: Item | Consumable) -> None:
        if isinstance(item, Consumable):
            self.player.consumables.append(item)
            self.log(f"You obtain {item.summary()}. {item.description}")
            return

        self.player.inventory.append(item)
        self.log(f"You obtain {item.summary()}. {item.description}")
        if self.settings.auto:
            self.auto_equip_best_item(item.slot)
        else:
            self.prompt_equip(item)

    def auto_equip_best_item(self, slot: str) -> None:
        candidate = best_item(self.player.inventory, slot=slot)
        if candidate is None:
            return

        current = getattr(self.player, slot)
        if candidate is current:
            return
        previous = current.summary() if current else "nothing"
        setattr(self.player, slot, candidate)
        self.log(f"Auto-equip: swapping {previous} for {candidate.summary()}.")

    def prompt_equip(self, item: Item) -> None:
        slot = item.slot
        current: Item | None = getattr(self.player, slot)
        if current is None:
            setattr(self.player, slot, item)
            self.log(f"You equip {item.summary()}.")
            return
        if item.score() <= current.score():
            self.log(f"You stow the {item.name} for later, keeping {current.summary()} equipped.")
            return

        prompt = (
            f"Equip {item.summary()} to replace {current.summary()} in your {slot} slot? "
            "([y]es/[n]o): "
        )
        while True:
            choice = input(prompt).strip().lower()
            if choice in {"y", "yes"}:
                setattr(self.player, slot, item)
                self.log(f"You equip {item.summary()}.")
                break
            if choice in {"n", "no"}:
                self.log(f"You keep {current.summary()} equipped.")
                break
            print("Please answer y or n.")

    def play(self) -> bool:
        self.log("\n=== Text Roguelite Expedition ===")
        while True:
            location = self.world.nodes[self.current_location_id]
            self.route_taken.append(location.name)
            self.describe_location(location)
            if location.encounter == "enemy":
                survived = self.handle_combat(location)
                if not survived:
                    self.log("You collapse. The expedition ends here.")
                    return False
            elif location.encounter == "rest":
                self.handle_rest(location)
            else:
                self.handle_event(location)

            if not self.player.stats.is_alive():
                self.log("Your injuries are too severe to continue.")
                return False
            if not location.exits:
                self.log("You have reached the end of this route. Victory!")
                return True

            chosen_exit = self.choose_next_step(location)
            self.apply_travel_cost(chosen_exit)
            if not self.player.stats.is_alive():
                self.log("You collapse. The expedition ends here.")
                return False
            self.current_location_id = chosen_exit.destination

    def describe_location(self, location: Location) -> None:
        self.log(
            f"\n[{len(self.route_taken)}] {location.name} ({location.biome.title}) :: "
            f"{location.description}"
        )
        self.log(
            f"Encounter: {location.encounter.upper()}, danger {location.danger}, "
            f"rewards x{location.reward_multiplier:.2f}."
        )
        self.log("Status :: " + describe_combatants([self.player]))
        breadcrumb = " -> ".join(self.route_taken)
        self.log(f"Route so far: {breadcrumb}")

    def handle_combat(self, location: Location) -> bool:
        template = pick_enemy_template(location.biome.key, location.danger, self.rng)
        foe = template.spawn(location.danger, self.rng)
        self.log(
            f"A {template.title.lower()} emerges: {template.description}. "
            f"Threat level {location.danger}."
        )
        self.describe_status_effects("combat")
        while foe.stats.is_alive() and self.player.stats.is_alive():
            self.log("-- Combat Round --")
            self.log(describe_combatants([self.player, foe]))
            enemy_action, intent = template.behavior.decide(foe, self.player, self.rng)
            self.log(f"{foe.name} signals intent: {intent} [{enemy_action.upper()}].")
            player_action = self.choose_player_action(foe)
            self.resolve_player_action(player_action, foe)
            if not foe.stats.is_alive():
                break
            self.resolve_enemy_action(enemy_action, foe, template)
        if foe.stats.is_alive():
            return False
        loot = max(
            1,
            round((location.danger // 2 or 1) * location.reward_multiplier * template.loot_multiplier),
        )
        xp_gain = max(1, round(location.danger * template.xp_value * location.reward_multiplier))
        self.player.stats.stamina = min(
            self.player.stats.stamina + loot, self.player.stats.awareness + 6
        )
        self.log(
            f"Enemy defeated. You salvage {loot} stamina worth of supplies and gain "
            f"{xp_gain} insight."
        )
        self.award_experience(xp_gain, "victory")
        dropped_item = roll_item_drop(self.rng, location.danger)
        if dropped_item:
            self.add_item_to_inventory(dropped_item)
        dropped_consumable = roll_consumable_drop(self.rng, location.danger)
        if dropped_consumable:
            self.add_item_to_inventory(dropped_consumable)
        self.decay_statuses("combat")
        return True

    def choose_player_action(self, foe: Combatant) -> str:
        if self.settings.auto:
            if self.should_use_consumable_auto(foe):
                return "use"
            if self.player.stats.health <= 4:
                return "recover"
            if self.player.stats.guard < 2 and self.player.stats.stamina < 3:
                return "recover"
            return "attack"
        prompt = "Choose action ([a]ttack, [g]uard, [r]ecover, [u]se consumable): "
        while True:
            choice = input(prompt).strip().lower()
            mapping = {"a": "attack", "g": "guard", "r": "recover", "u": "use"}
            if choice in mapping:
                return mapping[choice]
            if choice in mapping.values():
                return choice
            print("Invalid choice. Try again.")

    def resolve_player_action(self, action: str, foe: Combatant) -> None:
        if action == "attack" and self.player.stats.stamina > 0:
            self.player.stats.stamina -= 1
            self.log(self.player.attack(foe, self.rng))
        elif action == "guard":
            self.log(self.player.guard())
        elif action == "use":
            if not self.use_consumable(in_combat=True, foe=foe):
                self.log("No consumable used; you steady yourself instead.")
        else:
            self.log(self.player.recover())

    def available_consumables(self, in_combat: bool) -> List[Consumable]:
        return [
            c
            for c in self.player.consumables
            if c.charges > 0 and (in_combat or not c.requires_target)
        ]

    def should_use_consumable_auto(self, foe: Combatant) -> bool:
        consumables = self.available_consumables(in_combat=True)
        if not consumables:
            return False
        if self.player.stats.health <= 4:
            return any(c.name == "Healing Draught" for c in consumables)
        if self.player.stats.stamina <= 2:
            return any(c.name == "Stamina Tonic" for c in consumables)
        if foe.stats.guard >= 2:
            return any(c.name == "Shock Grenade" for c in consumables)
        return False

    def use_consumable(self, in_combat: bool, foe: Combatant | None = None) -> bool:
        consumables = self.available_consumables(in_combat)
        if not consumables:
            return False

        chosen: Consumable | None = None
        if self.settings.auto:
            chosen = self.auto_select_consumable(consumables, foe)
        else:
            chosen = self.prompt_select_consumable(consumables, in_combat)

        if chosen is None:
            return False

        target = foe if chosen.requires_target else None
        message = chosen.use(self.player, target, self.rng)
        self.log(message)
        return True

    def auto_select_consumable(
        self, consumables: List[Consumable], foe: Combatant | None
    ) -> Consumable | None:
        priority = [
            "Healing Draught" if self.player.stats.health <= 5 else None,
            "Stamina Tonic" if self.player.stats.stamina <= 2 else None,
            "Shock Grenade" if foe and foe.stats.guard >= 1 else None,
            "Focus Charm" if self.player.stats.skill < 6 else None,
        ]
        for desired in priority:
            if desired is None:
                continue
            for c in consumables:
                if c.name == desired:
                    return c
        return consumables[0] if consumables else None

    def prompt_select_consumable(
        self, consumables: List[Consumable], in_combat: bool
    ) -> Consumable | None:
        self.log("Choose a consumable to use:")
        for idx, consumable in enumerate(consumables, start=1):
            target_note = "(requires target)" if consumable.requires_target else "(self)"
            self.log(f" {idx}. {consumable.summary()} {target_note} :: {consumable.description}")
        self.log(" 0. Cancel")
        prompt = "Select consumable number: "
        while True:
            try:
                choice = int(input(prompt))
            except ValueError:
                print("Enter a number.")
                continue
            if choice == 0:
                return None
            if 1 <= choice <= len(consumables):
                selected = consumables[choice - 1]
                if in_combat and selected.requires_target is False:
                    return selected
                if in_combat and selected.requires_target is True:
                    return selected
                if not in_combat and selected.requires_target:
                    print("That requires a target and cannot be used now.")
                    continue
                return selected
            print("Invalid choice.")

    def maybe_use_consumable_outside_combat(self, reason: str) -> None:
        consumables = self.available_consumables(in_combat=False)
        if not consumables:
            return
        if self.settings.auto:
            if self.player.stats.health <= 6 or self.player.stats.stamina <= 2:
                self.use_consumable(in_combat=False)
            return
        prompt = f"Use a consumable before {reason}? ([y]/[n]): "
        while True:
            choice = input(prompt).strip().lower()
            if choice in {"y", "yes"}:
                self.use_consumable(in_combat=False)
                return
            if choice in {"n", "no", ""}:
                return
            print("Please answer y or n.")

    def auto_pick_event_option(self, options: List[EventOption]) -> EventOption:
        def score(option: EventOption) -> int:
            base = {"safe": 3, "balanced": 2, "trade": 2, "risky": 1}.get(
                option.risk, 2
            )
            if self.player.stats.health <= 4 and option.risk == "risky":
                base -= 1
            if self.player.stats.stamina <= 2 and option.risk == "trade":
                base -= 1
            if self.player.has_status("inspired") and option.risk == "risky":
                base += 1
            return base

        return max(options, key=score)

    def choose_event_option(self, scenario: EventScenario) -> EventOption:
        self.log("Choose how to respond:")
        for idx, option in enumerate(scenario.options, start=1):
            self.log(f" {idx}. {option.title} [{option.risk}] :: {option.detail}")

        if self.settings.auto:
            selected = self.auto_pick_event_option(scenario.options)
            self.log(f"Auto-pick event response: {selected.title} ({selected.risk}).")
            return selected

        prompt = "Select option number: "
        while True:
            try:
                choice = int(input(prompt))
            except ValueError:
                print("Enter a listed number.")
                continue
            if 1 <= choice <= len(scenario.options):
                return scenario.options[choice - 1]
            print("Invalid selection.")

    def resolve_enemy_action(self, action: str, foe: Combatant, template: EnemyTemplate) -> None:
        if action == "guard":
            self.log(foe.guard())
            return
        if action == "recover":
            self.log(foe.recover())
            return

        if foe.stats.stamina <= 0:
            foe.stats.stamina += 1
            self.log(f"{foe.name} falters, forced to regain stamina instead.")
            return

        foe.stats.stamina -= 1
        self.log(foe.attack(self.player, self.rng))
        effect = template.on_hit_effect(foe, self.player, self.rng)
        if effect:
            self.log(effect)

    def handle_rest(self, location: Location) -> None:
        self.maybe_use_consumable_outside_combat("resting")
        heal = max(1, round((2 + location.danger // 2) * location.reward_multiplier))
        stamina = max(2, round(3 * location.reward_multiplier))
        self.player.stats.health = min(self.player.stats.health + heal, self.player.stats.awareness + 10)
        self.player.stats.stamina = min(self.player.stats.stamina + stamina, self.player.stats.awareness + 6)
        self.log(f"Safe pocket: you rest, healing {heal} and restoring {stamina} stamina.")
        self.log("Status :: " + describe_combatants([self.player]))
        self.award_experience(1, "resting and reflecting")
        self.decay_statuses("rest")

    def handle_event(self, location: Location) -> None:
        self.maybe_use_consumable_outside_combat("facing the event")
        scenario = resolve_event(self, location, self.rng)
        self.log(f"Event: {scenario.title} [{location.biome.title}]")
        self.log(scenario.intro)
        self.describe_status_effects("event")
        choice = self.choose_event_option(scenario)
        self.log(f"You choose: {choice.title}. {choice.detail}")
        outcome = choice.resolver(self.player, self, location, self.rng)
        self.log(outcome.narration)
        self.log(outcome.outcome)
        for name, duration, source in outcome.status_effects:
            self.grant_status(name, duration, source)
        if outcome.item:
            self.add_item_to_inventory(outcome.item)
        if outcome.consumable:
            self.add_item_to_inventory(outcome.consumable)
        bonus_consumable = roll_consumable_drop(self.rng, location.danger)
        if bonus_consumable:
            self.add_item_to_inventory(bonus_consumable)
        self.award_experience(1, "learning from the encounter")
        self.log("Status :: " + describe_combatants([self.player]))
        self.decay_statuses("event")

    def choose_next_step(self, location: Location) -> Exit:
        self.log("Paths branch ahead:")
        for idx, exit in enumerate(location.exits, start=1):
            destination = self.world.nodes[exit.destination]
            note = f" [{exit.note}]" if exit.note else ""
            self.log(
                f" {idx}. {exit.label} toward {destination.name} (cost {exit.cost} stamina, "
                f"danger {destination.danger}, {destination.biome.title}){note}"
            )

        if self.settings.auto:
            return min(
                location.exits,
                key=lambda ex: (self.world.nodes[ex.destination].danger + ex.cost),
            )

        prompt = "Choose your path by number: "
        while True:
            try:
                choice = int(input(prompt))
            except ValueError:
                print("Enter a number matching the listed paths.")
                continue
            if 1 <= choice <= len(location.exits):
                return location.exits[choice - 1]
            print("Invalid path. Try again.")

    def apply_travel_cost(self, chosen_exit: Exit) -> None:
        self.player.stats.guard = 0
        self.player.stats.stamina -= chosen_exit.cost
        if self.player.stats.stamina < 0:
            deficit = abs(self.player.stats.stamina)
            self.player.stats.stamina = 0
            self.player.stats.health -= deficit
            self.log(
                f"Travel grinds you down: you spend {chosen_exit.cost} stamina and lose "
                f"{deficit} health pushing onward."
            )
        else:
            self.log(f"You spend {chosen_exit.cost} stamina reaching the next waypoint.")
