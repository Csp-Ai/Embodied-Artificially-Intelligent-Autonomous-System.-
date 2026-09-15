"""Embodiment adapters for simulation and physical backends."""

from .mujoco import MuJoCoGridConfig, MuJoCoGridEmbodiment, MuJoCoUnavailableError

__all__ = ["MuJoCoGridConfig", "MuJoCoGridEmbodiment", "MuJoCoUnavailableError"]
