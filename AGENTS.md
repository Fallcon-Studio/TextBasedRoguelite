AGENTS.md



This file defines mandatory operating rules for any automated agent (including Codex) working in this repository.



These rules are not suggestions. They must be followed exactly.



Authoritative Rules Document



The following file is the single source of truth for all gameplay mechanics, systems, terminology, scope, and constraints:



Game\_Rules\_Document.txt



All implementation decisions must be derived from that document.



If a behavior, system, value, or interaction is not explicitly defined in Game\_Rules\_Document.txt, it must not be invented.



If there is ever a conflict between code behavior and the rules document, the rules document overrides the code.



Mandatory Journal Requirement



Every change made to this repository MUST include a journal entry.



This includes, but is not limited to:



Code changes



Refactors



File additions or deletions



Logic fixes



Balance adjustments



Structural or organizational changes



No update is considered complete without an accompanying journal entry.



Journal Entry Format (Required)



Journal entries must follow this exact format:



\## Time and Date:

&nbsp;- <current CDT time>



\## Changes made:

&nbsp;- Example Changes



\## Reason for changes:

&nbsp;- Example reason



\## Notes:

&nbsp;- Example Notes



Rules for journal entries:



Use the current CDT time at the moment the change is made



Be factual and specific



Do not add commentary, opinions, or speculation



One journal entry per logical update (do not batch unrelated changes)



Enforcement Rules



Do not modify the journal format



Do not skip journal entries



Do not combine multiple updates into a single vague entry



If unsure how to document a change, stop and ask



Failure to follow these rules is considered an invalid update.



Final Instruction



This repository is designed so an automated agent can produce a correct, deterministic implementation of the text-based roguelite without guessing.



When in doubt:



Follow Game\_Rules\_Document.txt



Document the change



Do not invent behavior





