import os.path
from argparse import RawTextHelpFormatter
import argparse
import estimators
import time
import sys

# Set up command line argument parser
parser = argparse.ArgumentParser(description="Estimate result size of path queries on a graph by computing a summary.\n"
                                             "After the graph summary is created it can be queried using input of \n"
                                             "the form ID1 ID2 ID3 or a filename containing lines of inputs of this form.\n"
                                             "The script will terminate after an empty line has been entered.\n"
                                             "\n"
                                             "Estimators available:\n"
                                             "BruteForce\t brute force, always 100% accurate, ignores b", formatter_class=RawTextHelpFormatter)
parser.add_argument('estimator', type=str, help='estimator to use')
parser.add_argument('file', type=file, help='filename of the graph data file')
parser.add_argument('k', type=long, help='maximum path length')
parser.add_argument('b', type=long, help='budget of b bytes to take up for graph summary storage')
parser.add_argument('--verbose', default=False, const=True, nargs='?', help='if passed outputs all information, otherwise only summaries and averages')

estimator = None
bruteForce = estimators.BruteForce()
estimation_times = []
estimation_accuracies = []
verbose = False


def generate_graph_summary(cli_arguments):
    # Load contents of graph data file into the estimator
    graph = set(tuple(line.rstrip().split(' ')) for line in cli_arguments.file)
    bruteForce.load(graph, cli_arguments.k, cli_arguments.b)

    ts = time.time()
    estimator.load(graph, cli_arguments.k, cli_arguments.b)
    graph_summary_time = max(0, (time.time() - ts)) * 1000
    print "# Graph summary generation bonus\n%s\tmilliseconds\n%s\tbytes" % (graph_summary_time, estimator.summary_size())


def process_line(line, output=False):
    # Read the line into a path
    path = line.strip().split(' ')
    if len(path) == 0:
        if verbose:
            print 'Skipping badly formatted line: %s' % line
        return

    # Turn list into list of tuples
    it = iter(path)
    path = zip(it, it)

    # Estimate and time
    ts = time.time()
    estimation = estimator.estimate(path)
    estimation_time = time.time() - ts
    estimation_times.append(max(0, estimation_time) * 1000)

    # Determine the accuracy
    actual_result = bruteForce.estimate(path)
    if actual_result == 0:
        accuracy = 1 if actual_result == estimation else 0
    else:
        accuracy = float(estimation) / float(actual_result)
    estimation_accuracies.append(accuracy)

    if verbose or output:
        print "%s\t%s\t%s\t%s\t%s" % (line, estimation, actual_result, accuracy, estimation_time * 1000)

    return True


def process_file(filename):
    with open(filename) as f:
        lines = f.readlines()
    for l in lines:
        process_line(l)
    return True


def listen():
    input_line = raw_input('')
    if not input_line:  # empty input, terminate
        return False

    if os.path.isfile(input_line):
        process_file(input_line)
    else:
        process_line(input_line, True)

    return True


if __name__ == "__main__":
    args = parser.parse_args()
    verbose = args.verbose

    # Check if estimator exists
    if not hasattr(estimators, args.estimator):
        raise RuntimeError('Estimator ' + args.estimator + ' is not available')

    # Set global estimator
    estimator = getattr(estimators, args.estimator)()
    if estimator is None:
        raise RuntimeError('No estimator instantiated')

    # Generate the graph summary
    if verbose:
        print '# Starting graph summary generation'
    generate_graph_summary(args)

    if verbose:
        print "# Estimations"

    while listen():
        continue

    average_times = (sum(estimation_times) / float(len(estimation_times))) if len(estimation_times) > 0 else 0
    average_accuracy = (sum(estimation_accuracies) / float(len(estimation_accuracies))) if len(estimation_accuracies) > 0 else 0

    print "# Average of estimations\n%s\t milliseconds\n%s\taccuracy" % (average_times, average_accuracy)

else:
    raise RuntimeError('This file can only be run as a top-level script')
