"""Value objects for advisory complexity assessment and authorized routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExecutionMode(str, Enum):
    """Execution collaboration modes ordered from least to most expansive."""

    SINGLE = "single"
    ASSISTED = "assisted"
    SWARM = "swarm"

    @property
    def rank(self) -> int:
        return {
            ExecutionMode.SINGLE: 0,
            ExecutionMode.ASSISTED: 1,
            ExecutionMode.SWARM: 2,
        }[self]

    @classmethod
    def lower(cls, left: "ExecutionMode", right: "ExecutionMode") -> "ExecutionMode":
        return left if left.rank <= right.rank else right


class AuthorizationSource(str, Enum):
    """Sources that are allowed to expand the collaboration ceiling."""

    DEFAULT_SINGLE = "default_single"
    CURRENT_USER_REQUEST = "current_user_request"
    USER_APPROVED_PROJECT_POLICY = "user_approved_project_policy"


@dataclass(frozen=True)
class ComplexityProfile:
    """Explicit signals used by the deterministic complexity analyzer.

    The profile is supplied by the goal-framing layer. It does not inspect or
    change Codex settings.
    """

    affected_files: int = 1
    affected_modules: int = 1
    domains: tuple[str, ...] = ("general",)
    risk_level: str = "low"
    parallel_work_items: int = 1
    specialist_capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.affected_files < 1:
            raise ValueError("affected_files must be at least 1")
        if self.affected_modules < 1:
            raise ValueError("affected_modules must be at least 1")
        if self.parallel_work_items < 1:
            raise ValueError("parallel_work_items must be at least 1")
        if not self.domains or any(not item.strip() for item in self.domains):
            raise ValueError("domains must contain non-empty values")
        if self.risk_level not in {"low", "medium", "high"}:
            raise ValueError("risk_level must be low, medium, or high")


@dataclass(frozen=True)
class ComplexityAssessment:
    recommended_mode: ExecutionMode
    score: int
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommended_mode": self.recommended_mode.value,
            "score": self.score,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class ExecutionAuthorization:
    """User-owned ceiling for collaboration expansion.

    The default is intentionally single-executor. A higher ceiling must carry
    an explicit user authorization source. This object is runtime input, not a
    Codex configuration override.
    """

    ceiling: ExecutionMode = ExecutionMode.SINGLE
    source: AuthorizationSource = AuthorizationSource.DEFAULT_SINGLE
    requested_mode: ExecutionMode | None = None
    force_single: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.source, AuthorizationSource):
            raise ValueError("authorization source must be an approved user-owned source")
        if (
            self.ceiling is not ExecutionMode.SINGLE
            and self.source is AuthorizationSource.DEFAULT_SINGLE
        ):
            raise ValueError("expanded collaboration requires explicit user authorization")
        if self.requested_mode and self.requested_mode.rank > self.ceiling.rank:
            raise ValueError("requested_mode cannot exceed the authorized ceiling")

    @classmethod
    def user_authorized(
        cls,
        ceiling: ExecutionMode,
        *,
        requested_mode: ExecutionMode | None = None,
        source: AuthorizationSource = AuthorizationSource.CURRENT_USER_REQUEST,
    ) -> "ExecutionAuthorization":
        return cls(ceiling=ceiling, requested_mode=requested_mode, source=source)


@dataclass(frozen=True)
class RoutingDecision:
    recommended_mode: ExecutionMode
    authorized_ceiling: ExecutionMode
    selected_mode: ExecutionMode
    authorization_source: AuthorizationSource
    reasons: tuple[str, ...] = ()
    codex_settings_preserved: bool = field(default=True, init=False)

    @property
    def needs_additional_authorization(self) -> bool:
        return self.recommended_mode.rank > self.authorized_ceiling.rank

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommended_mode": self.recommended_mode.value,
            "authorized_ceiling": self.authorized_ceiling.value,
            "selected_mode": self.selected_mode.value,
            "authorization_source": self.authorization_source.value,
            "reasons": list(self.reasons),
            "needs_additional_authorization": self.needs_additional_authorization,
            "codex_settings_preserved": self.codex_settings_preserved,
        }
