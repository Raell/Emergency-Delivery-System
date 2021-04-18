from path_planning.Astar import *
from queue import PriorityQueue
import numpy as np


def cbs(env, starts, goals):
    pq = PriorityQueue()
    root = Constraint()
    root.find_paths(env, starts, goals)
    mask = np.array(root.cost) != float('inf')
    root_cost = np.sum(np.array(root.cost)[mask])
    pq.put_nowait((root_cost, root.depth, root))
    while not pq.empty():
        cost, _, x = pq.get_nowait()
        conflict = find_conflict(x.solution)
        if conflict is None:
            return x.solution
        else:
            for agent in ['agent1', 'agent2']:
                child = x.create_child()
                if not conflict['transition']:
                    is_new_constraint = child.add_constraint(agent=conflict[agent], t=conflict['t'],
                                                             node=conflict['node'])
                else:
                    if agent == 'agent1':
                        is_new_constraint = child.add_transition_constraint(agent=conflict['agent1'], t=conflict['t'],
                                                                            node=conflict['node'],
                                                                            lastnode=conflict['lastnode'])
                    else:
                        is_new_constraint = child.add_transition_constraint(agent=conflict['agent2'], t=conflict['t'],
                                                                            node=conflict['lastnode'],
                                                                            lastnode=conflict['node'])
                if is_new_constraint:
                    child.find_paths(env, starts, goals)
                    child_cost = np.sum(np.array(child.cost)[mask])
                    pq.put_nowait((child_cost, child.depth + np.random.rand(1)[0], child))
    return None


class Constraint:

    def __init__(self):
        self.constraints = {}
        self.transition_constraints = {}
        self.children = []
        self.solution = None
        self.cost = None
        self.depth = 0
        self.T = 0

    def create_child(self):
        child = Constraint()
        child.constraints = self.constraints.copy()
        child.transition_constraints = self.transition_constraints.copy()
        child.depth = self.depth + 1
        child.T = self.T
        self.children.append(child)
        return child

    def add_constraint(self, agent, t, node):
        if agent not in self.constraints:
            self.constraints[agent] = {}
        if t not in self.constraints[agent]:
            self.constraints[agent][t] = set()
        if node in self.constraints[agent][t]:
            return False
        self.constraints[agent][t].add(node)
        self.T = max(self.T, t)
        return True

    def add_transition_constraint(self, agent, t, node, lastnode):
        if agent not in self.transition_constraints:
            self.transition_constraints[agent] = {}
        if t not in self.transition_constraints[agent]:
            self.transition_constraints[agent][t] = {}
        if node not in self.transition_constraints[agent][t]:
            self.transition_constraints[agent][t][node] = set()
        if lastnode in self.transition_constraints[agent][t][node]:
            return False
        self.transition_constraints[agent][t][node].add(lastnode)
        self.T = max(self.T, t)
        return True

    def get_constraint_fn(self, agent):
        def constraint_fn(node, lastnode, t):
            overlap = node in self.constraints.get(agent, {}).get(t, set())
            swap = lastnode in self.transition_constraints.get(agent, {}).get(t, {}).get(node, set())
            return (not overlap) and (not swap)

        return constraint_fn

    def find_paths(self, env, starts, goals):
        paths = [None] * len(starts)
        costs = [None] * len(starts)
        for agent in range(len(starts)):
            path, cost = astar(env=env, start=starts[agent], goal=goals[agent],
                               constraint_fn=self.get_constraint_fn(agent), return_cost=True)
            paths[agent] = path
            costs[agent] = cost
        self.T = max(self.T, max([len(path) for path in paths]))
        for agent in range(len(starts)):
            start_t = len(paths[agent]) - 1
            hold_path = stay(env=env, start=paths[agent][-1], goal=goals[agent],
                             constraint_fn=self.get_constraint_fn(agent), start_t=start_t, T=self.T)
            paths[agent] = paths[agent] + hold_path[1:]
        self.solution = paths
        self.cost = costs


def find_conflict(paths):
    maxlength = min(map(lambda path: len(path) if path is not None else 0, paths))
    last_states = {}
    for t in range(maxlength):
        # Check collisions
        states = {}
        for agent in range(len(paths)):
            if paths[agent] is None:
                continue
            if t < len(paths[agent]):
                node = paths[agent][t]
            else:
                node = paths[agent][-1]
            if node in states:
                other_agent = states[node]
                return {'agent1': agent, 'agent2': other_agent, 't': t, 'node': node, 'transition': False}
            states[node] = agent
        # Check swaps
        for node, agent in states.items():
            if node in last_states:  # if agent has moved into a spot that was just occupied, get the other agent who just moved out
                other_agent = last_states[node]
                if other_agent != agent:
                    last_node = paths[agent][t - 1]
                    if paths[other_agent][
                        t] == last_node:  # if the agent's last spot is now occupied by that other agent, it's a swap
                        return {'agent1': agent, 'agent2': other_agent, 't': t, 'node': node, 'lastnode': last_node,
                                'transition': True}
        last_states = states
    return None
