from __future__ import division

import numpy as np
import random
import scipy
from pandas import *
from sklearn.cluster import MeanShift, AffinityPropagation

PATH_TO_ABB = '/home/luis/abb/'
PATH_TO_UDC = '/home/luis/udc/'
TIME_SERIES_NAMES = ['edition', 'text_nav', 'high_nav', 'file', 'refactoring',
                     'debug', 'tools', 'control', 'testing', 'search']


def levenshtein(s1, s2):
    """
    Calculates the levenshtein distance of the two parameters
    """
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1  
            deletions = current_row[j] + 1 
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def split_in_chunks(l,n):
    """
    Splits the list 'l' into 'n' chunks of equal size
    """
    size = len(l)    
    size_chunks = size/n
    residue = size%n
    splitted = []
    i = 0
    j = 0
    while n > 0:
        r = 0
        if residue != 0:
            r = 1
            residue = residue - 1
        j = i + (size_chunks + r)
        splitted.append(l[i:j])
        n -= 1
        i = j
    return splitted
    
    
def clustering_mean_shift(data_res):
    """
    Executes the mean shift model from sklearn
    """
    ms = MeanShift()
    ms.fit(data_res)

    predictions = ms.predict(data_res)
    cluster_centers = ms.cluster_centers_

    return predictions, cluster_centers
    

def clustering_affinity_propagation(data_res):
    """
    Executes sklearn's affinity propagation function with the given data frame
    """
    af = AffinityPropagation()
    af.fit(data_res)

    predictions = af.predict(data_res)
    cluster_centers = af.cluster_centers_

    return predictions, cluster_centers
    
    
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

           # new_center = new_center + [len(related)]

            # add the summarized center to to the 2d array
            if len(summarized_centers) == 0:
                summarized_centers = new_center
            else:
                summarized_centers = np.vstack([summarized_centers, new_center])

    return summarized_centers, differences
    
    
def pipeline(chunks, sessions, chunk_centers, directory, chunk_types, column_names, 
             algorithm, splitted_sessions_name, sessions_centers_name, sessions_name):
    """
    Pipeline for the clustering of sessions
    """
    # get the label from the centers
    centers_labels = list(set(chunks_centers['label']))
    chunks_centers['label'] = chunks_centers['label'].astype('str')
    
    # add the string label to the chunks
    label_c = []
    for i in range(0,len(chunks)):
        l = chunks.iloc[i]['label']
        label_c.append(chunks_centers.iloc[l]['label'])
    chunks['label_c'] = label_c
    
    print '\nClustering sessions'
    
    # for every session get the correspondent chunks and split them into 3 
    # phases of equal size
    splitted_sessions = DataFrame(columns=column_names+('id',))
    sessions_ids = list(set(chunks['session_id']))
    
    c = 0
    for s in sessions_ids:
        session_chunks = chunks[chunks['session_id'] == s]
        if len(session_chunks) >= 3:
            splitted_ids = split_in_chunks(np.array(session_chunks['label_c']), 3)
            row = []
            for i in range(0,len(splitted_ids)):
                for j in chunk_types:
                    row.append(splitted_ids[i].tolist().count(j))
            
            total = sum(row)
            if total > 0:
                row = [x/total for x in row]
                row.append(s)
                splitted_sessions.loc[c] = row
                c = c + 1
    
    pred, centers = 0,0
    if algorithm == 'meanshift':
        pred, centers = clustering_mean_shift(splitted_sessions.iloc[:,0:len(column_names)].as_matrix())
    else:
        pred, centers = clustering_affinity_propagation(splitted_sessions.iloc[:,0:len(column_names)].as_matrix())

    # summarize the close centers  and fit a new model with the new centers
    centers2 = summarize_centers(centers, 0.3, 15, 15)[0]
    prediction_model = MeanShift()
    prediction_model.cluster_centers_ = centers2
    pred2 = prediction_model.predict(splitted_sessions.iloc[:,0:len(column_names)].as_matrix())
    
    # create a dataframe with the sessions split into 3 phases
    splitted_sessions['label'] = pred2
    centers = DataFrame(data=centers, columns=column_names)
    centers['id'] = range(0, len(centers))
    labels = []
    for i in range(0, len(sessions)):
        ss = splitted_sessions[splitted_sessions['id'] == i]
        if len(ss) == 0:
            labels.append(-1) # label with a -1 those sessions to small to split
        else:
            labels.append(ss['label'].iloc[0])
    sessions['label'] = labels
    
    splitted_sessions.to_csv(directory + splitted_sessions_name, index=False)
    sessions.to_csv(directory + sessions_name, index=False)
    centers.to_csv(directory + sessions_centers_name, index=False)
    
    
if __name__ == "__main__":
    
    print 'Clustering sessions with ABB'    
    
    chunks = pandas.read_csv(PATH_TO_ABB + 'chunks_abb.csv', index_col=None, header=0)
    sessions = pandas.read_csv(PATH_TO_ABB + 'ts_abb.csv', index_col=None, header=0)
    chunks_centers = pandas.read_csv(PATH_TO_ABB + 'chunks_centers_abb.csv', index_col=None, header=0)
    chunk_types = ['Programming', 'Debugging', 'Navigation', 'Version', 'Testing']
    column_names=('Programming_1', 'Debugging_1', 'Navigation_1', 'Version_1', 'Testing_1',
                  'Programming_2', 'Debugging_2', 'Navigation_2', 'Version_2', 'Testing_2', 
                  'Programming_3', 'Debugging_3', 'Navigation_3', 'Version_3', 'Testing_3')
    pipeline(chunks, sessions, chunks_centers, PATH_TO_ABB, chunk_types, column_names,
             'affinity', 'splitted_sessions_abb.csv', 'sessions_centers_abb.csv', 'ts_abb.csv')
    
    print '\n\nClustering sessions with UDC'    
    
    chunks = pandas.read_csv(PATH_TO_UDC + 'chunks_udc.csv', index_col=None, header=0)
    sessions = pandas.read_csv(PATH_TO_UDC + 'ts_udc.csv', index_col=None, header=0)
    chunks_centers = pandas.read_csv(PATH_TO_UDC + 'chunks_centers_udc.csv', index_col=None, header=0)
    chunk_types = ['Programming', 'Debugging', 'Version', 'Tools', 'Refactoring']
    column_names = ('Programming_1', 'Debugging_1', 'Version_1', 'Tools_1', 'Refactoring_1',
                    'Programming_2', 'Debugging_2', 'Version_2', 'Tools_2', 'Refactoring_2',
                    'Programming_3', 'Debugging_3', 'Version_3', 'Tools_3', 'Refactoring_3')
    pipeline(chunks, sessions, chunks_centers, PATH_TO_UDC, chunk_types, column_names,
             'affinity', 'splitted_sessions_udc.csv', 'sessions_centers_udc.csv', 'ts_udc.csv')
             