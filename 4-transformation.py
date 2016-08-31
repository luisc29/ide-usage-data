from __future__ import division
from pandas import *
from datetime import datetime
from time import mktime
import glob
import time
import math
import os
from multiprocessing import Pool
import multiprocessing
import numpy as np


SIZE_INT = 180  # size threshold for the interruptions
SPACE_BETWEEN_INT = 14400  # threshold for the sessions
BREAK_POINT = 2700  # size of the interval to split the session in two
PATH_TO_UDC = '/home/luis/udc/'
PATH_TO_ABB = '/home/luis/abb/'


def load_data(path):
    """
    Loads the events partitioned in several files into
    one dataset
    """
    filenames = glob.glob(path + "/*")
    
    events = DataFrame()
    data = []
    
    for f in filenames:
        data.append(pandas.read_csv(f, index_col=None, header=0))
    
    events = pandas.concat(data)
    return events
    
    
def store_grouped_data(data,path):
    """
    Stores the data grouped by user
    """
    i = 0
    for name, group in data:
        l = len(group)
        print name, ", ", l
        if l > 999:
            group.to_csv(path + "//clean.events"+ str(i), index=False)
        i += 1


def get_minute(time):
    """
    Calculates a unique identifier for the minute of the time given as
    parameter
    """
    m = time[4] + (time[3]*60) + (time[2]*60*24) * time[1] * time[0]
    return m
    
    
def preprocess_events(events):
    """
    Adds lacking information before transforming the data to sessions, like 
    an identifier for the minute, a label for the interruptions and the sessions
    """
    events = events[events['type'] != 'system']
    events.is_copy = False
    
    # set the time interval between events
    t = np.array(events['seconds'])    
    t_plus_1 = np.append(t[1:(len(t))],t[len(t)-1])
    t = t_plus_1 - t
    events['interval'] = t
    
    # Create an identifier for the minute of the event, usefull when creating
    # the sessions
    dt = [time.strptime(d, '%Y-%m-%d %H:%M:%S') for d in events['datetime']]
    events['minute'] = [get_minute(d) for d in dt]
    
    # label interruptions and sessions
    interruptions = []
    sessions = []
    intervals = t
    s_id = 0
    for i in range(0,len(events)):
        sessions.append(s_id)
        if intervals[i] >= SPACE_BETWEEN_INT:
            s_id += 1
            interruptions.append(False)
            continue
            
        if intervals[i] >= SIZE_INT:
            interruptions.append(True)
        else:
            interruptions.append(False)
            
    events['is_interruption'] = interruptions
    events['session_id'] = sessions
    
    return events


def break_points(inte, minutes):
    """
    Finds breaking points of the session where there are very prolonged interruptions, like lunch time
    """
    inte = np.asarray(inte)
    minutes = np.asarray(minutes)
    n = len(inte)
    breaks = []
    last_observed_min = 0

    # we consider sessions of 30 productive minutes, so we cannot split a session lesser than 60 minutes
    if n > 60:
        c = 0
        for i in range(0,(n)):
            if minutes[i] != last_observed_min:
                last_observed_min = minutes[i]
                c += 1
                
            if (inte[i] >= BREAK_POINT and c > 30) and len(inte[i:]) > 30:
                breaks.append(i)
                c = 0
            
    return breaks


def transform_to_sessions(events, uid):
    """
    Transforms the data of every user to sessions
    """
    
    class Sessions:
        values = {
            'id': [], 'size_ts': [],
            'interruptions': [], 'n_inte': [], 'n_events': [], 'start_time': [], 'end_time': [],
            'user': [], 'edition': [],  'text_nav': [],  'high_nav': [], 'file': [], 'refactoring': [],
            'clean_build': [],  'debug': [],  'tools': [], 'control': [], 'testing': [], 'search': []

        }

        lists = {
            'l_interruptions': [], 'l_edition': [], 'l_text_nav': [], 'l_high_nav': [], 'l_file': [],
            'l_refactoring': [], 'l_clean_build': [], 'l_debug': [], 'l_tools': [], 'l_control': [],
            'l_testing': [], 'l_search': [], 'size_ts': [], 'n_inte': [], 'id': []
        }

        def __init__(self):
            pass

        def create_dataframe(self):
            """
            Creates a dataframe with the sessions of the user
            """
            sessions = pandas.DataFrame().from_dict(self.values)
            sessions_lists = pandas.DataFrame().from_dict(self.lists)
            return sessions, sessions_lists
            
    so = Sessions()

    s = set(events['session_id'])

    count = 0  # count of sessions

    # process all the sessions of the user
    for i in s:
        user_sessions = events[events['session_id'] == i]
        #user_sessions.to_csv(PATH_SESSIONS + '/' + str(uid) + '-' + str(count) + '.csv', index=False)

        split_session = [user_sessions]

        # if breaking points are found, the session splits into subsessions
        bp = break_points(user_sessions['interval'], user_sessions['minute'])
        if len(bp) > 0:
            bp.append(len(user_sessions))
            split_session = []
            index = 0
            for k in range(0,len(bp)):
                sub_session = user_sessions.iloc[index:(bp[k]+1)]
                split_session.append(sub_session)
                index = bp[k]+1

        count += 1

        for session in split_session:

            minutes = np.unique(np.array(session['minute']))
            l_edits = []
            l_text_nav = []
            l_high_nav = []
            l_refactoring = []
            l_debug = []
            l_file = []
            l_build = []
            l_tools = []
            l_control = []
            l_testing = []
            l_search = []
            l_inte = []
            dur = len(minutes)
            ni = 0

            for m in minutes:
                # for every minute of the session, count the number of edition and
                # selection events and the duration of the interruptions (among other types of events)
                subset = session[session['minute'] == m]
                l_edits.append(len(subset[subset['detailed_type'] == 'edit-text']))
                l_high_nav.append(len(subset[subset['detailed_type'] == 'high-nav']))
                l_text_nav.append(len(subset[subset['detailed_type'] == 'text-nav']))
                l_refactoring.append(len(subset[subset['detailed_type'] == 'refactoring']))
                l_debug.append(len(subset[subset['detailed_type'] == 'debug']))
                l_file.append(len(subset[subset['detailed_type'] == 'file']))
                l_build.append(len(subset[subset['detailed_type'] == 'clean-build']))
                l_tools.append(len(subset[subset['detailed_type'] == 'tools']))
                l_control.append(len(subset[subset['detailed_type'] == 'control']))
                l_testing.append(len(subset[subset['detailed_type'] == 'testing']))
                l_search.append(len(subset[subset['detailed_type'] == 'search']))

                if subset.iloc[len(subset)-1]['is_interruption']:
                    l_inte.append(subset.iloc[len(subset)-1]['interval']//60)
                    ni += 1
                else:
                    l_inte.append(0)

            so.values['id'].append(str(uid) + '-' + str(count))
            so.lists['id'].append(str(uid) + '-' + str(count))
            # print (str(uid) + '-' + str(count))
            so.values['size_ts'].append(dur)
            so.lists['size_ts'].append(dur)

            # convert the lists to string
            str_edits = ' '.join(str(e) for e in l_edits)
            str_high_nav = ' '.join(str(e) for e in l_high_nav)
            str_text_nav = ' '.join(str(e) for e in l_text_nav)
            str_refactoring = ' '.join(str(e) for e in l_refactoring)
            str_debug = ' '.join(str(e) for e in l_debug)
            str_file = ' '.join(str(e) for e in l_file)
            str_build = ' '.join(str(e) for e in l_build)
            str_tools = ' '.join(str(e) for e in l_tools)
            str_control = ' '.join(str(e) for e in l_control)
            str_testing = ' '.join(str(e) for e in l_testing)
            str_search = ' '.join(str(e) for e in l_search)
            str_inte = ' '.join(str(e) for e in l_inte)

            so.values['edition'].append(str_edits)
            so.values['high_nav'].append(str_high_nav)
            so.values['text_nav'].append(str_text_nav)
            so.values['refactoring'].append(str_refactoring)
            so.values['debug'].append(str_debug)
            so.values['file'].append(str_file)
            so.values['clean_build'].append(str_build)
            so.values['tools'].append(str_tools)
            so.values['control'].append(str_control)
            so.values['testing'].append(str_testing)
            so.values['search'].append(str_search)
            so.values['interruptions'].append(str_inte)

            so.lists['l_interruptions'].append(l_inte)
            so.lists['l_edition'].append(l_edits)
            so.lists['l_high_nav'].append(l_high_nav)
            so.lists['l_text_nav'].append(l_text_nav)
            so.lists['l_refactoring'].append(l_refactoring)
            so.lists['l_debug'].append(l_debug)
            so.lists['l_file'].append(l_file)
            so.lists['l_clean_build'].append(l_build)
            so.lists['l_tools'].append(l_tools)
            so.lists['l_control'].append(l_control)
            so.lists['l_testing'].append(l_testing)
            so.lists['l_search'].append(l_search)
            so.lists['n_inte'].append(ni)
            
            so.values['n_inte'].append(ni)
            so.values['start_time'].append(session.iloc[0]['datetime'])
            so.values['end_time'].append(session.iloc[len(session) - 1]['datetime'])
            so.values['user'].append(session.iloc[0][0])
            so.values['n_events'].append(len(session[session['detailed_type'] != ' ']))

    result, lists = so.create_dataframe()
    return result, lists
    

def chunks(l, n):
    n = max(1, n)
    return [l[i:i + n] for i in range(0, len(l), n)]


def split_segment(start, end, size):
    length = end - start
    if length >= (size*2):
        s1 = split_segment(start, start+(length//2), size)
        s2 = split_segment(start+(length//2)+1, end, size)
        return s1 + s2
    else:
        return [(start,end)]
    
        
def decompose_sessions(sessions, lists,  time_frame_min):
    """
    Decomposes sessions into smaller chunks of time, returning only chunks of productive time (ignores interruptions)
    """
    interruptions = np.asarray(lists['l_interruptions'])
    col_names = ['l_edition', 'l_text_nav', 'l_high_nav', 'l_file', 'l_refactoring', 'l_clean_build', 'l_debug',
                 'l_tools', 'l_control', 'l_testing', 'l_search']
    decomposed_sessions = DataFrame()

    # iterate over the interruptions time series to identify productive segments
    print '# sessions to decompose: ' + str(len(interruptions))
    for i in range(0, len(interruptions)):
        print 'decomposing session #' + str(i)
        inte = interruptions[i]
        session = sessions.iloc[i]
        session_lists = lists.iloc[i]
        start = 0
        count = 0
        segments = []

        # identify segments with at least 10 minutes of productive time and store the indexes
        # also store the segments with interruptions
        for j in range(0, len(inte)):
            if inte[j] == 0:
                count += 1
            else:
                if count >= time_frame_min:
                    segments = segments + split_segment(start, j-1, time_frame_min)                    

                start = j + 1
                count = 0

        # for every segment, get the indexes and decompose all the time series and create a new dataframe with them
        for s in segments:
            row = DataFrame()

            n_events = 0

            for col in col_names:
                sub_list = np.asarray(session_lists[col])
                sub_list = sub_list[s[0]:s[1]]
                new_name = '_'.join(col.split('_')[1:])
                row[new_name] = [' '.join(str(s) for s in sub_list)]
                n_events += sum(sub_list)
                
            row['user'] = [session['user']]
            row['id'] = [session['id']]
            row['session_id'] = [session['session_id']]
            row['n_events'] = [n_events]

            if len(decomposed_sessions) == 0:
                decomposed_sessions = row
            else:
                decomposed_sessions = decomposed_sessions.append(row)

    return decomposed_sessions
    
    
def pipe_trans_events(file_path, files):
    """
    Applies transformation to the data on the files. Returns an object with the sessions
    """
    res = DataFrame()
    res_lists = DataFrame()
    
    for i in range(0,len(files)):
        events = DataFrame.from_csv(file_path + '//' + files[i], index_col=False)
        print 'processing file: ' + files[i]
        events = preprocess_events(events)
        sessions, lists = transform_to_sessions(events, i)
        if len(res) == 0:
            res = sessions
            res_lists = lists
        else:
            res = res.append(sessions, ignore_index=True)
            res_lists = res_lists.append(lists, ignore_index=True)
    return res, res_lists
    
    
def pipeline(events, directory, sessions_file_name, chunks_file_name):
    """
    Main pipeline for the transformation of the ABB and UDC datasets
    """
    start = time.time()
    
    # sort it by user and datetime
    events = events.sort(['user', 'datetime'], ascending=[1, 1])
    
    # group by user
    events = events.groupby(["user"])
    
    # Create a file per user
    store_grouped_data(events, directory + 'users')
    
    cores = multiprocessing.cpu_count()
    
    # Split the files into n groups
    files = os.listdir(directory + 'users')
    files = np.array_split(files, cores)
    
    # Transform the data to sessions in parallel
    pool = Pool()
    r = []
    res = DataFrame()
    lists = DataFrame()
    
    for i in range(0, cores):
        r1 = pool.apply_async(pipe_trans_events, [directory + 'users', files[i]])
        r.append(r1)

    for i in range(0, cores):
        r1, r2 = r[i].get()
        if len(res) == 0:
            res = r1
            lists = r2
        else:
            res = res.append(r1)
            lists = lists.append(r2)
    
    pool.close()
    pool.terminate()
    end = time.time()
    print 'Parallel execution finished'

    # keep sessions with at least 30 minutes of productive time and remove
    # sessions with high proportion of interruptions
    res['prop_inte'] = res['n_inte']/res['size_ts']
    lists['prop_inte'] = lists['n_inte']/lists['size_ts']

    res = res[res['size_ts'] >= 30]    
    res = res[res['prop_inte'] < 0.5]
    lists = lists[lists['size_ts'] >= 30]
    lists = lists[lists['prop_inte'] < 0.5]

    res['session_id'] = range(0,len(res))

    res.to_csv(directory + '/' + sessions_file_name, index=False)

    # decompose the sessions into chunks of productive time of at least n minutes
    decomposed_sessions = decompose_sessions(res, lists, 4)
    decomposed_sessions.to_csv(directory + '/' + chunks_file_name, index=False)

    end = time.time()
    print end-start
    

if __name__ == '__main__':
    
    print 'Starting ABB data transformation'
    
    #log = load_data(PATH_TO_ABB + 'preproc')
    #pipeline(log, PATH_TO_ABB, 'abb.sessions.csv', 'abb.chunks.csv')
    
    print '\n\nStarting UDC data transformation'
    
    log = DataFrame.from_csv(PATH_TO_UDC + 'clean.dataC.csv', index_col=False)
    pipeline(log, PATH_TO_UDC, 'udc.sessions.csv', 'udc.chunks.csv')
    
    print 'Transformation finished'