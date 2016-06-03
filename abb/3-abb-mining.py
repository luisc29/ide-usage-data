from __future__ import division

import matplotlib as mp
import matplotlib.pyplot as plt
import numpy

from pandas import *
from sklearn.cluster import KMeans
from collections import Counter
from sklearn import metrics
from sklearn.ensemble import ExtraTreesClassifier


PATH_TO_RESULT_MAIN = "/home/luis/abb/"
PATH_TS_FILE = "/home/luis/abb/ts_abb.csv"  
TIME_SERIES_NAMES = ['edition', 'text_nav', 'high_nav', 'file', 'refactoring',
                     'clean_build', 'debug', 'tools', 'control', 'testing', 'search']
#TIME_SERIES_NAMES = ['clean_build', 'debug', 'tools', 'control', 'testing', 'search']


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
            

def clustering_by_proportions(data):
    """
    Finds clusters by the proportion of events
    """
    data_res = DataFrame()

    users = data['user'].unique()
    n_k = len(users)

    # prepare the dataset
    for ts in TIME_SERIES_NAMES:
        data_res['prop_' + ts] = data['prop_' + ts]


    # feature selection
    print('Feature selection')
    model = ExtraTreesClassifier()
    model.fit(data_res, data['user'])
    print('Feature importances')
    feature_importances = DataFrame()
    feature_importances['feature'] = TIME_SERIES_NAMES
    feature_importances['importance'] = model.feature_importances_
    print feature_importances

    # fitting the model
    print('Fitting a k-means model')
    print(' Number of clusters: ' + str(n_k))
    km = KMeans(n_clusters=n_k)
    km.fit(data_res)

    print('Predicting cluster for every session')
    predictions = km.predict(data_res)
    data['prediction'] = predictions

    # calculating error
    print('Calculating error')
    errors = []
    common_prediction = []
    n_sessions = []
    for u in users:
        data_user = data[data['user']==u]
        user_predictions = np.asarray(data_user['prediction'])
        most_common_value = Counter(user_predictions).most_common(1)
        user_pred = most_common_value[0][0]
        error = most_common_value[0][1]/len(data_user)
        errors.append(error)
        common_prediction.append(user_pred)
        n_sessions.append(len(data_user))

    error_prediction = DataFrame()
    error_prediction['user'] = users
    error_prediction['common_prediction'] = common_prediction
    error_prediction['error'] = errors
    error_prediction['n_sessions'] = n_sessions
    print error_prediction
    print('average error: '+ str(np.mean(errors)))
    return data


def clustering(data):
    """
    Performea clustering of sessions
    """

    # remove data from users with little information
    data_aggregated = DataFrame({'count':data.groupby(["user"]).size()}).reset_index()
    list_users = np.asarray(data_aggregated[data_aggregated['count'] >= 5]['user'])
    data = data[data['user'].isin(list_users)]

    # implement clustering
    clustering_by_proportions(data)


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

    sessions = clustering(sessions)
    #sessions.to_csv(PATH_TO_RESULT_MAIN + 'after_prop.csv', index=False)
    
    #sessions = calc_metrics(sessions)

    #plot_productivity(sessions)
