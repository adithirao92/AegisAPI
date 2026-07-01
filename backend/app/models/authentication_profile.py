"""Persistence-oriented authentication profile model for Phase 2."""

from __future__ import annotations

from app.schemas.auth import AuthenticationProfile


class AuthenticationProfileModel(AuthenticationProfile):
    """Thin ORM-ready wrapper around the authentication profile schema."""

    pass
