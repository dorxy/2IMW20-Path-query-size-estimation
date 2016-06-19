from abc import ABCMeta, abstractmethod
from itertools import combinations
import sys


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

    def summary_size(self):
        return sys.getsizeof(self._summary)


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


class Language(Abstract):
    def load(self, graph, k, b):
        # Set up an empty summary
        self._summary = dict()

        # First pass over the edges, counting the edge types and counting the options for all nodes
        counts = dict()
        node_options = dict()
        for t in graph:
            # Count the edge type
            if t[1] in counts:
                counts[t[1]] += 1
            else:
                counts[t[1]] = 1

            # For the source node, count the forward option
            if t[0] not in node_options:
                node_options[t[0]] = dict()
            if ('+', t[1]) not in node_options[t[0]]:
                node_options[t[0]][('+', t[1])] = 1
            else:
                node_options[t[0]][('+', t[1])] += 1

            # For the target node, count the backward option
            if t[2] not in node_options:
                node_options[t[2]] = dict()
            if ('-', t[1]) not in node_options[t[2]]:
                node_options[t[2]][('-', t[1])] = 1
            else:
                node_options[t[2]][('-', t[1])] += 1

        # Add the counts to the summary, we need these for the queries
        self._summary['counts'] = counts

        # Second pass
        table = dict()
        for t in graph:
            # Make sure the edge type has both entries in the table
            if ('+', t[1]) not in table:
                table[('+', t[1])] = dict()
                table[('-', t[1])] = dict()

            # Add options of taking this edge forward to the options of taking this edge type forward
            for o in node_options[t[2]]:
                if o not in table[('+', t[1])]:
                    table[('+', t[1])][o] = node_options[t[2]][o]
                else:
                    table[('+', t[1])][o] += node_options[t[2]][o]

            # Do the same for taking this edge backward
            for o in node_options[t[0]]:
                if o not in table[('-', t[1])]:
                    table[('-', t[1])][o] = node_options[t[0]][o]
                else:
                    table[('-', t[1])][o] += node_options[t[0]][o]

        # Divide options by counts
        for c in counts:
            for t in table[('+', c)]:
                table[('+', c)][t] *= 1.0 / counts[c]
            for t in table[('-', c)]:
                table[('-', c)][t] *= 1.0 / counts[c]

        # Add the edge type options table to the summary
        self._summary['table'] = table

    def estimate(self, path):
        if path[0][1] not in self._summary['counts']:
            return 0
        total = self._summary['counts'][path[0][1]]
        for i in range(1, len(path)):
            if total == 0:
                return total
            if path[i] not in self._summary['table'][path[i - 1]]:
                return 0
            total *= self._summary['table'][path[i - 1]][path[i]]
        return total

    def summary_size(self):
        size = sys.getsizeof(self._summary)
        for sub in self._summary:
            size += sys.getsizeof(sub)
        for sub in self._summary['table']:
            size += sys.getsizeof(sub)
        return size


class Four(Abstract):
    def load(self, graph, k, b):
        return

    def estimate(self, path):
        return 4


class Average(Abstract):
    _summary = dict()

    def load(self, graph, k, b):
        paths = self.all_paths(graph, k)
        bf = BruteForce()
        bf.load(graph, k, b)
        self.initialize_summary(graph, k)
        self.save_averages(paths, bf)

    def initialize_summary(self, graph, k):
        self._summary = dict()
        self._summary['s'] = dict()
        self._summary['e'] = dict()
        self._summary['l'] = dict()
        for i in self.relations(graph):
            self._summary['s'][i] = []
            self._summary['e'][i] = []
        for i in range(1, k + 1):
            self._summary['l'][i] = []

    def average_summary(self):
        for key, value in self._summary.iteritems():
            for k, v in value.iteritems():
                self._summary[key][k] = sum(self._summary[key][k]) / len(self._summary[key][k])

    def save_averages(self, paths, bf):
        for i in paths:
            forward = [('+', x) for x in i]
            exact = bf.estimate(forward)
            self._summary['s'][i[0]].append(exact)
            self._summary['e'][i[-1]].append(exact)
            self._summary['l'][len(i)].append(exact)
        self.average_summary()

    def relations(self, graph):
        # Determine all types of relations present in the graph
        return set([t[1] for t in graph])

    def all_paths(self, graph, k):
        r = list(self.relations(graph))
        combs = []
        for i in range(1, k + 1):  # all forward paths
            combs.extend([list(x) for x in combinations(r, i)])
        return combs

    def estimate(self, path):
        if len(path) not in self._summary['l']:
            raise Exception('This length has not been summarized!')
        try:
            return (
                   self._summary['s'][path[0][1]] + self._summary['e'][path[-1][1]] + self._summary['l'][len(path)]) / 3
        except KeyError:
            return 0
