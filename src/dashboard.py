import pandas as pd
import plotly.graph_objs as go
import plotly.offline as pyo
from plotly.subplots import make_subplots


def replace_nan_date_completed(x):
    if pd.isnull(x['date_completed']):
        return x['date_created']
    else:
        return x['date_completed']

# Read the CSV file into a DataFrame
df = pd.read_csv('data/data_dor_dashboard.csv', parse_dates=['date_created', 'date_completed'], na_values=['None'])

# Convert date columns to datetime format
df['date_created'] = pd.to_datetime(df['date_created'])
df['date_completed'] = pd.to_datetime(df['date_completed'])

# Replace NaN values in date_completed with date_created
# df['date_completed'] = df.apply(replace_nan_date_completed, axis=1)

# Create a new column for days taken to complete the task
df['days_taken'] = (df['date_completed'] - df['date_created']).dt.days

# Define a function to create a scatter plot with status as the color
def create_scatter_plot(df, x_col, y_col, color_col):
    # get color map by values of color_col column
    # number of unique values should be of a variable length
    color_map = dict(zip(df[color_col].unique(), [
        'red', 'green', 'blue', 'yellow', 'black', 'orange', 'pink', 'purple', 'brown', 'grey', 'cyan', 'magenta',
        'lime', 'maroon', 'navy', 'olive', 'teal', 'aqua', 'gold', 'indigo', 'violet', 'turquoise', 'tan', 'orchid',
    ]))
    fig = go.Figure(data=go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='markers',
        marker=dict(
            color=[color_map[x] for x in df[color_col]],
            colorscale='Viridis',
            showscale=False
        )
    ))
    fig.update_layout(
        title=f"{y_col} vs {x_col} by {color_col}",
        xaxis_title=x_col,
        yaxis_title=y_col,
    )
    return fig

# Create scatter plots for different combinations of columns
scatter_plot_1 = create_scatter_plot(df, 'urgency', 'days_taken', 'status')
scatter_plot_2 = create_scatter_plot(df, 'label_semantic', 'label_action', 'status')
scatter_plot_3 = create_scatter_plot(df, 'urgency', 'days_taken', 'label_semantic')

# Define a function to create a bar chart of task counts by label
def create_bar_chart(df, col):
    counts = df[col].value_counts()
    color_map = dict(zip(counts.index, [
        'red', 'green', 'blue', 'yellow', 'black', 'orange', 'pink', 'purple', 'brown', 'grey', 'cyan', 'magenta',
        'lime', 'maroon', 'navy', 'olive', 'teal', 'aqua', 'gold', 'indigo', 'violet', 'turquoise', 'tan', 'orchid',
    ]))
    fig = go.Figure(data=go.Bar(
        x=counts.index,
        y=counts.values,
        marker=dict(
            color=[color_map[x] for x in counts.index],
            colorscale='Viridis',
            showscale=False
        )
    ))
    fig.update_layout(
        title=f"Task Counts by {col}",
        xaxis_title=col,
        yaxis_title="Count"
    )
    return fig

# Create bar charts for different columns
bar_chart_1 = create_bar_chart(df, 'label_semantic')
bar_chart_2 = create_bar_chart(df, 'label_action')

# Arrange the plots in a grid using subplots
fig = make_subplots(
    rows=4,
    cols=1,
    specs=[[{'type': 'scatter'}], [{'type': 'scatter'}], [{'type': 'bar'}], [{'type': 'bar'}]],
    subplot_titles=(
        "Days taken to complete task", "Label semantic vs label action", "Task counts by label semantic",
        "Task counts by label action"
    ),
)
fig.add_trace(scatter_plot_1.data[0], row=1, col=1)
fig.add_trace(scatter_plot_2.data[0], row=2, col=1)
fig.add_trace(bar_chart_1.data[0], row=3, col=1)
fig.add_trace(bar_chart_2.data[0], row=4, col=1)

# Update the layout to add titles and adjust the size
fig.update_layout(height=1800, width=600, title_text="Task Dashboard")

# Show the dashboard in the notebook or save it to an HTML file
pyo.plot(fig, filename='task_dashboard.html')
