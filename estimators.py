from abc import ABCMeta, abstractmethod
from itertools import combinations
from sys import getsizeof
from itertools import chain
from collections import deque
from math import modf


# Source: http://code.activestate.com/recipes/577504-compute-memory-footprint-of-an-object-and-its-cont/
def total_size(o, handlers={}):
    """ Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    """
    dict_handler = lambda d: chain.from_iterable(d.items())
    all_handlers = {tuple: iter,
                    list: iter,
                    deque: iter,
                    dict: dict_handler,
                    set: iter,
                    frozenset: iter,
                    }
    all_handlers.update(handlers)  # user handlers take precedence
    seen = set()  # track which object id's have already been seen
    default_size = getsizeof(0)  # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen:  # do not double count the same object
            return 0
        seen.add(id(o))
        s = getsizeof(o, default_size)

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)


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
        return total_size(self._summary)


# BruteForce estimator
class BruteForce(Abstract):
    def load(self, graph, k, b):
        self._summary = dict()
        for edge in graph:
            if edge[0] not in self._summary:
                self._summary[edge[0]] = set()
            self._summary[edge[0]].add(edge)
            if edge[2] not in self._summary:
                self._summary[edge[2]] = set()
            self._summary[edge[2]].add(edge)

    def estimate(self, path, current=None):
        # No root given, must be initial call. Run recursive on all nodes.
        if current is None:
            result = 0
            for node in self._summary:
                result += len(self.estimate(path, node))
            return result

        # Base case
        if len(path) == 0:
            return {current}

        # We have a root and at least one edge in path
        # Determine which direction to look at when we find matching edges
        if path[0][0] == '+':
            direction = 2
        else:
            direction = 0

        # Check all edges associated with this node
        result = set()
        for edge in self._summary[current]:
            if edge[1] == path[0][1] and edge[2 - direction] == current:
                result |= self.estimate(path[1:], edge[direction])
        return result


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
        self.save_summary(paths, bf)

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

    def process_summary(self):
        for key, value in self._summary.iteritems():
            for k, v in value.iteritems():
                self._summary[key][k] = (sum(self._summary[key][k]) / len(self._summary[key][k])) if len(
                    self._summary[key][k]) > 0 else 0

    def save_summary(self, paths, bf):
        for i in paths:
            forward = [('+', x) for x in i]
            exact = bf.estimate(forward)
            self._summary['s'][i[0]].append(exact)
            self._summary['e'][i[-1]].append(exact)
            self._summary['l'][len(i)].append(exact)
        self.process_summary()

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


class Median(Average):
    @staticmethod
    def median(lst):
        lst = sorted(lst)
        if len(lst) < 1:
            return None
        if len(lst) % 2 == 1:
            return lst[((len(lst) + 1) / 2) - 1]
        else:
            return float(sum(lst[(len(lst) / 2) - 1:(len(lst) / 2) + 1])) / 2.0

    def process_summary(self):
        for key, value in self._summary.iteritems():
            for k, v in value.iteritems():
                self._summary[key][k] = self.median(self._summary[key][k])


class TrimmedAverage(Average):
    @staticmethod
    def percent_tmean(data, pcent):
        # make sure data is a list
        dc = list(data)
        # find the number of items
        n = len(dc)
        # sort the list
        dc.sort()
        # get the proportion to trim
        p = pcent / 100.0
        k = n * p
        # print "n = %i\np = %.3f\nk = %.3f" % ( n,p,k )
        # get the decimal and integer parts of k
        dec_part, int_part = modf(k)
        # get an index we can use
        index = int(int_part)
        # trim down the list
        dc = dc[index: index * -1]
        return (sum(dc) / (n - 2.0 * k)) if (n - 2.0 * k) != 0 else 0

    def process_summary(self):
        for key, value in self._summary.iteritems():
            for k, v in value.iteritems():
                self._summary[key][k] = self.percent_tmean(self._summary[key][k], 10)
