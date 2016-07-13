from __future__ import division

import numpy as np
import random
import scipy
from pandas import *
from sklearn.cluster import MeanShift

PATH_TO_RESULT_MAIN = '/home/luis/abb/'
PATH_TS_FILE = "/home/luis/abb/ts_abb.csv"
TIME_SERIES_NAMES = ['edition', 'text_nav', 'high_nav', 'file', 'refactoring',
                     'debug', 'tools', 'control', 'testing', 'search']


def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[
                             j + 1] + 1  # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1  # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

if __name__ == "__main__":

    # label the sessions and chunks with the clusters created in the previous step
    chunks = pandas.read_csv(PATH_TO_RESULT_MAIN + 'decomposed_ts.csv')
    sessions = pandas.read_csv(PATH_TO_RESULT_MAIN + 'ts_abb.csv')

    # predict the label for the sessions
    sessions_centers = pandas.read_csv(PATH_TO_RESULT_MAIN + 'sessions_centers.csv')
    ms_model = MeanShift()
    ms_model.cluster_centers_ = sessions_centers.ix[:, 0:10].as_matrix()

    sessions['label'] = ms_model.predict(sessions.loc[:, ['prop_' + e for e in TIME_SERIES_NAMES]])
    sessions.to_csv(PATH_TO_RESULT_MAIN + 'ts_abb.csv', index=False)

    # predict the label for the chunks
    chunks_centers = pandas.read_csv(PATH_TO_RESULT_MAIN + 'chunks_centers.csv', index_col=None, header=0)
    ms_model = MeanShift()
    ms_model.cluster_centers_ = chunks_centers.ix[:, 0:10].as_matrix()
    chunks['label'] = ms_model.predict(chunks.loc[:, ['prop_' + e for e in TIME_SERIES_NAMES]])
    chunks.to_csv(PATH_TO_RESULT_MAIN + 'decomposed_ts.csv', index=False)


    sizes = np.array([])
    chains = []
    for s in set(chunks['id']):
        chunks_sel = chunks[chunks['id'] == s]
        labels = chunks_sel['label']
        #chain = ' '.join(str(e) for e in labels)
        chains.append(np.array(labels).tolist())
        sizes = np.append(sizes, len(np.array(labels)))

    # compress chains
    for i in range(0, len(chains)):
        chain = chains[i]
        compressed_chain = []
        last_symbol = -1
        current_symbol = 0
        repetition_count = 1
        for j in range(0, len(chain)):
            current_symbol = chain[j]
            if current_symbol != last_symbol:
                compressed_chain = compressed_chain + [current_symbol]
            last_symbol = current_symbol
        chains[i] = [compressed_chain]

    print len(chains)
    chains = [(' '.join(str(e) for e in x)) for x in chains]
    sets = {}

    # the first iteration discovers the common clusters
    while len(chains) > 0:
        print len(chains)
        element = list.pop(chains)
        min_val = 999
        min_index = -1

        # find an element alike to the current in the chains
        for i in range(0, len(chains)):
            l = levenshtein(chains[i], element)
            if l < min_val:
                min_index = i
                min_val = l

        # or find an element within an existing set
        min_key = ''
        flag = False
        for i in sets.keys():
            content = sets[i]
            for j in content:
                l = levenshtein(j, element)
                if l < min_val:
                    min_key = i
                    min_val = l
                    flag = True

        # if the element alike was found within a set, add it there
        # else, create a new set
        if flag:
            sets[min_key] = sets[min_key] + [element]
            print '     Found in sets'
        else:
            sets[str(len(sets)+1)] = [element] + [chains[min_index]]
            del chains[min_index]
            print '     Found in chains'

    for i in sets.keys():
        print len(sets[i])

    print "Second iteration"

    # the second iteration reassigns the remaining chains to a set
    print len(sets)
    remaining = []
    for i in sets.keys():
        contents = sets[i]
        if len(i) < 4:
            remaining = remaining + contents
            del sets[i]
    print len(sets)
    while len(remaining) > 0:
        element = list.pop(remaining)
        min_val = 999
        min_key = ''
        for i in sets.keys():
            content = sets[i]
            for j in content:
                l = levenshtein(j, element)
                if l < min_val:
                    min_key = i
                    min_val = l
        sets[min_key] = sets[min_key] + [element]

