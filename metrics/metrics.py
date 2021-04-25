from collections import defaultdict


class PrioritisedTaskTime:
    def __init__(self, priority_scale=None):
        if priority_scale is None:
            priority_scale = {1: 5, 2: 3, 3: 1}

        self.tasks_completed = 0
        self.prioritised_time = 0
        self.priority_scale = priority_scale
        self.priority_task_completed = defaultdict(int)
        self.priority_task_time = defaultdict(int)

    def process_completed_task(self, task):
        self.tasks_completed += 1
        self.prioritised_time += task.time_waiting * self.priority_scale[task.priority]
        self.priority_task_completed[task.priority] += 1
        self.priority_task_time[task.priority] += task.time_waiting

    def get_score(self):
        return self.prioritised_time

    def get_avg_wait_time(self):
        return {p: time/self.priority_task_completed[p] for p, time in self.priority_task_time.items()}