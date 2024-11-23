# Import required libraries
from shiny import App, ui, render, reactive
import pandas as pd
import plotly.express as px

# Step 1: Load a dataset (for this example, we'll use the Seaborn 'tips' dataset)
# You can replace this with your dataset of choice
df = pd.read_csv("https://raw.githubusercontent.com/mwaskom/seaborn-data/master/tips.csv")

# Step 2: Define the reactive data filtering function
@reactive.calc
def filter_data(time_of_day: str):
    """Filter the dataframe based on user-selected time of day."""
    return df[df['time'] == time_of_day]

# Step 3: Define UI components
app_ui = ui.page_fluid(
    # Title of the dashboard
    ui.h1("Interactive Dashboard: Restaurant Tips Data"),

    # Dropdown input to filter by time of day (Lunch or Dinner)
    ui.input_select("time_of_day", "Select Time of Day", choices=["Lunch", "Dinner"]),

    # Output: Table of filtered data
    ui.output_table("table"),

    # Output: Plot of tips data (bar plot of total bill vs tip, colored by day)
    ui.output_plot("plot")
)

# Step 4: Define the server-side reactive outputs
@render.table
def render_table(time_of_day):
    """Render the table based on the filtered data."""
    filtered_data = filter_data(time_of_day)
    return filtered_data

@render.plot
def render_plot(time_of_day):
    """Render a bar plot based on the filtered data."""
    filtered_data = filter_data(time_of_day)

    # Create a Plotly bar plot of total_bill vs tip, colored by day
    fig = px.bar(filtered_data, x='total_bill', y='tip', color='day', 
                 title="Total Bill vs Tip (Filtered by Time of Day)")
    return fig

# Step 5: Create the app instance
app = App(app_ui)
