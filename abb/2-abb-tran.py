from __future__ import division
import glob
import time
from pandas import *
import os
import numpy as np

SIZE_INT = 180  # size threshold for the interruptions
SPACE_BETWEEN_INT = 28800  # threshold for the sessions
PATH_PREPROC = "//home//luis//abb//preproc"  # path to the processed data
PATH_GROUPED_DATA = "//home//luis//abb//users"  # where to store the grouped data
PATH_TS_RESULT = "/home/luis/abb/ts_abb.csv"  # where to store the time series file
PATH_SESSIONS = "/home/luis/abb/sessions"  # where to store a file per session
BREAK_POINT = 2700  # size of the interval to split the session in two


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
    events = events[events["type"] != "system"]
    
    #set the time interval between events
    t = np.array(events["seconds"])    
    t_plus_1 = np.append(t[1:(len(t))],t[len(t)-1])
    t = t_plus_1 - t
    events["interval"] = t
    
    # Create an identifier for the minute of the event, usefull when creating
    # the sessions
    dt = [time.strptime(d,'%Y-%m-%d %H:%M:%S') for d in events["datetime"]]
    events["minute"] = [get_minute(d) for d in dt]
    
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
            
    events["is_interruption"] = interruptions
    events["session_id"] = sessions
    
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
    
        def __init__(self):
            pass


        def create_dataframe(self):
            """
            Creates a dataframe with the sessions of the user
            """
            sessions = pandas.DataFrame().from_dict(self.values)
            return sessions
            
    so = Sessions()

    s = set(events["session_id"])

    count = 0  # count of sessions

    # process all the sessions of the user
    for i in s:
        user_sessions = events[events["session_id"] == i]
        user_sessions.to_csv(PATH_SESSIONS + "/" + str(uid) + "-" + str(count) + ".csv", index=False)

        split_session = [user_sessions]

        # if breaking points are found, the session splits into subsessions
        bp = break_points(user_sessions["interval"], user_sessions["minute"])
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

            minutes = np.unique(np.array(session["minute"]))
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
                subset = session[session["minute"] == m]
                l_edits.append(len(subset[subset["detailed_type"] == "edit-text"]))
                l_high_nav.append(len(subset[subset["detailed_type"] == "high-nav"]))
                l_text_nav.append(len(subset[subset["detailed_type"] == "text-nav"]))
                l_refactoring.append(len(subset[subset["detailed_type"] == "refactoring"]))
                l_debug.append(len(subset[subset["detailed_type"] == "debug"]))
                l_file.append(len(subset[subset["detailed_type"] == "file"]))
                l_build.append(len(subset[subset["detailed_type"] == "clean-build"]))
                l_tools.append(len(subset[subset["detailed_type"] == "tools"]))
                l_control.append(len(subset[subset["detailed_type"] == "control"]))
                l_testing.append(len(subset[subset["detailed_type"] == "testing"]))
                l_search.append(len(subset[subset["detailed_type"] == "search"]))

                if subset.iloc[len(subset)-1]["is_interruption"]:
                    l_inte.append(subset.iloc[len(subset)-1]["interval"]//60)
                    ni += 1
                else:
                    l_inte.append(0)

            so.values["id"].append(str(uid) + '-' + str(count))
            print (str(uid) + '-' + str(count))
            so.values["size_ts"].append(dur)

            #convert the lists created before to string
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

            so.values["edition"].append(str_edits)
            so.values["high_nav"].append(str_high_nav)
            so.values["text_nav"].append(str_text_nav)
            so.values["refactoring"].append(str_refactoring)
            so.values["debug"].append(str_debug)
            so.values["file"].append(str_file)
            so.values["clean_build"].append(str_build)
            so.values["tools"].append(str_tools)
            so.values["control"].append(str_control)
            so.values["testing"].append(str_testing)
            so.values["search"].append(str_search)
            so.values["interruptions"].append(str_inte)

            so.values["n_inte"].append(ni)
            so.values["start_time"].append(session.iloc[0]["datetime"])
            so.values["end_time"].append(session.iloc[len(session) - 1]["datetime"])
            so.values["user"].append(session.iloc[0][0])
            so.values["n_events"].append(len(session[session["detailed_type"] != " "]))

    result = so.create_dataframe()
    return result


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


def pipe_trans_events(file_path, files):
    """
    Applies transformation to the data on the files. Returns an object with the sessions
    """
    res = DataFrame()
    for i in range(0,len(files)):
        events = DataFrame.from_csv(file_path + "//" + files[i], index_col=False)
        print "processing file: " + files[i]
        events = preprocess_events(events)
        sessions = transform_to_sessions(events, i)
        #sessions = calc_metrics(sessions)
        if len(res) == 0:
            res = sessions
        else:
            res = res.append(sessions, ignore_index=True)
    return res
    
    
if __name__ == "__main__":

    print "starting transformation"

    start = time.time()
    
    # load all the data
    events = load_data(PATH_PREPROC)
    
    # sort it by user and datetime
    events = events.sort(["user","datetime"], ascending=[1, 1])
    
    # group by user
    events = events.groupby(["user"])
    
    # Create a file per user
    store_grouped_data(events, PATH_GROUPED_DATA)
    
    files = os.listdir(PATH_GROUPED_DATA)
    
    # Transform the data to sessions
    res = pipe_trans_events(PATH_GROUPED_DATA, files)

    # Keep sessions with at least 30 minutes of productive time
    res = res[res["size_ts"] >= 30]

    res.to_csv(PATH_TS_RESULT, index = False)
    end = time.time()
    print end-start


