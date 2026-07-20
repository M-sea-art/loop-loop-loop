"""Registry of reusable expert capability profiles."""

from __future__ import annotations

from dataclasses import dataclass
import re


_PROFILE_ID = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class ExpertProfile:
    """Capability metadata.

    Registering a profile does not create a process, agent, or Codex session.
    """

    profile_id: str
    capabilities: tuple[str, ...]
    cost: str = "medium"
    evidence_required: bool = True

    def __post_init__(self) -> None:
        if not _PROFILE_ID.fullmatch(self.profile_id):
            raise ValueError("profile_id must use lowercase snake_case")
        if not self.capabilities or any(not item.strip() for item in self.capabilities):
            raise ValueError("capabilities must contain non-empty values")
        if self.cost not in {"low", "medium", "high"}:
            raise ValueError("cost must be low, medium, or high")


class ExpertRegistry:
    def __init__(self, profiles: tuple[ExpertProfile, ...] = ()):
        self._profiles: dict[str, ExpertProfile] = {}
        for profile in profiles:
            self.register(profile)

    def register(self, profile: ExpertProfile) -> None:
        if profile.profile_id in self._profiles:
            raise ValueError(f"duplicate expert profile: {profile.profile_id}")
        self._profiles[profile.profile_id] = profile

    def get(self, profile_id: str) -> ExpertProfile:
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise KeyError(f"unknown expert profile: {profile_id}") from exc

    def all(self) -> tuple[ExpertProfile, ...]:
        return tuple(self._profiles[key] for key in sorted(self._profiles))

    def match(self, required_capabilities: tuple[str, ...]) -> tuple[ExpertProfile, ...]:
        required = set(required_capabilities)
        if not required:
            return self.all()
        matches = [
            profile
            for profile in self._profiles.values()
            if required.issubset(set(profile.capabilities))
        ]
        cost_rank = {"low": 0, "medium": 1, "high": 2}
        return tuple(
            sorted(matches, key=lambda item: (cost_rank[item.cost], item.profile_id))
        )


def default_registry() -> ExpertRegistry:
    """Return built-in capability profiles without instantiating agents."""

    return ExpertRegistry(
        (
            ExpertProfile(
                "game_director",
                ("game_direction", "gameplay", "product_scope"),
                cost="high",
            ),
            ExpertProfile(
                "software_architect",
                ("architecture", "refactor", "code_review"),
            ),
            ExpertProfile(
                "builder",
                ("implementation", "refactor", "integration"),
            ),
            ExpertProfile(
                "visual_designer",
                ("visual_design", "interaction_design", "visual_review"),
            ),
            ExpertProfile(
                "writer",
                ("writing", "editing", "content_structure"),
                cost="low",
            ),
            ExpertProfile(
                "qa_engineer",
                ("testing", "product_qa", "evidence"),
            ),
            ExpertProfile(
                "researcher",
                ("research", "source_verification", "synthesis"),
            ),
        )
    )
