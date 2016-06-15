from __future__ import division

import numpy as np
import random
import scipy
from pandas import *
from sklearn.cluster import KMeans, AffinityPropagation, DBSCAN, MeanShift

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

    pred, centers, error = clustering_kmeans(data_res, n_clusters, g) if method == 'kmeans'\
        else clustering_affinity_propagation(data_res) if method == 'affinity' else clustering_mean_shift(data_res)

    n_clusters = len(centers)

    data['prediction'] = pred

    # creates a dataset with the summary of clusters and predictions per cluster
    n_sessions = []
    users_by_cluster = [0] * n_clusters
    n_predictions_by_cluster = [0] * n_clusters
    user_list_by_cluster = [''] * n_clusters
    c = 65
    for u in users:
        data_user = data[data['user'] == u]
        user_predictions = np.asarray(data_user['prediction'])

        # counts the number of times a session was predicted in some cluster
        for i in user_predictions:
            n_predictions_by_cluster[i] += 1
            user_list_by_cluster[i] += chr(c)

        unique_predictions = set(user_predictions)
        for i in unique_predictions:
            users_by_cluster[i] += 1

        n_sessions.append(len(data_user))

        c += 1

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

    centers = DataFrame(centers, columns=attributes)
    centers['n_predictions'] = n_predictions_by_cluster
    centers['n_users'] = users_by_cluster
    centers['users'] = user_list_by_cluster

    centers.to_csv(PATH_TO_RESULT_MAIN + file_name)


if __name__ == "__main__":

    # load sessions data
    sessions = pandas.read_csv(PATH_TS_FILE, index_col=None, header=0)
    sessions = calc_proportions(sessions)
    sessions = calc_metrics(sessions)

    # remove data from users with little information
    data_aggregated = DataFrame({'count': sessions.groupby(['user']).size()}).reset_index()
    list_users = np.asarray(data_aggregated[data_aggregated['count'] >= 3]['user'])
    data_res = sessions[sessions['user'].isin(list_users)]
    users = data_res['user']
    users = users.unique()

    print('\nClustering sessions')
    # clustering sessions by proportions
    # kmeans
    clustering_sessions_by_proportions(data_res, TIME_SERIES_NAMES, 18, users, 'sessions_kmeans_centers.csv', 'kmeans')
    # affinity propagation
    clustering_sessions_by_proportions(data_res, TIME_SERIES_NAMES, 0, users, 'sessions_affinity_centers.csv', 'affinity')
    # meanshift
    clustering_sessions_by_proportions(data_res, TIME_SERIES_NAMES, 0, users, 'sessions_meanshift_centers.csv', 'meanshift')

    # load chunks data
    chunks = pandas.read_csv(PATH_TO_RESULT_MAIN + 'decomposed_ts.csv', index_col=None, header=0)
    chunks = calc_proportions(chunks)

    users = chunks['user']
    users = users.unique()

    print('\nClustering proportions')
    # clustering chunks by proportions
    # kmeans
    clustering_sessions_by_proportions(chunks, TIME_SERIES_NAMES, 18, users, 'chunks_kmeans_centers.csv', 'kmeans' )
    # affinity propagation
    clustering_sessions_by_proportions(chunks, TIME_SERIES_NAMES, 0, users, 'chunks_affinity_centers.csv', 'affinity')
    # meanshift
    clustering_sessions_by_proportions(chunks, TIME_SERIES_NAMES, 0, users, 'chunks_meanshift_centers.csv', 'meanshift')
