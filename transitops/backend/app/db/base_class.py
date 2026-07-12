"""Declarative base class — imported by ALL model files.

This module ONLY defines the Base class and does NOT import any models,
avoiding circular import issues. The full base.py imports all models
for Alembic autogenerate.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass
