
class PrioritisedTaskTime:
    def __init__(self, priority_scale=None):
        if priority_scale is None:
            priority_scale = {1: 5, 2: 3, 3: 1}

        self.tasks_completed = 0
        self.prioritised_time = 0
        self.priority_scale = priority_scale

    def process_completed_task(self, task):
        self.tasks_completed += 1
        self.prioritised_time += task.time_waiting * self.priority_scale[task.priority]

    def get_score(self):
        return self.prioritised_time