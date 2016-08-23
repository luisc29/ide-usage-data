from __future__ import division

import numpy as np
import random
import scipy
from pandas import *
from sklearn.cluster import AffinityPropagation, MeanShift     

PATH_TO_ABB = '/home/luis/abb/'
PATH_TO_UDC = '/home/luis/udc/'
TIME_SERIES_NAMES = ['edition', 'text_nav', 'high_nav', 'file', 'refactoring',
                     'debug', 'tools', 'control', 'testing', 'search']


def calc_metrics(data):
    """
    Calculates the metrics for every session in the data
    """
    nrows = len(data)
    types_edit = ['edition', 'refactoring', 'text_nav']
    types_selection = ['high_nav', 'search', 'debug']
    emin = []
    smin = []
    eratio = []
    for i in range(0,nrows):
        sum_edits = 0
        sum_selections = 0
        for j in range(0, len(types_edit)):
            chain = data.iloc[i][types_edit[j]]
            vector = chain.split(' ')
            vector = [int(x) for x in vector]
            sum_edits += sum(vector)

        for k in range(0, len(types_selection)):
            chain = data.iloc[i][types_selection[k]]
            vector = chain.split(' ')
            vector = [int(x) for x in vector]
            sum_selections += sum(vector)

        size = data.iloc[i]['size_ts']
        e = sum_edits/size
        s = sum_selections/size
        emin.append(e)
        smin.append(s)

        er = e/(e+s)
        eratio.append(er)

    data['emin'] = emin
    data['smin'] = smin
    data['eratio'] = eratio
    return data


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


def clustering_mean_shift(data_res):
    """
    Executes the mean shift model from sklearn
    """
    #print('\nFitting a mean shift model')

    ms = MeanShift()
    ms.fit(data_res)

    predictions = ms.predict(data_res)
    cluster_centers = ms.cluster_centers_

    #print('Estimated number of clusters: ', len(cluster_centers))
    return predictions, cluster_centers, 0


def clustering_affinity_propagation(data_res):
    """
    Executes sklearn's affinity propagation function with the given data frame
    """
    #print('\nFitting an affinity propagation model')
    af = AffinityPropagation()
    af.fit(data_res)

    predictions = af.predict(data_res)
    cluster_centers = af.cluster_centers_
    #print('Estimated number of clusters: ', len(cluster_centers))

    return predictions, cluster_centers
    
    
def clustering_sessions_by_proportions(data, attributes, n_clusters, users, method='kmeans'):
    """
    Perform clustering of sessions by the proportion using different methods. 
    Creates a file with the resulting centers
    """
    # prepare the dataset
    data_res = DataFrame()
    data.is_copy = False
    g = []
    for ts in attributes:
        data_res['prop_' + ts] = data['prop_' + ts]
        g.append('prop_' + ts)

    pred, cluster_centers, error = clustering_affinity_propagation(data_res) if method == 'affinity' \
                                    else clustering_mean_shift(data_res)

    n_clusters = len(cluster_centers)

    data['prediction'] = pred

    # create a dataset with the summary of clusters and predictions per cluster
    n_sessions = []
    users_by_cluster = [0] * n_clusters
    n_predictions_by_cluster = [0] * n_clusters
    c = 65
    for u in users:
        data_user = data[data['user'] == u]
        user_predictions = np.asarray(data_user['prediction'])

        # count the number of times a session was predicted in some cluster
        for i in user_predictions:
            n_predictions_by_cluster[i] += 1

        unique_predictions = set(user_predictions)
        for i in unique_predictions:
            users_by_cluster[i] += 1

        n_sessions.append(len(data_user))

        c = (c + 1) if c != 90 else 97

    centers = DataFrame(cluster_centers, columns=attributes)
    centers['n_predictions'] = n_predictions_by_cluster
    centers['n_users'] = users_by_cluster

    return cluster_centers, centers


def clustering_bootstrap(samples,repetitions, algorithm):
    """
    Generates n models and return all the resulting centers
    """
    all_centers = []
    for i in range(0, repetitions):
        # selects chunks data
        rows = random.sample(chunks.index, samples)

        chunks2 = chunks.ix[rows]
        users = chunks2['user']
        users = users.unique()

        centers, df = clustering_sessions_by_proportions(chunks2, TIME_SERIES_NAMES, 
                                                            0, users, 'meanshift')
        if len(all_centers) == 0:
            all_centers = np.array(df)
        else:
            all_centers = np.concatenate([all_centers, np.array(df)])
            
    return all_centers


def summarize_centers(all_centers, proximity_threshold, n_attributes, n_extended_attributes):
    """
    Summarizes all the detected centers taking all the close centers and getting 
    the median of the values for each attribute
    """
    indexes = range(0, len(all_centers))
    summarized_centers = []
    checked = []
    proximity = proximity_threshold
    differences = []

    for i in indexes:  # for every center found
        if i not in checked:  # first check if it was already analyzed
            center = all_centers[i][0:n_attributes]
            checked = checked + [i]
            related = [i]
            l = list(set(indexes) - set(checked))  # get the set difference

            for j in l:  # find all the centers close to the current one
                diff = np.linalg.norm(center - all_centers[j][0:n_attributes])
                differences = differences + [diff]
                if diff <= proximity:
                    related = related + [j]
                    checked = checked + [j]

            new_center = []

            for k in range(0, n_extended_attributes):  # get the median of all the close centers
                values = [all_centers[r][k] for r in related]
                new_center = new_center + [max(values)]

            new_center = new_center + [len(related)]

            # add the summarized center to to the 2d array
            if len(summarized_centers) == 0:
                summarized_centers = new_center
            else:
                summarized_centers = np.vstack([summarized_centers, new_center])

    return summarized_centers, differences
    

def pipeline(chunks, directory, chunks_file_name, chunks_centers_file_name,
             n_sample, rep, algorithm):
    """
    Main pipeline for the first phase of data mining.
    Chunks clustering.
    """
    
    # calculate the proportion of events
    chunks = calc_proportions(chunks)
    
    # creates n models and store all found clusters
    print 'Creating ' + str(rep) + ' models with bootstrap'
    all_centers = clustering_bootstrap(n_sample, rep, algorithm)
        
    # remove redundant centers, param based on quantiles
    summarized_centers, diffs = summarize_centers(all_centers, 0.4, 10, 12)
    
    summarized_centers = DataFrame(summarized_centers, 
                                   columns= TIME_SERIES_NAMES +
                                   ['n_predictions', 'n_users', 'repetitions'])

    summarized_centers = summarized_centers[summarized_centers['repetitions'] > 1]
    summarized_centers['id'] = range(0,len(summarized_centers))
    summarized_centers.set_index([range(0,len(summarized_centers))], inplace=True)
    summarized_centers.to_csv(directory + chunks_centers_file_name, index=False)
    
    
    print "Final number of clusters of chunks: " + str(len(summarized_centers))

    # get a prediction with the summarized centers
    print "Predicting labels with the new centers"
    final_model = MeanShift()
    final_model.cluster_centers_ = summarized_centers.ix[:,0:10].as_matrix()
    chunks['label'] = final_model.predict(chunks.ix[:,15:25])

    # measure the distance of the chunks to the center of the cluster
    print 'Measuring distances to the center...'
    labels = ['prop_' + x for x in TIME_SERIES_NAMES]
    distances = []
    for i in range(0,len(chunks)):
        c = chunks.ix[i]
        center = summarized_centers.ix[c['label']][TIME_SERIES_NAMES]
        c = c[labels]
        d = np.linalg.norm(np.array(c) - np.array(center))
        distances.append(d)

    chunks['distance_to_center'] = distances
    
    print 'Distribution of distance to the centers'
    for i in range(0,len(summarized_centers)):
        elements = np.array(chunks[chunks['label'] == i]['distance_to_center'])
        print 'Cluster ' + str(i) + ': ' 
        print scipy.stats.mstats.mquantiles(elements, prob=[0, 0.25, 0.50, 0.75, 1])

    chunks.to_csv(directory + chunks_file_name, index=False)
    
    
if __name__ == "__main__":
    
    print 'Clustering chunks with ABB'    
    
    chunks = pandas.read_csv(PATH_TO_ABB + 'chunks_abb.csv', index_col=None, header=0)
    #pipeline(chunks,PATH_TO_ABB,'chunks_abb.csv', 'chunks_centers_abb.csv',  2000, 100, 'meanshift')
    
    print '\n\nClustering chunks with UDC'    
    
    chunks = pandas.read_csv(PATH_TO_UDC + 'chunks_udc.csv', index_col=None, header=0)
    pipeline(chunks,PATH_TO_UDC,'chunks_udc.csv', 'chunks_centers_udc.csv', 500, 200, 'meanshift')
    