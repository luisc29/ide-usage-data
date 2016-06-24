import matplotlib as mp
import matplotlib.pyplot as plt
import numpy

from pandas import *

PATH_TO_RESULT_MAIN = "/home/luis/abb/"
PATH_TS_FILE = "/home/luis/abb/ts_abb.csv"
TIME_SERIES_NAMES = ['edition', 'text_nav', 'high_nav', 'file', 'refactoring',
                     'clean_build', 'debug', 'tools', 'control', 'testing', 'search']

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
    # todo