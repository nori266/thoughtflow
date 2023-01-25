import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

DATA = "data/all_thoughts.csv"
PLOT_FILE = "data/seq_length_hist.png"
PLOT_TITLE = "Sequence Length Distribution"


def main():
    df = pd.read_csv(DATA)
    df["seq_length"] = df["thought"].apply(lambda x: len(x))
    ax = sns.distplot(df["seq_length"])
    ax.axvline(df["seq_length"].quantile(.95))
    plt.text(df["seq_length"].quantile(.95), 0.01, "95%")
    plt.title(PLOT_TITLE)
    plt.savefig(PLOT_FILE)
    print("Saved plot to", PLOT_FILE)


if __name__ == "__main__":
    main()
