from task_allocation.allocation import Allocation


class RandomAllocation(Allocation):
    def __init__(self, randomizer):
        super().__init__()
        self.randomizer = randomizer

    def allocate_jobs(self, jobs):
        return self.randomizer.choice(jobs)
