from abc import ABC, abstractmethod


# Extend this class to run any of the MAPF implementations
# Note: node can be anything, as long as it is hashable and has __equals__ implemented (for example, tuples work)
class Environment(ABC):

    def __init__(self, *args, **kwargs):
        super().__init__()

    @abstractmethod
    def next(self, node, t):
        pass  # returns a list of (next_node, cost) tuples. this represents the children of node at time t.

    @abstractmethod
    def estimate(self, node, goal, t):
        pass  # returns an estimate of the cost to travel from the current node to the goal node
