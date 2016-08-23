import os
from pandas import * 
from multiprocessing import Pool
import multiprocessing
import numpy as np
import time
import math

PATH_TO_MAIN = '//home//luis//udc//'


def infer_detailed_type(cmds):
    """
    Based on the description of the command, infers a type between edition, selection,
    system and control
    """
    res = []
    for i in range(0,len(cmds)):
        print i
        d = cmds[i]
        value = ''
        
        if d == ' ':
            res.append('system')
            continue
        
        if '.ui.project' in d or '.ant.ui' in d:
            value = 'clean-build'
        
        if '.file' in d:
            value = "file"
            
        if ('.report' in d or '.pde' in d or '.php' in d or '.emf' in d
            or '.gmf' in d or '.mylyn' in d):
            value = 'tools'
        else:
            if '.ui.edit' in d:
                value = 'edit-text'
                if '.goto' in d or '.scroll' in d or '.select' in d:
                    value = 'text-nav'
                if '.find' in d or '.search' in d:
                    value = 'search'
                if '.ui.edit.text.java' in d:
                    value = 'refactoring'
            else:
                if '.Search' in d:
                    value = 'search'
                    
                if ('.CompilationUnitEditor' in d or 'hierarchy' in d or 'View' in d
                    or '.ui.window' in d):
                    value = 'high-nav'
                    
                if '.debug.ui' in d:
                    value = 'debug'
                
                if '.junit' in d:
                    value = 'test'
                    
                if '.team' in d or '.subversion' in d or '.compare' in d:
                    value = 'control'
        
        res.append(value)
        
    return res
    

def infer_general_type(types):
    res = []
    for t in types:
        if t == 'edit-text' or t == 'text-nav':
            res.append('edition')
        else:
            if t == 'clean-build':
                res.append('system')
            else:
                res.append('selection')
    return res
    
    
def clean_events(log):
    log = log.drop('kind', 1)
    log = log.drop('bundleId', 1)
    log.columns = ['user', 'description', 'datetime']
    
    log['description'] = log['description'].fillna(' ')
    
    types = infer_detailed_type(np.array(log.loc[:,'description']))
    log['detailed_type'] = types
    log['type'] = infer_general_type(types)
    
    log["seconds"] = [time.mktime(time.strptime(s,'%Y-%m-%d %H:%M:%S')) for s in log["datetime"]]
    
    log.to_csv(PATH_TO_MAIN + 'clean.dataC.csv', index=False)
    return log
    

if __name__ == "__main__":
    print "Preprocessing started"
    
    log = DataFrame.from_csv(PATH_TO_MAIN + 'dataC.csv', index_col=False)
    
    clean_events(log)
    
    
    
    