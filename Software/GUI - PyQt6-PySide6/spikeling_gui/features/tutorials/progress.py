"""Local tutorial progress (v2 curriculum), independent of experimental files."""
from __future__ import annotations

from spikeling_gui.preferences import preference_store


PREFIX = "tutorials/v2"


class TutorialProgress:
    def __init__(self, store=None):
        self.store = store if store is not None else preference_store()

    def is_complete(self, tutorial_id: str) -> bool:
        return str(self.store.value(f"{PREFIX}/{tutorial_id}/complete", "false")).lower() == "true"

    def mark_complete(self, tutorial_id: str) -> None:
        self.store.setValue(f"{PREFIX}/{tutorial_id}/complete", "true")
        self.clear_resume()
        self.store.sync()

    def save_resume(self, tutorial_id: str, step_id: str) -> None:
        self.store.setValue(f"{PREFIX}/active_tutorial", tutorial_id)
        self.store.setValue(f"{PREFIX}/active_step", step_id)
        self.store.sync()

    def get_resume(self) -> tuple[str, str] | None:
        tutorial_id = self.store.value(f"{PREFIX}/active_tutorial", "")
        step_id = self.store.value(f"{PREFIX}/active_step", "")
        return (str(tutorial_id), str(step_id)) if tutorial_id and step_id else None

    def clear_resume(self) -> None:
        self.store.remove(f"{PREFIX}/active_tutorial")
        self.store.remove(f"{PREFIX}/active_step")
        self.store.sync()

    def save_response(self, tutorial_id: str, step_id: str, text: str) -> None:
        """Optional free text stays in the user's local Qt settings only."""
        key = f"{PREFIX}/{tutorial_id}/{step_id}/response"
        if text.strip():
            self.store.setValue(key, text)
        else:
            self.store.remove(key)
        self.store.sync()

    def get_response(self, tutorial_id: str, step_id: str) -> str:
        return str(self.store.value(f"{PREFIX}/{tutorial_id}/{step_id}/response", ""))
