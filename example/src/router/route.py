from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from typing import Dict, Tuple
from src.service.tsp.tsp import run
from fastapi import Depends, HTTPException
from example.src.database.__init__ import get_db
from example.src.database.models.optimize.result import Analysis
from example.src.database.dml.analysis import analysisQuery
from example.src.service.jwt import JWTAuthenticator

# 1. FastAPI 설정
app = FastAPI()


class Waypoints(BaseModel):
    stop_fix_type: str = "Departure"
    waypoints: Dict[str, Tuple[float, float]]


class RouteOptimizer:
    def __init__(self, waypoints: Waypoints):
        self.stop_fix_type = "Departure"
        self.waypoints = waypoints
        
    def get_stop_fix_type(self):
        if self.stop_fix_type == "Departure":
            if self.stop_fix_type == "Arrival":
                return [True, True]
            else:
                return [True, False]
        else:
            if self.stop_fix_type == "Arrival":
                return [False, True]
            else:
                return [False, False]

    async def optimize_route(self) -> Dict[str, Tuple[float, float]]:
        try:
            optimized_waypoints = run(self.waypoints.waypoints, self.get_stop_fix_type()[0], self.get_stop_fix_type()[1])
            return optimized_waypoints
        except Exception as e:
            raise e


class OptAPIRouter:
    def __init__(self):
        self.router = APIRouter()

        self.optimize_waypoints()
        self.get_analysis_by_id()
        self.get_analysis_by_user()
        self.optimize_waypoints_test()

    def optimize_waypoints_test(self):
        @self.router.post("/optimize_test")
        async def _(waypoints: Waypoints):
            try:
                optimizer = RouteOptimizer(waypoints)
                optimized_route = await optimizer.optimize_route()
                return JSONResponse(status_code=200, content=optimized_route)
            except Exception as e:
                raise HTTPException(status_code=200, detail=str(e))

    def optimize_waypoints(self):
        @self.router.post("/optimize")
        async def _(waypoints: Waypoints,  current_user: str = Depends(JWTAuthenticator.get_current_user)):
            try:
                optimizer = RouteOptimizer(waypoints)
                optimized_route = optimizer.optimize_route()
                return JSONResponse(content=optimized_route)
            except Exception as e:
                raise HTTPException(status_code=200, detail=str(e))
        
    def get_analysis_by_user(self):
        @self.router.get("/analysis/user/{user_id}", response_model=List[Analysis])
        async def _(user_id: str, current_user: str = Depends(JWTAuthenticator.get_current_user), db: Session = Depends(get_db)):
            return analysisQuery.get_analysis_by_user_id(user_id)

    def get_analysis_by_id(self):
        @self.router.get("/analysis/{analysis_id}", response_model=Analysis)
        async def _(analysis_id: str, current_user: str = Depends(JWTAuthenticator.get_current_user), db: Session = Depends(get_db)):
            analysis = analysisQuery.get_analysis_by_id(analysis_id)
            if analysis is None:
                raise HTTPException(status_code=404, detail="Analysis not found")
            return analysis
