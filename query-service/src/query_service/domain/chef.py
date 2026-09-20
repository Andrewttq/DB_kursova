"""Доменний клас шеф-кухаря."""

from dataclasses import dataclass


@dataclass
class Chef:
    id: str
    full_name: str
