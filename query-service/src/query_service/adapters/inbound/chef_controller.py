"""Вхідний адаптер — REST-контролер шефів."""

from fastapi import APIRouter, HTTPException

from query_service.application.dto import ChefProfileDTO
from query_service.application.ports.inbound.chef_use_cases import ChefQueryUseCase


class ChefController:
    def __init__(self, use_case: ChefQueryUseCase) -> None:
        self._use_case = use_case
        self.router = APIRouter(prefix="/api/chefs", tags=["chefs"])
        self.router.add_api_route("/{chef_id}", self.get_chef, methods=["GET"])

    async def get_chef(self, chef_id: str) -> ChefProfileDTO:
        """GET /api/chefs/{id} — профіль і рецепти шефа. None -> HTTP 404."""
        profile = await self._use_case.get_chef_profile(chef_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="Шефа не знайдено")
        return profile
