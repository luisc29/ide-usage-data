import matplotlib as mp
import matplotlib.pyplot as plt
import numpy

from pandas import *

PATH_TO_RESULT_MAIN = "//home//luis//abb//"
PATH_TS_FILE = "/home/luis/abb/ts_abb.csv"


def load_data():
    data = pandas.read_csv(PATH_TS_FILE, index_col=None, header=0)
    return data


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


def plot_boxplot(data, x_label, y_label, y_lim, color, file_name):
    # Create a figure instance
    fig = plt.figure(1, figsize=(9, 6))

    # Create an axes instance
    ax = fig.add_subplot(111)

    # Create the boxplot
    bp = ax.boxplot(data)

    # Save the figure
    fig.savefig(file_name, bbox_inches='tight')


def plot_productivity(sessions):
    metrics = ["emin", "smin", "eratio"]
    metrics_label = ["Edits per minute", "Selections per minute", "Edit ratio"]

    n_inte = numpy.asarray(sessions["n_inte"], int)
    thresholds = [numpy.percentile(n_inte, 25), numpy.percentile(n_inte, 50), numpy.percentile(n_inte, 75)]

    for m in metrics:
        vals = sessions[m]
        g1 = sessions[sessions["n_inte"] == 0][m]
        g2 = sessions[(sessions["n_inte"] > 0) & (sessions["n_inte"] <= thresholds[0])][m]
        g3 = sessions[(sessions["n_inte"] > thresholds[0]) & (sessions["n_inte"] <= thresholds[1])][m]
        g4 = sessions[(sessions["n_inte"] > thresholds[1]) & (sessions["n_inte"] <= thresholds[2])][m]
        g5 = sessions[(sessions["n_inte"] > thresholds[2])][m]
        groups = [g1, g2, g3, g4, g5]
        plot_boxplot(groups, 0, 0, 0, 0, m + ".png")


if __name__ == "__main__":
    sessions = load_data()

    sessions = calc_metrics(sessions)

    plot_productivity(sessions)
