"""Game loop and mechanics for the text-based roguelite."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List

from .entities import Combatant, Stats, describe_combatants
from .items import Item, best_item, roll_item_drop
from .events import resolve_event
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

    def log(self, entry: str) -> None:
        self.journal.append(entry)
        print(entry)

    def add_item_to_inventory(self, item: Item) -> None:
        self.player.inventory.append(item)
        self.log(f"You obtain {item.summary()}. {item.description}")
        if self.settings.auto:
            self.auto_equip_best_item()
        else:
            self.prompt_equip(item)

    def auto_equip_best_item(self) -> None:
        candidate = best_item(self.player.inventory)
        if candidate is None:
            return
        if candidate is self.player.equipped:
            return
        previous = self.player.equipped.summary() if self.player.equipped else "nothing"
        self.player.equipped = candidate
        self.log(f"Auto-equip: swapping {previous} for {candidate.summary()}.")

    def prompt_equip(self, item: Item) -> None:
        if self.player.equipped is None:
            self.player.equipped = item
            self.log(f"You equip {item.summary()}.")
            return
        if item.score() <= self.player.equipped.score():
            self.log(f"You stow the {item.name} for later, keeping {self.player.equipped.summary()} equipped.")
            return

        prompt = (
            f"Equip {item.summary()} instead of {self.player.equipped.summary()}? "
            "([y]es/[n]o): "
        )
        while True:
            choice = input(prompt).strip().lower()
            if choice in {"y", "yes"}:
                self.player.equipped = item
                self.log(f"You equip {item.summary()}.")
                break
            if choice in {"n", "no"}:
                self.log(f"You keep {self.player.equipped.summary()} equipped.")
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
        foe_stats = Stats(
            health=6 + location.danger,
            stamina=5 + location.danger,
            skill=3 + location.danger // 2,
            awareness=3 + location.danger // 2,
        )
        foe = Combatant(name="Adversary", stats=foe_stats)
        self.log(f"An enemy emerges, matching the threat level {location.danger}.")
        while foe.stats.is_alive() and self.player.stats.is_alive():
            self.log("-- Combat Round --")
            self.log(describe_combatants([self.player, foe]))
            player_action = self.choose_player_action()
            self.resolve_player_action(player_action, foe)
            if not foe.stats.is_alive():
                break
            self.resolve_enemy_turn(foe)
        if foe.stats.is_alive():
            return False
        loot = max(1, round((location.danger // 2 or 1) * location.reward_multiplier))
        self.player.stats.stamina = min(self.player.stats.stamina + loot, self.player.stats.awareness + 6)
        self.log(f"Enemy defeated. You salvage {loot} stamina worth of supplies.")
        dropped_item = roll_item_drop(self.rng, location.danger)
        if dropped_item:
            self.add_item_to_inventory(dropped_item)
        return True

    def choose_player_action(self) -> str:
        if self.settings.auto:
            if self.player.stats.health <= 4:
                return "recover"
            if self.player.stats.guard < 2 and self.player.stats.stamina < 3:
                return "recover"
            return "attack"
        prompt = "Choose action ([a]ttack, [g]uard, [r]ecover): "
        while True:
            choice = input(prompt).strip().lower()
            mapping = {"a": "attack", "g": "guard", "r": "recover"}
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
        else:
            self.log(self.player.recover())

    def resolve_enemy_turn(self, foe: Combatant) -> None:
        if foe.stats.stamina <= 0:
            foe.stats.stamina += 1
            self.log(f"{foe.name} hesitates, regaining stamina.")
            return
        if self.player.stats.guard > 2 and foe.stats.stamina > 1:
            foe.stats.stamina -= 1
            self.log(foe.guard())
            return
        foe.stats.stamina -= 1
        self.log(foe.attack(self.player, self.rng))

    def handle_rest(self, location: Location) -> None:
        heal = max(1, round((2 + location.danger // 2) * location.reward_multiplier))
        stamina = max(2, round(3 * location.reward_multiplier))
        self.player.stats.health = min(self.player.stats.health + heal, self.player.stats.awareness + 10)
        self.player.stats.stamina = min(self.player.stats.stamina + stamina, self.player.stats.awareness + 6)
        self.log(f"Safe pocket: you rest, healing {heal} and restoring {stamina} stamina.")
        self.log("Status :: " + describe_combatants([self.player]))

    def handle_event(self, location: Location) -> None:
        narration, outcome, item = resolve_event(self.player, location.danger, self.rng)
        self.log(f"Event: {narration}")
        self.log(outcome)
        if item:
            self.add_item_to_inventory(item)
        self.log("Status :: " + describe_combatants([self.player]))

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
