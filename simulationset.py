__author__ = 'taghawi'
class SimulationSet:
    def __init__(self, input_keys, target):
        self.input_keys = input_keys
        self.target = self.encode(target)
        self.input = []
        self.result = []

    def encode(self, what):
        return [what[category][key] for category, key in self.keys]

    def insert(self, input, output):
        self.input.append(self.encode(input))
        self.result.append(self.metric(output))

    def metric(self, output):
        output = self.encode(output)
        return sum(((self.target - output) / self.target) ** 2)
