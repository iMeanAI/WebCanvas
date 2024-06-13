class TaskEvaluator():
    def __init__(self):
        pass


class TaskLengthEvaluator(TaskEvaluator):
    def __init__(self, alpha=1.2):
        # Give a multiplier to the reference step number. 
        # If it is within the reference multiplier * a, give full score, otherwise give score according to the ratio
        self.alpha = alpha

    def task_length_score(self, reference_length, current_task_length):
        '''
        Judge whether the task length is within a times the reference number of steps. 
        If so, score, otherwise get reference number of steps/actual number of steps
        '''
        reference_length *= self.alpha
        if current_task_length < reference_length:
            return 1  # TODO Specific value to be determined
        else:
            return reference_length/current_task_length


class FinishTaskEvaluator(TaskEvaluator):
    
    @staticmethod
    def finish_task_score(reference_step_score, step_score):
        '''Judge whether the task is completed. If the task is completed, score'''
        if reference_step_score == step_score:
            return 1  # TODO Specific value to be determined
        else:
            return 0
