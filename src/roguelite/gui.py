"""Tkinter-powered GUI for the text-based roguelite.

This module wraps the existing :class:`Game` loop with a lightweight
Tkinter interface that renders the journal feed, available choices, player
status, and inventory. Interactive choices are made through buttons instead
of raw ``input`` prompts, while the existing auto-mode remains available for
testing.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Sequence

from .entities import Combatant, describe_combatants
from .game import Game, GameSettings
from .items import Consumable, Item, best_item
from .world import FrontierOption, FrontierState


Choice = tuple[str, str]


class GameUI:
    """Owns the Tk widgets and brokers choices between the user and game."""

    def __init__(self, settings: GameSettings):
        self.root = tk.Tk()
        self.root.title("Text Roguelite")
        self.settings = settings
        self._choice_event = threading.Event()
        self._choice_value: str | None = None

        self._build_layout()

    def _build_layout(self) -> None:
        self.root.geometry("900x620")
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Label(self.root, text="Text Roguelite Expedition", font=("TkDefaultFont", 14, "bold"))
        header.grid(row=0, column=0, columnspan=2, pady=(8, 4))

        sidebar = ttk.Frame(self.root)
        sidebar.grid(row=1, column=0, sticky="nsew", padx=(8, 6), pady=6)

        status_frame = ttk.LabelFrame(sidebar, text="Status")
        status_frame.pack(fill="x", pady=(0, 6))
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, justify=tk.LEFT)
        self.status_label.pack(fill="x", padx=6, pady=4)

        inv_frame = ttk.LabelFrame(sidebar, text="Inventory")
        inv_frame.pack(fill="both", expand=True)
        self.inventory_box = tk.Listbox(inv_frame, height=12)
        self.inventory_box.pack(fill="both", expand=True, padx=6, pady=4)

        self.consumable_box = tk.Listbox(inv_frame, height=6)
        self.consumable_box.pack(fill="x", padx=6, pady=(0, 6))

        main = ttk.Frame(self.root)
        main.grid(row=1, column=1, sticky="nsew", padx=(0, 8), pady=6)
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)

        prompt_frame = ttk.Frame(main)
        prompt_frame.grid(row=0, column=0, sticky="ew")
        self.prompt_var = tk.StringVar()
        self.prompt_label = ttk.Label(prompt_frame, textvariable=self.prompt_var, font=("TkDefaultFont", 11, "bold"))
        self.prompt_label.pack(side=tk.LEFT, padx=(4, 0), pady=(0, 4))

        self.choice_frame = ttk.Frame(main)
        self.choice_frame.grid(row=0, column=1, sticky="e")

        log_frame = ttk.LabelFrame(main, text="Journal")
        log_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, wrap="word", state="disabled", height=24)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=scrollbar.set)

        frontier_frame = ttk.LabelFrame(main, text="Frontier")
        frontier_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        frontier_frame.columnconfigure(0, weight=1)
        self.frontier_var = tk.StringVar()
        self.frontier_label = ttk.Label(frontier_frame, textvariable=self.frontier_var, justify=tk.LEFT)
        self.frontier_label.grid(row=0, column=0, sticky="w", padx=6, pady=4)

    def run(self, start: Callable[[], None]) -> None:
        self.root.after(50, start)
        self.root.mainloop()

    def append_log(self, entry: str) -> None:
        def _append() -> None:
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, entry + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")

        self.root.after(0, _append)

    def refresh_status(self, player: Combatant) -> None:
        def _update() -> None:
            lines: List[str] = [describe_combatants([player])]
            if player.statuses:
                status_notes = [f"{name} ({turns} steps)" for name, turns in player.statuses.items()]
                lines.append("Statuses: " + ", ".join(status_notes))
            self.status_var.set("\n".join(lines))

            def format_item(prefix: str, item: Item | None) -> str:
                return f"{prefix}: {item.summary()}" if item else f"{prefix}: (empty)"

            gear = [
                format_item("Weapon", player.weapon),
                format_item("Armor", player.armor),
                format_item("Charm", player.charm),
            ]
            self.inventory_box.delete(0, tk.END)
            for line in gear:
                self.inventory_box.insert(tk.END, line)

            self.consumable_box.delete(0, tk.END)
            if player.consumables:
                for consumable in player.consumables:
                    self.consumable_box.insert(tk.END, f"{consumable.summary()} x{consumable.charges}")
            else:
                self.consumable_box.insert(tk.END, "No consumables")

        self.root.after(0, _update)

    def show_frontier(self, frontier: FrontierState) -> None:
        def _update() -> None:
            details = [
                "Frontier size target: "
                f"{frontier.size.clamped()} (base {frontier.size.base} + {frontier.size.positive_total()} pos - {frontier.size.negative_total()} neg)."
            ]
            if frontier.size.positive:
                pos = ", ".join(f"+{mod.value} {mod.label}" for mod in frontier.size.positive)
                details.append(f" Positive modifiers: {pos}.")
            if frontier.size.negative:
                neg = ", ".join(f"-{mod.value} {mod.label}" for mod in frontier.size.negative)
                details.append(f" Negative modifiers: {neg}.")
            self.frontier_var.set("\n".join(details))

        self.root.after(0, _update)

    def prompt_choice(self, prompt: str, options: Sequence[Choice]) -> str:
        self._choice_event.clear()
        self._choice_value = None

        def _build() -> None:
            for child in list(self.choice_frame.winfo_children()):
                child.destroy()
            self.prompt_var.set(prompt)
            for label, value in options:
                btn = ttk.Button(self.choice_frame, text=label, command=lambda v=value: self._submit_choice(v))
                btn.pack(side=tk.LEFT, padx=4)

        self.root.after(0, _build)
        self._choice_event.wait()
        assert self._choice_value is not None
        return self._choice_value

    def _submit_choice(self, value: str) -> None:
        self._choice_value = value
        self._choice_event.set()


class GuiGame(Game):
    """A ``Game`` variant that routes interaction through :class:`GameUI`."""

    def __init__(self, settings: GameSettings, ui: GameUI):
        super().__init__(settings)
        self.ui = ui

    def log(self, entry: str) -> None:
        # Preserve console output for transparency while sending to the GUI.
        super().log(entry)
        self.ui.append_log(entry)

    def offer_talent_choice(self) -> None:
        options = {
            "health": ("Bolster vitality (+3 health)", lambda: self.apply_stat_gain("health", 3)),
            "stamina": ("Deepen stamina reserves (+2 stamina)", lambda: self.apply_stat_gain("stamina", 2)),
            "skill": ("Sharpen skill (+1 skill)", lambda: self.apply_stat_gain("skill", 1)),
            "awareness": ("Widen awareness (+1 awareness)", lambda: self.apply_stat_gain("awareness", 1)),
        }
        keys = list(options.keys())
        choices = [(f"{idx}. {options[key][0]}", key) for idx, key in enumerate(keys, start=1)]
        pick = self.ui.prompt_choice("Choose how to grow from your experience", choices)
        _, action = options[pick]
        action()
        self.log(f"You feel stronger: {options[pick][0]}.")

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
        options = [("Equip", "yes"), ("Keep current", "no")]
        choice = self.ui.prompt_choice(
            f"Equip {item.summary()} to replace {current.summary()} in your {slot} slot?", options
        )
        if choice == "yes":
            setattr(self.player, slot, item)
            self.log(f"You equip {item.summary()}.")
        else:
            self.log(f"You keep {current.summary()} equipped.")

    def choose_player_action(self, foe: Combatant) -> str:
        self.ui.refresh_status(self.player)
        prompt = f"{foe.name} signals intent. Choose your action"
        options: Sequence[Choice] = [
            ("Attack", "attack"),
            ("Guard", "guard"),
            ("Recover", "recover"),
            ("Use Consumable", "use"),
        ]
        return self.ui.prompt_choice(prompt, options)

    def prompt_select_consumable(self, consumables: List[Consumable], in_combat: bool) -> Consumable | None:
        choices: List[Choice] = []
        for idx, consumable in enumerate(consumables, start=1):
            target_note = "(requires target)" if consumable.requires_target else "(self)"
            label = f"{idx}. {consumable.summary()} {target_note}"
            choices.append((label, str(idx)))
        choices.append(("Cancel", "0"))
        selection = self.ui.prompt_choice("Choose a consumable to use", choices)
        if selection == "0":
            return None
        return consumables[int(selection) - 1]

    def maybe_use_consumable_outside_combat(self, reason: str) -> None:
        consumables = self.available_consumables(in_combat=False)
        if not consumables:
            return
        choice = self.ui.prompt_choice(f"Use a consumable before {reason}?", [("Yes", "yes"), ("No", "no")])
        if choice == "yes":
            self.use_consumable(in_combat=False)

    def choose_event_option(self, scenario) -> object:  # type: ignore[override]
        choices: List[Choice] = []
        for idx, option in enumerate(scenario.options, start=1):
            choices.append((f"{idx}. {option.title} [{option.risk}]", str(idx)))
        selection = self.ui.prompt_choice("Choose how to respond", choices)
        return scenario.options[int(selection) - 1]

    def choose_frontier_option(self, frontier: FrontierState) -> FrontierOption:
        self.ui.show_frontier(frontier)
        self.ui.refresh_status(self.player)
        choices: List[Choice] = []
        for idx, option in enumerate(frontier.options, start=1):
            exit = option.exit
            if option.placeholder:
                label = f"{idx}. {exit.label} :: {option.reason}"
            else:
                destination = option.location
                note = f" [{exit.note}]" if exit.note else ""
                label = (
                    f"{idx}. {exit.label} toward {destination.name} "
                    f"(cost {exit.cost} stamina, danger {destination.danger}, {destination.biome.title}){note}"
                )
            choices.append((label, str(idx)))
        prompt = "Paths branch ahead. Choose your route"
        selection = self.ui.prompt_choice(prompt, choices)
        return frontier.options[int(selection) - 1]

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
        self.ui.refresh_status(self.player)


def launch_gui(settings: GameSettings) -> None:
    """Start the Tkinter UI and play a run."""

    ui = GameUI(settings)
    game = GuiGame(settings, ui)

    def start_game() -> None:
        ui.refresh_status(game.player)
        worker = threading.Thread(target=game.play, daemon=True)
        worker.start()

    ui.run(start_game)

