from __future__ import division
import glob
import time
from pandas import *
from multiprocessing import Pool
import multiprocessing
import os

SIZE_INT = 180 #size threshold for the interruptions
SPACE_BETWEEN_INT= 28800 #threshold for the sessions
PREPROC_PATH = "//home//luis//abb//preproc" #path to the processed data
GROUPED_DATA_PATH = "//home//luis//abb//users" #where to store the grouped data
TS_RESULT_PATH = "/home/luis/abb/ts_abb.csv" #where to store the time series



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
    
    
def process_sessions(events):
    """
    Transforms the data of every user to sessions, obtaining the metrics aswell 
    """
    size = []
    inte = []
    edits = []
    selec = []
    emin = []
    smin = []
    eratio = []
    emin_detailed = []
    smin_detailed = []
    eratio_detailed = []
    n_inte = []
    n_events = []
    st_time = []
    end_time = []
    user = []
    et = []
    tn = []
    hn = []
    fi = []
    ref = []
    cb = []
    de = []
    too = []
    con = []
    te = []
    n_events = []


    s = set(events["session_id"])
    
    #process every session of the user
    for i in s:
        session = events[events["session_id"] == i]
        minutes = set(session["minute"])
        l_edits = []
        l_selec = []
        l_inte = []
        dur = len(minutes)
        ni = 0
        
        for m in minutes:
            #for every minute of the session, count the number of edition and 
            #selection events and the duration of the interruptions
            subset = session[session["minute"] == m]
            l_edits.append(len(subset[subset["type"] == "edition"]))
            l_selec.append(len(subset[subset["type"] == "selection"]))
            if subset.iloc[len(subset)-1]["is_interruption"] == True:
                l_inte.append(subset.iloc[len(subset)-1]["interval"]//60)
                ni = ni+1
            else:
                l_inte.append(0)
        
        size.append(dur)
        
        #convert the lists created before to string
        str_edits = ' '.join(str(e) for e in l_edits)
        str_selec = ' '.join(str(e) for e in l_selec)    
        str_inte = ' '.join(str(e) for e in l_inte)
        edits.append(str_edits)
        selec.append(str_selec)
        inte.append(str_inte)
        
        #calculate the metrics
        sum_e = sum(l_edits)
        sum_s = sum(l_selec)
        emin.append(sum_e/dur)
        smin.append(sum_s/dur)
        
        #edit ratio
        if (sum_e + sum_s) == 0:
            eratio.append(0)
        else:
            eratio.append(sum_e/(sum_e+sum_s))
        
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
        
        #editions and selections per minute according to the detailed type
        sum_ed = p_edit_text+p_refactoring
        sum_sd = p_text_nav+p_high_nav
        emin_detailed.append(sum_ed/dur)
        smin_detailed.append(sum_sd/dur)
        if (sum_ed + sum_sd) == 0:
            eratio_detailed.append(0)
        else:
            eratio_detailed.append(sum_ed / (sum_ed + sum_sd))

        n_inte.append(ni)
        #n_events.append(len(session))
        st_time.append(session.iloc[0]["datetime"])
        end_time.append(session.iloc[len(session)-1]["datetime"])
        user.append(session.iloc[0][0])
        et.append(p_edit_text)
        tn.append(p_text_nav)
        hn.append(p_high_nav)
        fi.append(p_file)
        ref.append(p_refactoring)
        cb.append(p_clean_build)
        de.append(p_debug)
        too.append(p_tools)
        con.append(p_control)
        te.append(p_testing)

        n_events.append(len(session[session["detailed_type"] != " "]))

    
    #creates a data frame with the sessions of the user
    sessions = pandas.DataFrame()
    sessions["size_ts"] = size
    sessions["interruption"] = inte
    sessions["edits"] = edits
    sessions["navigation"] = selec
    sessions["edit_min"] = emin
    sessions["sel_min"] = smin
    sessions["edit_ratio"] = eratio
    sessions["num_inte"] = n_inte
    sessions["start"] = st_time
    sessions["end"] = end_time
    sessions["user"] = user
    sessions["edit_text"] = et
    sessions["text_nav"] = tn
    sessions["high_nav"] = hn
    sessions["file"] = fi
    sessions["refactoring"] = ref
    sessions["clean_build"] = cb
    sessions["debug"] = de
    sessions["tools"] = too
    sessions["control"] = con
    sessions["testing"] = te
    sessions["event_count"] = n_events
    sessions["edit_min_detailed"] = emin_detailed
    sessions["sel_min_detailed"] = smin_detailed
    sessions["edit_ratio_detailed"] = eratio_detailed
    
    return sessions
    
    
def pipe_trans_events(file_path,files):
    """
    Applies transformation to the data on the files. Returns an object with the sessions
    """
    res = DataFrame()
    for i in range(0,len(files)):
        events = DataFrame.from_csv(file_path + "//" + files[i],index_col=False)
        print "processing file: " + files[i]
        events = transform_events(events)
        events = process_sessions(events)
        res = res.append(events)
    return res
    
    
if __name__ == "__main__":


    print "starting transformation"

    start = time.time()
    
    #load all the data
    events = load_data(PREPROC_PATH)
    
    #sort it by user and datetime
    events = events.sort(["user","datetime"],ascending = [1,1])
    
    #group by user
    events = events.groupby(["user"])
    
    #Create a file per user
    store_grouped_data(events, GROUPED_DATA_PATH)
    
    files = os.listdir(GROUPED_DATA_PATH)
    cores = multiprocessing.cpu_count()
    
    #Transform the data to sessions
    res = pipe_trans_events(GROUPED_DATA_PATH,files)

    #Keep sessions with at least 30 minutes of productive time
    res = res[res["size_ts"] >= 30]
    
    res.to_csv(TS_RESULT_PATH, index = False)
    end = time.time()
    print end-start


