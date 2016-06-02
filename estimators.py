from abc import ABCMeta, abstractmethod


# Abstract class for estimators, each estimator
# should implement a load function and an estimate function
class Abstract:
    __metaclass__ = ABCMeta

    # Protected variable to store the summary in
    _summary = None

    # Load graph, k and b into the estimator and create graph summary
    @abstractmethod
    def load(self, graph, k, b): pass

    # Estimate a path with the current graph summary
    @abstractmethod
    def estimate(self, path): pass

    def summary(self):
        return self._summary


# BruteForce estimator
class BruteForce(Abstract):
    def load(self, graph, k, b):
        self._summary = graph

    def estimate(self, path):
        nodes = None
        paths = []
        for e in path:
            nodes = self.subset(e, [n[1] for n in nodes] if nodes is not None else None)
            paths = self.add_to_paths(paths, nodes)
        return len(set(paths))

    def add_to_paths(self, paths, nodes):
        if len(paths) == 0:
            return nodes
        new_paths = []
        for p in paths:
            connections = [n[1] for n in nodes if n[0] == p[1]]
            for c in connections:
                new_paths.append((p[0], c))
        return new_paths

    def subset(self, edge, nodes=None):
        if edge[0] == '+':
            return self.subset_forward(edge[1], nodes)
        elif edge[0] == '-':
            return self.subset_backward(edge[1], nodes)

    def subset_forward(self, edge, nodes):
        if nodes is None:
            return [(t[0], t[2]) for t in self._summary if t[1] == edge]
        return [(t[0], t[2]) for t in self._summary if t[1] == edge and t[0] in nodes]

    def subset_backward(self, edge, nodes):
        if nodes is None:
            return [(t[2], t[0]) for t in self._summary if t[1] == edge]
        return [(t[2], t[0]) for t in self._summary if t[1] == edge and t[2] in nodes]


class Four(Abstract):
    def load(self, graph, k, b):
        return

    def estimate(self, path):
        return 4
