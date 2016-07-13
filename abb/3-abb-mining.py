from __future__ import division

import numpy as np
import random
import scipy
from pandas import *
from sklearn.cluster import KMeans, AffinityPropagation, MeanShift     

PATH_TO_RESULT_MAIN = '/home/luis/abb/'
PATH_TS_FILE = "/home/luis/abb/ts_abb.csv"  
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

            
def initialize_kmeanspp(x, k):
    """
    Initializes the centroids for the given vector of values using k-means++
    """
    random.seed(29)
    c = [x[0]]
    for k in range(1, k):
        d = scipy.array([min([scipy.inner(j-i,j-i) for j in c]) for i in x])
        probs = d/d.sum()
        cumprobs = probs.cumsum()
        r = random.random()
        for j,p in enumerate(cumprobs):
            if r < p:
                i = j
                break
        c.append(x[i])
    return c


def clustering_kmeans(data_res, n_clusters, attributes):
    """
    Executes sklearn k-means clustering function with the given dataframe
    """
    n_k = n_clusters

    # initialize the centroids with k-means++
    initial = []
    for i in attributes:
        x = np.array(data_res[i])
        initialized_centroids = np.array(initialize_kmeanspp(x, n_k))
        if len(initial) == 0:
            initial = initialized_centroids
        else:
            initial = np.vstack((initial,initialized_centroids))
    initial = np.rot90(initial)

    print('\nFitting a k-means model')
    print('Number of clusters: ' + str(n_k))
    km = KMeans(n_clusters=n_k, init=initial, n_init=1)
    km.fit(data_res)
    inertia = km.inertia_
    print('Inertia: ', inertia)

    predictions = km.predict(data_res)
    cluster_centers = km.cluster_centers_

    return predictions, cluster_centers, inertia


def clustering_affinity_propagation(data_res):
    """
    Executes sklearn's affinity propagation function with the given data frame
    """
    print('\nFitting an affinity propagation model')
    af = AffinityPropagation()
    af.fit(data_res)

    predictions = af.predict(data_res)
    cluster_centers = af.cluster_centers_
    print('Estimated number of clusters: ', len(cluster_centers))

    return predictions, cluster_centers, 0


def clustering_mean_shift(data_res):
    """
    Executes the mean shift model from sklearn
    """
    print('\nFitting a mean shift model')

    ms = MeanShift()
    ms.fit(data_res)

    predictions = ms.predict(data_res)
    cluster_centers = ms.cluster_centers_

    print('Estimated number of clusters: ', len(cluster_centers))
    return predictions, cluster_centers, 0


def clustering_sessions_by_proportions(data, attributes, n_clusters, users, file_name, method='kmeans'):
    """
    Perform clustering of sessions by the proportion using different methods. Creates a file with the resulting
    centers
    """
    # prepare the dataset
    data_res = DataFrame()
    data.is_copy = False
    g = []
    for ts in attributes:
        data_res['prop_' + ts] = data['prop_' + ts]
        g.append('prop_' + ts)

    pred, cluster_centers, error = clustering_kmeans(data_res, n_clusters, g) if method == 'kmeans'\
        else clustering_affinity_propagation(data_res) if method == 'affinity' else clustering_mean_shift(data_res)

    n_clusters = len(cluster_centers)

    data['prediction'] = pred

    # create a dataset with the summary of clusters and predictions per cluster
    n_sessions = []
    users_by_cluster = [0] * n_clusters
    n_predictions_by_cluster = [0] * n_clusters
    user_list_by_cluster = [''] * n_clusters
    c = 65
    for u in users:
        data_user = data[data['user'] == u]
        user_predictions = np.asarray(data_user['prediction'])

        # count the number of times a session was predicted in some cluster
        for i in user_predictions:
            n_predictions_by_cluster[i] += 1
            user_list_by_cluster[i] += chr(c)

        unique_predictions = set(user_predictions)
        for i in unique_predictions:
            users_by_cluster[i] += 1

        n_sessions.append(len(data_user))

        c = (c + 1) if c != 90 else 97

    # compress the users list per cluster
    for i in range(0, len(user_list_by_cluster)):
        sub_list = user_list_by_cluster[i]
        previous = ''
        count = 0
        result = ''
        for j in range(0, len(sub_list)):
            current = sub_list[j]
            if previous != current:
                if count > 0:
                    result += (previous + str(count) + ',')
                previous = current
                count = 1
            else:
                count += 1
        if count > 0:
            result += (previous + str(count))
        user_list_by_cluster[i] = result

    centers = DataFrame(cluster_centers, columns=attributes)
    centers['n_predictions'] = n_predictions_by_cluster
    centers['n_users'] = users_by_cluster
    centers['users'] = user_list_by_cluster

    #centers.to_csv(PATH_TO_RESULT_MAIN + file_name)

    return cluster_centers, n_predictions_by_cluster, centers


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


if __name__ == "__main__":
    # print '\nClustering sessions'
    #
    # # load sessions data
    # sessions = pandas.read_csv(PATH_TS_FILE, index_col=None, header=0)
    # sessions = calc_proportions(sessions)
    # sessions.to_csv(PATH_TS_FILE, index=False)
    #
    # # select users with enough information
    # data_aggregated = DataFrame({'count': sessions.groupby(['user']).size()}).reset_index()
    # list_users = np.asarray(data_aggregated[data_aggregated['count'] >= 10]['user'])
    #
    # # cluster with bootstrap
    # all_centers = []
    # samples = 400
    # repetitions = 100
    # for i in range(0, repetitions):
    #     # selects a subset of the data
    #     rows = random.sample(sessions.index, samples)
    #     sessions2 = sessions.ix[rows]
    #     users = sessions2['user']
    #     users = users.unique()
    #
    #     # clustering sessions by proportions
    #     centers, n_predictions, df = clustering_sessions_by_proportions(sessions2, TIME_SERIES_NAMES,
    #                                                                     0, users, 'sessions_meanshift_centers.csv',
    #                                                                     'meanshift')
    #     if len(all_centers) == 0:
    #         all_centers = np.array(df)
    #     else:
    #         all_centers = np.concatenate([all_centers, np.array(df)])
    #
    # # remove redundant centers
    # summarized_centers, diffs = summarize_centers(all_centers, 0.4, 10, 12)
    # summarized_centers = DataFrame(summarized_centers,
    #                                columns= TIME_SERIES_NAMES +
    #                                ['n_predictions', 'n_users', 'repetitions'])
    # summarized_centers = summarized_centers[summarized_centers['repetitions'] > 1]
    # summarized_centers.to_csv(PATH_TO_RESULT_MAIN + 'sessions_centers.csv')
    #
    # # get a prediction with the summarized centers
    # final_model = MeanShift()
    # final_model.cluster_centers_ = summarized_centers.ix[:,0:10].as_matrix()
    # sessions['label'] = final_model.predict(sessions.loc[:,[str('prop_' + i) for i in TIME_SERIES_NAMES]])
    # sessions.to_csv(PATH_TO_RESULT_MAIN + 'ts_abb.csv', index=False)
    
    print '\nClustering chunks'
    
    # load chunks data
    chunks = pandas.read_csv(PATH_TO_RESULT_MAIN + 'decomposed_ts.csv', 
                             index_col=None, header=0)
    chunks = calc_proportions(chunks)
    chunks.to_csv(PATH_TO_RESULT_MAIN + 'decomposed_ts.csv', index=False)

    # creates n models and store all found clusters
    all_centers = []
    samples = 3000
    repetitions = 50
    for i in range(0, repetitions):
        # selects chunks data
        rows = random.sample(chunks.index, samples)

        chunks2 = chunks.ix[rows]
        users = chunks2['user']
        users = users.unique()

        centers, n_predictions, df = clustering_sessions_by_proportions(chunks2, TIME_SERIES_NAMES, 
                                                                        0, users, '5min_chunks_centers.csv',
                                                                        'meanshift')
        if len(all_centers) == 0:
            all_centers = np.array(df)
        else:
            all_centers = np.concatenate([all_centers, np.array(df)])
        
    # remove redundant centers
    summarized_centers, diffs = summarize_centers(all_centers, 0.4, 10, 12)
    q = scipy.stats.mstats.mquantiles(diffs, prob=[0, 0.25, 0.50, 0.75, 1])
    print q
    
    summarized_centers = DataFrame(summarized_centers, 
                                   columns= TIME_SERIES_NAMES +
                                   ['n_predictions', 'n_users', 'repetitions'])

    summarized_centers = summarized_centers[summarized_centers['repetitions'] > 1]
    summarized_centers.to_csv(PATH_TO_RESULT_MAIN + 'chunks_centers2.csv')
    
    print "Final num of clusters of chunks: " + str(len(summarized_centers))

    # get a prediction with the summarized centers
    final_model = MeanShift()
    final_model.cluster_centers_ = summarized_centers.ix[:,0:10].as_matrix()
    chunks['label'] = final_model.predict(chunks.ix[:,14:24])
    chunks.to_csv(PATH_TO_RESULT_MAIN + 'decomposed_ts2.csv', index=False)

