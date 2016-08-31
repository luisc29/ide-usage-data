from __future__ import division

import numpy as np
import random
import scipy
from pandas import *
from sklearn.cluster import AffinityPropagation, MeanShift, KMeans
from sklearn.metrics import silhouette_score

PATH_TO_ABB = '/home/luis/abb/'
PATH_TO_UDC = '/home/luis/udc/'
TIME_SERIES_NAMES = ['edition', 'text_nav', 'high_nav', 'file', 'refactoring',
                     'debug', 'tools', 'control', 'testing', 'search']


def calc_proportions(data):
    """
    Calculates the proportion of type of events for every session
    """
    dic = {}
    for i in TIME_SERIES_NAMES:
        dic[i] = []
        
    for i in range(0,len(data)):
        session = data.iloc[i]
        n_events = session['n_events']
        for ts in TIME_SERIES_NAMES:
            values = [int(x) for x in session[ts].split(' ')]
            sum_values = sum(values)
            prop = 0 if sum_values == 0 else sum_values/n_events
            dic[ts].append(prop)
    
    for i in TIME_SERIES_NAMES:
        data['prop_' + i] = dic[i]
        
    return data

def pipeline(chunks, directory, chunks_file_name, chunks_centers_file_name, n_clus, bw):
    """
    Main pipeline for the first phase of data mining.
    Chunks clustering.
    """
    # calculate the proportion of events
    chunks = calc_proportions(chunks)

    print 'Clustering first model...'
    first_model = KMeans(n_clusters=2000, n_jobs=4)
    first_model.fit(chunks.ix[:,15:25])
    centers = first_model.cluster_centers_
    
    print 'Clustering second model...'    
    second_model = MeanShift(bandwidth=bw)
    second_model.fit(centers)
    print "Final number of clusters of chunks with MeanShift: " + str(len(second_model.cluster_centers_))
    
    chunks['label'] = second_model.predict(chunks.ix[:,15:25])
    
    centers = DataFrame(second_model.cluster_centers_, columns= TIME_SERIES_NAMES)
    centers.to_csv(directory + chunks_centers_file_name, index=False)

    chunks.to_csv(directory + chunks_file_name, index=False)

    
if __name__ == "__main__":
    
    print 'Clustering chunks with ABB'    
    
    chunks = pandas.read_csv(PATH_TO_ABB + 'abb.chunks.csv', index_col=None, header=0)
    #pipeline(chunks,PATH_TO_ABB,'abb.chunks_a.csv', 'abb.chunkscenters_a.csv', 2000, 0.40)
    
    print '\n\nClustering chunks with UDC'    
    
    chunks = pandas.read_csv(PATH_TO_UDC + 'udc.chunks.csv', index_col=None, header=0)
    pipeline(chunks,PATH_TO_UDC,'udc.chunks.csv', 'udc.chunkscenters.csv', 2000, 0.35)
    