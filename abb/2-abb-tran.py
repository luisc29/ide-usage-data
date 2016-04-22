from __future__ import division
import glob
import time
from pandas import *
import os
import numpy as np

SIZE_INT = 180 #size threshold for the interruptions
SPACE_BETWEEN_INT = 28800 #threshold for the sessions
PATH_PREPROC = "//home//luis//abb//preproc" #path to the processed data
PATH_GROUPED_DATA = "//home//luis//abb//users" #where to store the grouped data
PATH_TS_RESULT = "/home/luis/abb/ts_abb.csv" #where to store the time series file
PATH_SESSIONS = "/home/luis/abb/sessions" #where to store a file per session
BREAK_POINT = 2700 #size of the interval to split the session in two



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
        i=i+1


def get_minute(time):
    """
    Calculates a unique identifier for the minute of the time given as
    parameter
    """
    m = time[4] + (time[3]*60) + (time[2]*60*24) * time[1] * time[0]
    return m
    
    
def transform_events(events):
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
    
    #Create an identifier for the minute of the event, usefull when creating
    #the sessions
    dt = [time.strptime(d,'%Y-%m-%d %H:%M:%S') for d in events["datetime"]]
    events["minute"] = [get_minute(d) for d in dt]
    
    #label interruptions and sessions
    interruptions = []
    sessions = []
    intervals = t
    s_id = 0
    for i in range(0,len(events)):
        sessions.append(s_id)
        if intervals[i] >= SPACE_BETWEEN_INT:
            s_id = s_id + 1
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

    #we consider sessions of 30 productive minutes, so we cannot split a session lesser than 60 minutes
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


def process_sessions(events, uid):
    """
    Transforms the data of every user to sessions, obtaining the metrics aswell 
    """
    
    class Sessions:
        values = {
            'id': [],
            'size': [],
            'inte': [],
            'edits': [],
            'selec': [],
            'l_inte': [],
            'l_edits': [],
            'l_select': [],
            'emin': [],  # editions per minute
            'smin': [],  # selections per minute
            'eratio': [],  # edit ratio
            'emin_detailed': [],
            'smin_detailed': [],
            'eratio_detailed': [],
            'n_inte': [],
            'n_events': [],
            'st_time': [],  # start time
            'end_time': [],  # end time
            'user': [],  # user id
            'et': [],  # edit-text
            'tn': [],  # text navigation
            'hn': [],  # high navigation
            'fi': [],  # files
            'ref': [],  # refactoring
            'cb': [],  # clean and build
            'de': [],  # debug
            'too': [],  # tools
            'con': [],  # control
            'te': [],  # test
            'se': [], # search
            'total_sessions': 0
        }
    
        def __init__(self):
            pass

        def calc_metrics(self):
            """
            Calculates the metrics editions per minute, selections per minute and edit ratio
            """
            sum_edits = sum(self.values["l_edits"][-1])
            sum_sel = sum(self.values["l_select"][-1])
            dur = self.values["size"][-1]
            self.values["emin"].append(sum_edits / dur)
            self.values["smin"].append(sum_sel / dur)
    
            # edit ratio
            if (sum_edits + sum_sel) == 0:
                self.values["eratio"].append(0)
            else:
                self.values["eratio"].append(sum_edits / (sum_edits + sum_sel))
    
        def calc_metrics_detailed(self):
            """
            Calculates the metrics using the detailed classification
            """
            sum_ed = self.values["et"][-1] + self.values["ref"][-1]
            sum_sd = self.values["tn"][-1] + self.values["hn"][-1] + self.values["de"][-1] + self.values["se"][-1]
            dur = self.values["size"][-1]
            self.values["emin_detailed"].append(sum_ed / dur)
            self.values["smin_detailed"].append(sum_sd / dur)
            if (sum_ed + sum_sd) == 0:
                self.values["eratio_detailed"].append(0)
            else:
                self.values["eratio_detailed"].append(sum_ed / (sum_ed + sum_sd))
    
        def create_dataframe(self):
            # creates a data frame with the sessions of the user
            sessions = pandas.DataFrame()
            sessions["size_ts"] = self.values["size"]
            sessions["interruption"] = self.values["inte"]
            sessions["edits"] = self.values["edits"]
            sessions["navigation"] = self.values["selec"]
            sessions["edit_min"] = self.values["emin"]
            sessions["sel_min"] = self.values["smin"]
            sessions["edit_ratio"] = self.values["eratio"]
            sessions["num_inte"] = self.values["n_inte"]
            sessions["start"] = self.values["st_time"]
            sessions["end"] = self.values["end_time"]
            sessions["user"] = self.values["user"]
            sessions["edit_text"] = self.values["et"]
            sessions["text_nav"] = self.values["tn"]
            sessions["high_nav"] = self.values["hn"]
            sessions["file"] = self.values["fi"]
            sessions["refactoring"] = self.values["ref"]
            sessions["clean_build"] = self.values["cb"]
            sessions["debug"] = self.values["de"]
            sessions["tools"] = self.values["too"]
            sessions["control"] = self.values["con"]
            sessions["testing"] = self.values["te"]
            sessions["event_count"] = self.values["n_events"]
            sessions["edit_min_detailed"] = self.values["emin_detailed"]
            sessions["sel_min_detailed"] = self.values["smin_detailed"]
            sessions["edit_ratio_detailed"] = self.values["eratio_detailed"]
            sessions["id"] = self.values["id"]
            return sessions
            
    so = Sessions()

    result = []

    s = set(events["session_id"])

    count = 0

    #process every session of the user
    for i in s:
        user_sessions = events[events["session_id"] == i]
        user_sessions.to_csv(PATH_SESSIONS + "/" + str(uid) + "-" + str(count) + ".csv", index=False)

        split_session = [user_sessions]

        #if breaking points are found, the session splits into subsessions
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
            l_selec = []
            l_inte = []
            dur = len(minutes)
            ni = 0

            for m in minutes:
                #for every minute of the session, count the number of edition and
                #selection events and the duration of the interruptions (among other types of events)
                subset = session[session["minute"] == m]
                l_edits.append(len(subset[subset["type"] == "edition"]))
                l_selec.append(len(subset[subset["type"] == "selection"]))
                if subset.iloc[len(subset)-1]["is_interruption"] == True:
                    l_inte.append(subset.iloc[len(subset)-1]["interval"]//60)
                    ni += 1
                else:
                    l_inte.append(0)

            so.values["id"].append(str(uid) + '-' + str(count))
            print (str(uid) + '-' + str(count))
            so.values["total_sessions"] += 1
            so.values["size"].append(dur)

            #convert the lists created before to string
            str_edits = ' '.join(str(e) for e in l_edits)
            str_selec = ' '.join(str(e) for e in l_selec)
            str_inte = ' '.join(str(e) for e in l_inte)
            so.values["edits"].append(str_edits)
            so.values["selec"].append(str_selec)
            so.values["inte"].append(str_inte)
            so.values["l_inte"].append(l_inte)
            so.values["l_edits"].append(l_edits)
            so.values["l_select"].append(l_selec)

            #calculate the metrics
            so.calc_metrics()

            #proportions per detailed type
            p_edit_text = len(session[session["detailed_type"] == "edit-text"])
            p_text_nav = len(session[session["detailed_type"] == "text-nav"])
            p_high_nav = len(session[session["detailed_type"] == "high-nav"])
            p_file = len(session[session["detailed_type"] == "file"])
            p_refactoring = len(session[session["detailed_type"] == "refactoring"])
            p_clean_build = len(session[session["detailed_type"] == "clean-build"])
            p_debug = len(session[session["detailed_type"] == "debug"])
            p_tools = len(session[session["detailed_type"] == "tools"])
            p_control = len(session[session["detailed_type"] == "control"])
            p_testing = len(session[session["detailed_type"] == "testing"])
            p_search = len(session[session["detailed_type"] == "search"])

            #set more attributes to each session
            so.values["n_inte"].append(ni)
            so.values["st_time"].append(session.iloc[0]["datetime"])
            so.values["end_time"].append(session.iloc[len(session)-1]["datetime"])
            so.values["user"].append(session.iloc[0][0])
            so.values["et"].append(p_edit_text)
            so.values["tn"].append(p_text_nav)
            so.values["hn"].append(p_high_nav)
            so.values["fi"].append(p_file)
            so.values["ref"].append(p_refactoring)
            so.values["cb"].append(p_clean_build)
            so.values["de"].append(p_debug)
            so.values["too"].append(p_tools)
            so.values["con"].append(p_control)
            so.values["te"].append(p_testing)
            so.values["se"].append(p_search)
            so.values["n_events"].append(len(session[session["detailed_type"] != " "]))

            # editions and selections per minute according to the detailed type
            so.calc_metrics_detailed()

           
    
    result = so.create_dataframe()
    return result


    
def pipe_trans_events(file_path,files):
    """
    Applies transformation to the data on the files. Returns an object with the sessions
    """
    res = DataFrame()
    for i in range(0,len(files)):
        events = DataFrame.from_csv(file_path + "//" + files[i],index_col=False)
        print "processing file: " + files[i]
        events = transform_events(events)
        sessions = process_sessions(events, i)
        if len(res) == 0:
            res = sessions
        else:
            res = res.append(sessions, ignore_index=True)
    return res
    
    
if __name__ == "__main__":

    print "starting transformation"

    start = time.time()
    
    #load all the data
    events = load_data(PATH_PREPROC)
    
    #sort it by user and datetime
    events = events.sort(["user","datetime"],ascending = [1,1])
    
    #group by user
    events = events.groupby(["user"])
    
    #Create a file per user
    store_grouped_data(events, PATH_GROUPED_DATA)
    
    files = os.listdir(PATH_GROUPED_DATA)
    
    #Transform the data to sessions
    res = pipe_trans_events(PATH_GROUPED_DATA, files)

    #Keep sessions with at least 30 minutes of productive time
    res = res[res["size_ts"] >= 30]

    res.to_csv(PATH_TS_RESULT, index = False)
    end = time.time()
    print end-start


