from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from typing import Dict, Tuple
from src.service.tsp.solver import run
from example.src.config.config import Config, app
from fastapi import Depends, HTTPException
from example.src.service.jwt import JWTAuthenticator

# 1. FastAPI 설정
app = FastAPI()


class Waypoints(BaseModel):
    waypoints: Dict[str, Tuple[float, float]]


class RouteOptimizer:
    def __init__(self, waypoints: Dict[str, Tuple[float, float]]):
        self.waypoints = waypoints

    def optimize_route(self) -> Dict[str, Tuple[float, float]]:
        try:
            optimized_waypoints = run(self.waypoints)
            return optimized_waypoints
        except Exception as e:
            raise e


class OptAPIRouter:
    def __Init__(self):
        self.router = APIRouter()

    def optimize_waypoints(self):
        @app.post("/optimize")
        async def optimize(waypoints: Waypoints,  current_user: str = Depends(JWTAuthenticator.get_current_user)):
            try:
                optimizer = RouteOptimizer(waypoints.waypoints)
                optimized_route = optimizer.optimize_route()
                return optimized_route
            except Exception as e:
                raise HTTPException(status_code=200, detail=str(e))
