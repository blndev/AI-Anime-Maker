import pandas as pd  # db querys with visualization
import matplotlib.pyplot as plt  # diagrams
import matplotlib.image as mpimg  # images
import seaborn as sns           # Heatmaps etc.
from user_agents import parse   # Split OS. Browser etc.
import math  # calc sizes
import logging
import src.config as config

# Set up module logger
logger = logging.getLogger(__name__)


def showBar(df: pd.DataFrame, title: str, x_column: str, y_column: str = "SessionCount", x_label: str = None, y_label: str = None, show_x_values=True):
    """generates a bar chart in Jupyter Notebook"""
    if len(df) == 0:
        logger.info("No data collected")
        return

    try:
        if not x_label:
            x_label = x_column
        if not y_label:
            _ylabel = y_column
        ax = df.plot.bar(x=x_column, y=y_column,
                         color="skyblue", legend=show_x_values)
        for container in ax.containers:
            ax.bar_label(container, fmt='%d', label_type='edge')
            if show_x_values:
                plt.xlabel = x_label
            if not show_x_values:
                ax.set_xticks([])
            plt.ylabel = y_label
            plt.title(title)
            # optimization depending on your data
            # plt.figure(figsize=(10,6))
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
    except Exception as e:
        logger.error("Error showing bar chart: %s", str(e))


def showImage(path: str, name: str = ""):
    """shows an image in Jupyter Notebook"""
    img = mpimg.imread(path)
    plt.imshow(img)
    plt.axis('off')
    plt.title(f"Image {name}")
    plt.show()


def showImageGrid(df: pd.DataFrame, path_column: str, name_column: str = None, descr_column: str = None):
    if len(df) == 0:
        logger.info("No data collected")
        return
    n_cols = 3
    n_rows = math.ceil(len(df)/n_cols)

    # Calculate plot size
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(10, 10))

    # load images and text
    for idx, (ax, row) in enumerate(zip(axes.flatten(), df.iterrows())):
        _, row_data = row
        try:
            img = mpimg.imread(row_data[path_column])

            ax.imshow(img)
            ax.axis('off')
            if name_column:
                title = row_data[name_column]
                if descr_column:
                    title = f"{title} \n {row_data[descr_column]}"
                ax.set_title(title, fontsize=12)
        except FileNotFoundError:
            ax.text(0.5, 0.5, 'Image not found', fontsize=12, ha='center', va='center')
            ax.axis('off')

    for ax in axes.flatten()[len(df):]:
        ax.axis('off')  # Entferne leere Zellen

    # Align space between images
    plt.tight_layout()
    plt.show()


def get_os(user_agent):
    os = (parse(user_agent)).os
    if (os.version_string != ""):
        return os.family + " " + os.version_string
    else:
        return os.family


def enhance_data(df_sessions):
    # function to put make the dataframe more feature rich and simplify queries later
    df_sessions['Datetime'] = pd.to_datetime(df_sessions["Timestamp"])
    # For analysis it is interesting which day of week has the entry
    df_sessions['Day'] = df_sessions["Datetime"].dt.day_name()
    # alternate way is lambda, but a function can be more complex
    df_sessions['OS'] = df_sessions["Client"].apply(get_os)
    df_sessions['Browser'] = df_sessions["Client"].apply(
        lambda ua: parse(ua).browser.family)
    df_sessions['IsMobile'] = df_sessions["Client"].apply(
        lambda ua: parse(ua).is_mobile)
    df_sessions['IsBot'] = df_sessions["Client"].apply(
        lambda ua: parse(ua).is_bot)
    return df_sessions
