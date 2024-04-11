from simulator.predictor import StatefulPredictor
from collections import deque

class _State:
    def __init__(self, num_history_samples):
        self.num_history_samples = num_history_samples
        self.usage = deque(maxlen=self.num_history_samples)

class LocalmaxPredictor(StatefulPredictor):
    def __init__(self, config):
        super().__init__(config)
        self.num_history_samples = config.num_history_samples
        self.cap_to_limit = config.cap_to_limit

    def CreateState(self, vm_info):
        return _State(self.num_history_samples)

    def UpdateState(self, vm_measure, vm_state):
        usage = vm_measure["sample"]["abstract_metrics"]["usage"]
        vm_state.usage.appendleft(usage)
        
    def Predict(self, vm_states_and_num_samples):
        total_usage = 0
        last_prediction = max_total_usage
        for vm_state_and_num_sample in vm_states_and_num_samples: #for each vm
            if len(vm_state_and_num_sample.vm_state.usage) > 0:
                last_prediction = total_usage
                total_usage += vm_state_and_num_sample.vm_state.usage[1] #accumulates the resource usage
        max_total_usage = max(last_prediction, total_usage)
        return max_total_usage
        
