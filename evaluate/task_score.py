class TaskEvaluator():
    def __init__(self):
        pass


class TaskLengthEvaluator(TaskEvaluator):
    def __init__(self, alpha=1.2):
        # 将参考步数给出一个倍率，如果在参考倍率*a以内给满分，否则根据比例给分
        self.alpha = alpha

    
    def task_length_score(self, reference_length, current_task_length):
        '''判断是否任务长度是否在参考步数的α倍内，是则得分，否则得到 参考步数/实际步数'''
        reference_length *= self.alpha
        if current_task_length < reference_length:
            return 1  # TODO 具体数值待定
        else:
            return reference_length/current_task_length


class FinishTaskEvaluator(TaskEvaluator):
    
    @staticmethod
    def finish_task_score(reference_step_score, step_score):
        '''判断是否完成任务，完成任务则得分'''
        if reference_step_score == step_score:
            return 1  # TODO 具体数值待定
        else:
            return 0
