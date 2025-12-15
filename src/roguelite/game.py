"""Game loop and mechanics for the text-based roguelite."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List

from .entities import Combatant, Stats, describe_combatants
from .items import Item, best_item, roll_item_drop
from .events import resolve_event
from .world import Location, generate_world


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
        self.world: List[Location] = generate_world(settings.seed, settings.steps)
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
        for idx, location in enumerate(self.world, start=1):
            self.describe_location(location, idx)
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
        self.log("You have endured every encounter in this route. Victory!")
        return True

    def describe_location(self, location: Location, idx: int) -> None:
        self.log(f"\n[{idx}/{len(self.world)}] {location.name} :: {location.description}")
        self.log(f"Encounter: {location.encounter.upper()}, danger {location.danger}.")
        self.log("Status :: " + describe_combatants([self.player]))

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
        loot = max(1, location.danger // 2)
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
        heal = 2 + location.danger // 2
        stamina = 3
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
