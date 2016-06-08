from __future__ import division

import numpy as np
import random
import scipy
from pandas import *
from sklearn.cluster import KMeans
from sklearn.cluster import AffinityPropagation
from collections import Counter
from sklearn.ensemble import ExtraTreesClassifier


PATH_TO_RESULT_MAIN = "/home/luis/abb/"
PATH_TS_FILE = "/home/luis/abb/ts_abb.csv"  
TIME_SERIES_NAMES = ['edition', 'text_nav', 'high_nav', 'file', 'refactoring',
                     'debug', 'clean_build', 'tools', 'control', 'testing', 'search']

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
    '''
    Initializes the centroids for the given vector of values
    '''
    random.seed(29)
    c = [x[0]]
    for k in range(1, k):
        d = scipy.array([min([scipy.inner(c-x,c-x) for c in c]) for x in x])
        probs = d/d.sum()
        cumprobs = probs.cumsum()
        r = random.random()
        for j,p in enumerate(cumprobs):
            if r < p:
                i = j
                break
        c.append(x[i])
    return c


def clustering_by_proportions_kmeans(data_res, data, users):
    """
    Finds clusters by the proportion of events
    """
    n_k = len(users)

    # fitting the model
    print('Fitting a k-means model')
    print(' Number of clusters: ' + str(n_k))

    # initialize the centroids with kmeans++
    initial = []
    for i in TIME_SERIES_NAMES:
        x = np.array(data_res['prop_' + i])
        initialized_centroids = np.array(initialize_kmeanspp(x, n_k))
        if len(initial) == 0:
            initial = initialized_centroids
        else:
            initial = np.vstack((initial,initialized_centroids))
    initial = np.rot90(initial)

    km = KMeans(n_clusters=n_k, init=initial, n_init=1)
    km.fit(data_res)
    print('Inertia:', km.inertia_)
    # get the cluster centers
    centers = DataFrame(km.cluster_centers_, columns=TIME_SERIES_NAMES)

    # predict the cluster for every session
    predictions = km.predict(data_res)
    data['prediction'] = predictions

    common_prediction1 = []
    common_prediction2 = []
    common_prediction3 = []
    errors =[]
    n_sessions = []
    users_by_cluster = [0, 0, 0,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    n_predictions_by_cluster = [0, 0, 0,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    user_list_by_cluster = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
    c = 65
    for u in users:
        data_user = data[data['user']==u]
        user_predictions = np.asarray(data_user['prediction'])

        # counts the number of times a session was predicted in some cluster
        for i in user_predictions:
            n_predictions_by_cluster[i] += 1

        unique_predictions = set(user_predictions)
        for i in unique_predictions:
            users_by_cluster[i] += 1
            user_list_by_cluster[i] += chr(c)

        # get the top 3 most common prediction per user
        most_common_value = Counter(user_predictions).most_common(3)
        l_common = len(most_common_value)
        user_pred1 = most_common_value[0][0]
        user_pred2 = -1 if l_common < 2 else most_common_value[1][0]
        user_pred3 = -1 if l_common < 3 else most_common_value[2][0]

        # calculate the error using the top 1 prediction
        error = most_common_value[0][1]/len(data_user)
        errors.append(error)
        common_prediction1.append(user_pred1)
        common_prediction2.append(user_pred2)
        common_prediction3.append(user_pred3)
        n_sessions.append(len(data_user))

        c += 1

    centers['n_predictions'] = n_predictions_by_cluster
    centers['n_users'] = users_by_cluster
    centers['users'] = user_list_by_cluster

    # calculating prediction accuracy
    prediction_accuracy = DataFrame()
    prediction_accuracy['user'] = users
    prediction_accuracy['prediction_1'] = common_prediction1
    prediction_accuracy['prediction_2'] = common_prediction2
    prediction_accuracy['prediction_3'] = common_prediction3
    prediction_accuracy['error'] = errors
    prediction_accuracy['n_sessions'] = n_sessions

    centers.to_csv(PATH_TO_RESULT_MAIN + 'clustering_prop_centers.csv')
    prediction_accuracy.to_csv(PATH_TO_RESULT_MAIN + 'clustering_prop_accuracy.csv')

    return data


def clustering_by_proportions_affinity(data_res, data, users):
    af = AffinityPropagation()
    af.fit(data_res)
    centers_locations = af.cluster_centers_
    predictions = af.predict(data_res)
    data['prediction'] = predictions
    centers = DataFrame(centers_locations, columns=TIME_SERIES_NAMES)

    n_sessions = []
    users_by_cluster = [0]*len(centers_locations)
    n_predictions_by_cluster = [0]*len(centers_locations)
    user_list_by_cluster = ['']*len(centers_locations)
    c = 65
    for u in users:
        data_user = data[data['user'] == u]
        user_predictions = np.asarray(data_user['prediction'])

        # counts the number of times a session was predicted in some cluster
        for i in user_predictions:
            n_predictions_by_cluster[i] += 1

        unique_predictions = set(user_predictions)
        for i in unique_predictions:
            users_by_cluster[i] += 1
            user_list_by_cluster[i] += chr(c)

        # calculate the error using the top 1 prediction
        n_sessions.append(len(data_user))

        c += 1

    centers['n_predictions'] = n_predictions_by_cluster
    centers['n_users'] = users_by_cluster
    centers['users'] = user_list_by_cluster

    centers.to_csv(PATH_TO_RESULT_MAIN + 'af_clusters.csv')


def clustering(data):
    """
    Performs clustering of sessions. Prepares the data-
    """
    original = data
    # remove data from users with little information
    data_aggregated = DataFrame({'count':data.groupby(["user"]).size()}).reset_index()
    list_users = np.asarray(data_aggregated[data_aggregated['count'] >= 3]['user'])
    data = data[data['user'].isin(list_users)]

    # prepare the dataset
    data_res = DataFrame()
    for ts in TIME_SERIES_NAMES:
        data_res['prop_' + ts] = data['prop_' + ts]

    # feature selection
    model = ExtraTreesClassifier()
    model.fit(data_res, data['user'])
    print('Feature importances')
    feature_importances = DataFrame()
    feature_importances['feature'] = TIME_SERIES_NAMES
    feature_importances['importance'] = model.feature_importances_
    print feature_importances

    # implement clustering
    print('\n\n     Clustering with k-means')
    users = data['user']
    users = users.unique()
    #clustering_by_proportions_kmeans(data_res, data, users)
    print('\n\n     Clustering with affinity propagation')
    clustering_by_proportions_affinity(data_res, data, users)


def calc_metrics(data):
    nrows = len(data)
    types_edit = ["edition", "refactoring", "text_nav"]
    types_selection = ["high_nav", "search", "debug"]
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

        size = data.iloc[i]["size_ts"]
        e = sum_edits/size
        s = sum_selections/size
        emin.append(e)
        smin.append(s)

        er = e/(e+s)
        eratio.append(er)

    data["emin"] = emin
    data["smin"] = smin
    data["eratio"] = eratio
    return data


if __name__ == "__main__":
    sessions = pandas.read_csv(PATH_TS_FILE, index_col=None, header=0)
    sessions = calc_proportions(sessions)
    sessions = calc_metrics(sessions)

    sessions = clustering(sessions)
