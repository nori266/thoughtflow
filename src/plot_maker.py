from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.switch_backend('Agg') # for running on server without X11


class PlotMaker():
    PLOTS_DIR: Path = Path('plots')
    PLOTS_DIR.mkdir(exist_ok=True)

    @staticmethod
    def get_plots(thoughts: List) -> str:
        print("Plotting...")
        # transform database objects to pandas dataframe and parse the dates
        df = pd.DataFrame(thoughts)
        df['date_created'] = pd.to_datetime(df['date_created'])
        df['date_completed'] = pd.to_datetime(df['date_completed'])
        df_nn = df[df.status.notna()]
        return PlotMaker.plot_value_counts(df_nn)


    @staticmethod
    def plot_value_counts(df: pd.DataFrame) -> str:
        plot_path = PlotMaker.PLOTS_DIR / 'value_counts_done_2.png'
        uniq_labels = df.label.unique()
        colors = plt.cm.Paired(np.arange(uniq_labels.shape[0]))
        vc_all = df.label.value_counts()
        vc_done = df[df.status == "done"].label.value_counts()  # TODO plot done according to date_completed
        df_for_plot = pd.DataFrame({'opened': vc_all, 'done': vc_done}, index=uniq_labels)
        df_for_plot.sort_values(by="opened").plot.barh(color=colors)
        plt.tight_layout()
        plt.savefig(plot_path)
        return plot_path.as_posix()

    @staticmethod
    def plot_each_label(df) -> str:
        # FIXME not used at the moment
        # plot a sum of all the thoughts for each label by date
        for label in df['label'].unique():
            df_label = df[df['label'] == label]
            df_label = df_label.set_index('date_created')
            df_label['count'] = 1
            df_label = df_label.resample('D').sum()
            df_label['cumsum'] = df_label['count'].cumsum()
            df_label['cumsum'].plot()
            plt.savefig(PlotMaker.PLOTS_DIR / f'{label}.png')
            plt.close()
        return PlotMaker.PLOTS_DIR.as_posix()
