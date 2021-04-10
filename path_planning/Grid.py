from path_planning.Environment import *
import numpy as np


class Grid(Environment):
    MOVEMENTS = np.array([[1, 0], [0, 1], [-1, 0], [0, -1], [0, 0]])

    def __init__(self, grid):
        super().__init__()
        self.grid = grid

    def next(self, node, t):
        curr_pos = np.array(node)
        next_pos = curr_pos + Grid.MOVEMENTS
        next_pos = next_pos[self.is_valid(next_pos)]
        return list(zip(map(tuple, next_pos), np.ones(next_pos.shape[0])))

    def estimate(self, node1, node2, t):
        return abs(node1[0] - node2[0]) + abs(node1[1] - node2[1])

    def is_valid(self, pos):
        valid = np.ones(pos.shape[0]).astype(bool)
        # Check valid with edges
        valid = np.logical_and(valid, pos[:, 0] >= 0)
        valid = np.logical_and(valid, pos[:, 1] >= 0)
        valid = np.logical_and(valid, pos[:, 0] < self.grid.shape[0])
        valid = np.logical_and(valid, pos[:, 1] < self.grid.shape[1])
        # Check valid with obstacles
        valid[valid] = np.logical_and(valid[valid], ~self.grid[pos[valid, 0], pos[valid, 1]])
        # Return mask of which positions are valid
        return valid
