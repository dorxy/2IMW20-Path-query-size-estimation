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
        # TODO implement brute force of estimation
        return 1
