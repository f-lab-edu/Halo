from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from abc import ABC, abstractmethod

import networkx as nx
from typing import Tuple, List

from src.repo.log.__init__ import handler, Log
from src.service.tsp.a_star import *
from src.service.tsp.q import *

class RouteOptimizer(ABC):
    @abstractmethod
    def optimize_route(self, matrix) -> Tuple[int, List[int]]:
        pass


class RouteOptimizer(ABC):
    @abstractmethod
    def optimize_route(self, matrix, start_fixed=False, end_fixed=False) -> Tuple[int, List[int]]:
        pass


class RouteOptimizer(ABC):
    @abstractmethod
    def optimize_route(self, matrix, start_fixed=False, end_fixed=False) -> Tuple[int, List[int]]:
        pass


def create_data_model(matrix):
    data = {}
    data['distance_matrix'] = matrix

    data['num_vehicles'] = 1
    data['depot'] = 0

    return data
  
class OrToolsRouteOptimizer(RouteOptimizer):
    def __init__(self, logger):
        self.logger = logger if logger else handler

    def optimize_route(self, matrix, start_fixed=False, end_fixed=False) -> tuple:
        """
        Args:
            matrix: The distance matrix

        Returns:
            The objective value and the solution
        """
        try:
            data = create_data_model(matrix)

            start_index = 0 if start_fixed else data['depot']
            end_index = len(matrix) - 1 if end_fixed else data['depot']

            manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                                   data['num_vehicles'],
                                                   [start_index],
                                                   [end_index])

            routing = pywrapcp.RoutingModel(manager)

            def distance_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                return int(data['distance_matrix'][from_node][to_node])

            transit_callback_index = routing.RegisterTransitCallback(
                distance_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

            solution = routing.SolveWithParameters(search_parameters)

            if solution:
                self.logger.log.info("Objective: %s" % 
                                 solution.ObjectiveValue())  # type: ignore
                self.logger.log.info("Route: ")  # type: ignore

                objective_value = solution.ObjectiveValue()
                path = []
                index = routing.Start(0)

                while not routing.IsEnd(index):
                    path.append(manager.IndexToNode(index))
                    index = solution.Value(routing.NextVar(index))

                path.append(manager.IndexToNode(index))

                return objective_value, path
            else:
                return None, None

        except Exception as e:
            self.logger.log.error("Ortools error: %s" % e)  # type: ignore
            return None, None


class QLearningRouteOptimizer(RouteOptimizer):
    def __init__(self, logger):
        self.logger = logger if logger else handler

    def optimize_route(self, matrix, start_fixed=False, end_fixed=False) -> tuple:
        """
        Args:
            matrix: The distance matrix

        Returns:
            The objective value and the solution
        """
        try:
            graph = nx.from_numpy_array(np.array(matrix))

            origin_node = 0 if start_fixed else None
            destination_node = len(matrix) - 1 if end_fixed else None

            if origin_node is None:
                origin_node = 0
            if destination_node is None:
                destination_node = len(matrix) - 1

            env = RouteEnv(graph, origin_node, destination_node)
            agent = QLearningAgent(env)
            agent.train(1000)

            state = env.reset()
            done = False
            path = [state]

            while not done:
                action = agent.choose_action(state)
                next_state, _, done = env.step(action)
                path.append(next_state)
                state = next_state

            objective_value = 0
            for i in range(len(path) - 1):
                objective_value += matrix[path[i]][path[i + 1]]

            return objective_value, path

        except Exception as e:
            self.logger.log.error("Q-Learning error: %s" % e)
            return None, None


class AStarRouteOptimizer(RouteOptimizer):
    def __init__(self, logger):
        self.logger = logger if logger else handler

    def optimize_route(self, matrix, start_fixed=False, end_fixed=False):
        """
        Args:
            matrix: The distance matrix

        Returns:
            The objective value and the solution
        """
        try:
            graph = nx.from_numpy_array(np.array(matrix))

            origin_node = 0 if start_fixed else None
            destination_node = len(matrix) - 1 if end_fixed else None

            if origin_node is None:
                origin_node = 0
            if destination_node is None:
                destination_node = len(matrix) - 1

            path = nx.astar_path(graph, origin_node,
                                 destination_node, weight='weight')

            objective_value = 0
            for i in range(len(path) - 1):
                objective_value += matrix[path[i]][path[i + 1]]

            return objective_value, path

        except Exception as e:
            self.logger.log.error("A* error: %s" % e)
            return None, None
