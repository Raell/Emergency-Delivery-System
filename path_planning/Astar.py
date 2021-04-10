from queue import PriorityQueue
from collections import deque
import itertools
import numpy as np


def astar(env, start, goal, constraint_fn=lambda node, lastnode, t: True, return_cost=False):
    # env is an instance of an Environment subclass
    # start is an instance of node (whatever type you define)
    # end is an instance of node
    # constraint_fn(node, t) returns False if node at time t is invalid
    if isinstance(start, np.ndarray):
        start = tuple(start)
    if isinstance(goal, np.ndarray):
        goal = tuple(goal)
    pq = PriorityQueue()
    cost = 0.0
    t = 0.0
    heur = env.estimate(start, goal, t)
    costmap = {start: cost}
    prevmap = {start: None}
    best = (None, float('inf'))
    pq.put((heur + cost, start, t))
    while not pq.empty():
        totcost, curr, t = pq.get()
        if totcost < best[1]:
            best = (curr, totcost)
        if curr == goal:
            if return_cost:
                return (construct_path(prevmap, curr), totcost)
            else:
                return construct_path(prevmap, curr)
        for child, step_cost in env.next(curr, t):
            child_t = t + 1
            if not constraint_fn(child, curr, child_t):
                continue
            child_cost = costmap.get(curr, float('inf')) + step_cost
            if child_cost < costmap.get(child, float('inf')):
                prevmap[child] = curr
                costmap[child] = child_cost
                child_totcost = env.estimate(child, goal, child_t) + child_cost
                pq.put((child_totcost, child, child_t))
    if return_cost:
        return (construct_path(prevmap, best[0]), float('inf'))
    else:
        return construct_path(prevmap, best[0])


def astar_multi(env, starts, goals, constraint_fn=lambda node, lastnode, t: True):
    starts = tuple(starts)
    goals = tuple(goals)
    pq = PriorityQueue()
    cost = 0.0
    t = 0.0
    heur = sum([env.estimate(start, goal, t) for start, goal in zip(starts, goals)])
    costmap = {starts: cost}
    prevmap = {starts: None}
    pq.put((heur + cost, starts, t))
    while not pq.empty():
        totcost, curr, t = pq.get()
        at_goal = all([node == goal for node, goal in zip(curr, goals)])
        if at_goal:
            return construct_path_multi(prevmap, curr)
        transitions = [env.next(node, t) for node in curr]
        children = [[t[0] for t in node] for node in transitions]
        step_costs = [[t[1] for t in node] for node in transitions]
        children_combined = combine_actions(children)
        step_costs_combined = combine_actions(step_costs)
        for child, step_cost in zip(children_combined, step_costs_combined):
            if len(set(child)) < len(child):  # skip if there is a collision
                continue
            child_t = t + 1
            if not constraint_fn(child, curr, child_t):
                continue
            child_cost = costmap.get(curr, float('inf')) + sum(step_cost)
            if child_cost < costmap.get(child, float('inf')):
                prevmap[child] = curr
                costmap[child] = child_cost
                child_totcost = sum(
                    [env.estimate(child_i, goal_i, child_t) for child_i, goal_i in zip(child, goals)]) + child_cost
                pq.put((child_totcost, child, child_t))
    return None


def combine_actions(node_list):
    return itertools.product(*node_list)


def construct_path(prevmap, node):
    seq = deque([node])
    while prevmap[node] != None:
        prev = prevmap[node]
        seq.appendleft(prev)
        node = prev
    return list(seq)


def construct_path_multi(prevmap, nodes):
    seqs = [deque([node]) for node in nodes]
    while prevmap[nodes] != None:
        prevs = prevmap[nodes]
        for i, prev in enumerate(prevs):
            seqs[i].appendleft(prev)
        nodes = prevs
    return [list(seq) for seq in seqs]


def stay(env, start, goal, constraint_fn=lambda node, lastnode, t: True, start_t=0, T=0):
    # env is an instance of an Environment subclass
    # start is an instance of node (whatever type you define)
    # end is an instance of node
    # constraint_fn(node, t) returns False if node at time t is invalid
    if isinstance(start, np.ndarray):
        start = tuple(start)
    if isinstance(goal, np.ndarray):
        goal = tuple(goal)
    pq = PriorityQueue()
    t = start_t
    heur = env.estimate(start, goal, t)
    tmap = {start: t}
    prevmap = {(start, t): (None, t - 1)}
    best = ((start, t), float('inf'))
    pq.put((heur, start, t))
    while not pq.empty():
        heur, curr, t = pq.get()
        if t == T:
            if heur < best[1]:
                best = ((curr, t), heur)
            if curr == goal:
                return construct_path_stay(prevmap, (curr, t))
        if t >= T:
            continue
        for child, _ in env.next(curr, t):
            child_t = t + 1
            if not constraint_fn(child, curr, child_t):
                continue
            if child_t > tmap.get(child, 0):
                tmap[child] = child_t
                prevmap[(child, child_t)] = (curr, t)
                child_heur = env.estimate(child, goal, child_t)
                pq.put((child_heur, child, child_t))
    path = construct_path_stay(prevmap, best[0])
    for t in range(len(path), T - start_t + 1):
        path.append(path[-1])
    return path


def construct_path_stay(prevmap, node):
    seq = deque([node[0]])
    while prevmap[node][0] != None:
        prev = prevmap[node]
        seq.appendleft(prev[0])
        node = prev
    return list(seq)
