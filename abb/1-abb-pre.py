import os
from pandas import * 
from multiprocessing import Pool
import multiprocessing
import numpy as np
import time


PATH_TO_DATA = "//home//luis//abb//export-2015-10-23//"
PATH_TO_RESULT = "//home//luis//abb//preproc//"
PATH_TO_RESULT_MAIN = "//home//luis//abb//"


def infer_type(cmds):
    """
    Based on the description of the command, infers a type between edition, selection,
    system and control
    """
    desc = [s.split('.') for s in cmds["description"]]
    res = []
    for i in range(0,len(desc)):
        d = desc[i]
        value = ""
        # All the context menus labeled as selection
        if "ContextMenus" in d[0]:
            value = "selection"
            
        if("Analyze" in  d[0] or "Data" in d[0] or "Help" in d[0] or "Image" in d[0] or "Debug" in d[0] or "Design" in d[0]
        or "Report" in d[0] or "View" in d[0] or "File" in d[0] or "Macros" in d[0]
        or "Project" in d[0] or "Resources" in d[0] or "Explorer" in d[0]
        or "SQL" in d[0] or "Sql" in d[0] or "Table" in d[0] or "Test" in d[0]
        or "Tools" in d[0] or "Window" in d[0]):
            value = "selection"
        
        if("Edit" in d[0] or "Format" in d[0] or "ReSharper" in d[0] 
        or "Refactor" in d[0]):
            value = "edition"
            
        if "Team" in d[0]:
            value = "control"
        
        if "Build" in d[0] or "Action" in d[0]:
            value = "system"


        res.append(value)
    return res


def infer_detailed_type(cmds):
    """
    Infers the type of every event with more detail based on the description
    """
    desc = np.asarray(cmds["description"])
    res = []
    for i in range(0,len(desc)):
        d = desc[i]
        value = ""

        if "File" in d or "Project" in d:
            value = "file"

        if ("Analyze" in d or "Other" in d or "Image" in d or "Help" in d
            or "Designer" in d or "Report" in d or "SQL" in d or "Table" in d
            or "Data." in d or "Database" in d or "SSDT" in d or "Tools" in d
            or "Architecture" in d or "Diagram" in d or "Design" in d
            or "Graph" in d):
            value = "tools"

        if "Edit" in d or "Editor" in d:
            value = "edit-text"
            
        if value == "edit-text":
            if ("Scroll" in d or "Navigate" in d or "Next" in d or "Page" in d
            or "Previous" in d or "End" in d or "Start" in d or "Up" in d
            or "Down" in d or "Last" in d or "Left" in d or "Right" in d):
                value = "text-nav"
            
            if "Find" in d or "Found" in d or 'ObjectBrowser' in d:
                value = "search"
        
        if ("NavigateTo" in d or "GoTo" in d or "PreviousTab" in d
        or "NextTab" in d or "PreviousWindow" in d or "NextWindow" in d
        or "NextDocument" in d or "PreviousDocument" in d or 'Nav' in d):
            value = "high-nav"
        
        if "Refactor" in d or "ReSharper" in d:
            value = "refactoring"
        
        if "Build" in d:
            value = "clean-build"

        if "Debug" in d or "Debugger" in d:
            value = "debug"

        if "Test" in d:
            value = "testing"
            
        if "Team" in d or 'Diff' in d or 'Tfs' in d:
            value = "control"
            
        
        res.append(value)
    return res


def clean_commands(cmds):
    """
    Cleans the commands file, removing the curly braces from the
    unique identifier and the duplicated rows
    """
    cmds.columns = ["category", "event", "description"]
    cmds = cmds.drop_duplicates()
    cmds.is_copy = False

    # clean the description of the events
    res = [s.strip('{') for s in cmds.ix[:, 0]]
    res = [s.strip('}') for s in res]
    res = [s.lower() for s in res]
    cmds["category"] = res
    
    # infer the type and the detailed type of the events
    cmds["type"] = infer_type(cmds)
    cmds["detailed_type"] = infer_detailed_type(cmds)

    cmds.to_csv(PATH_TO_RESULT_MAIN + "cmds.clean.csv", index=False)

    return cmds


def set_description(events):
    """
    Looks for the description and type of an event on in the data frame 
    corresponding to the 'allcmds.csv' file
    """
    desc = []
    types = []
    d_types = []
    for i in range(0,len(events)):
        e = events.iloc[i]
        res = cmds[(cmds["category"] == e["category"]) & (cmds["event"] == e["event"])]
        if len(res)>0:
            desc.append(res["description"].iloc[0])
            types.append(res["type"].iloc[0])
            d_types.append(res["detailed_type"].iloc[0])
        else:
            desc.append(" ")
            types.append(" ")
            d_types.append(" ")
    return desc,types, d_types


def clean_events(file_path, file_name):
    """
    Cleans a single file, formatting the datetime, dropping
    repeated rows and setting the description of the event
    from the 'allcmds.csv' file
    """
    
    # Load a file and rename the columns
    events = DataFrame.from_csv(file_path + "//" + file_name,index_col=False)
    events.columns = ["user", "datetime", "category", "event"]
    
    # Format the datetime value
    events["datetime"] = [s.split('.')[0] for s in events["datetime"]]
    events["seconds"] = [time.mktime(time.strptime(s,'%Y-%m-%d %H:%M:%S')) for s in events["datetime"]]
    
    # Remove events based on the event description:
    # Build.SolutionConfigurations
    # Build.SolutionPlatforms
    events = events[events["event"] != 684]
    events = events[events["event"] != 1990]
    
    # Remove duplicated rows (all the values are the same)
    events = events.drop_duplicates()
    
    # Get the description and type from the commands dataset
    desc, types, d_types = set_description(events)
    events["description"] = desc
    events["type"] = types
    events["detailed_type"] = d_types
    
    # Remove events without description
    events = events[events["description"] != " "]
    
    # Store the cleaned data
    events.to_csv(PATH_TO_RESULT + "clean."+ file_name, index=False)
    

    return events


def clean_focus_data(file_path, file_name):
    focus = DataFrame.from_csv(file_path + file_name, index_col=False)
    focus.columns = ["user", "datetime", "focus"]
    focus = focus.sort(["user", "datetime"], ascending=[1, 1])
    return focus


def pipe_clean_events(file_path, files):
    """
    Processes a number of files on a single thread
    """
    res = DataFrame()
    for i in range(0,len(files)):
        res = res.append(clean_events(file_path,files[i]))
    return res
    
    
def exec_parallel(fun,args):
    """
    Executes the preprocessing in parallel
    """
    res = []
    tasks = []
    cores = multiprocessing.cpu_count()
    pool = Pool()
    for i in range(0,cores):
        t = pool.apply_async(set_description,[args[i]])
        tasks.append(t)
    
    for i in range(0,cores):
        res.append(tasks[i].get())
    
    return res
    
    
if __name__ == "__main__":
    print "Preprocessing started"
    
    # Load the commands. All the files must be previously appended
    cmds = DataFrame.from_csv(PATH_TO_DATA + "allcmds.csv", index_col=False)
    
    # Clean the commands
    cmds = clean_commands(cmds)

    # The tinyevents.csv was previously split into files of 200,000 lines each
    path = PATH_TO_RESULT_MAIN + "events"
    files = os.listdir(path)
    
    cores = multiprocessing.cpu_count()
    
    # Split the files into n groups
    files = np.array_split(files,cores)
    
    start = time.time()
    print "Parallel execution started"
    pool = Pool()
    r = []
    for i in range(0,cores):
        r1 = pool.apply_async(pipe_clean_events,[path,files[i]])
        r.append(r1)

    desc2 = []
    for i in range(0,cores):
        desc2.append(r[i].get())
    pool.close()
    pool.terminate()
    end = time.time()
    print "Parallel execution finished, total time: "
    print end - start

    # Clean focus dataset
    focus = clean_focus_data(PATH_TO_DATA, "tinyfocus.csv")
    focus.to_csv(PATH_TO_RESULT_MAIN + "focus.clean.csv", index=False)

