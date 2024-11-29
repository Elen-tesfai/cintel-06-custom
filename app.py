import pandas as pd
import requests
from io import StringIO
import plotly.express as px
from shiny import App, ui, render, reactive
import faicons as fa

# Fetch Titanic dataset from URL
url = "https://raw.githubusercontent.com/plotly/datasets/master/titanic.csv"

# Fetch the data using requests
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Convert the raw CSV text content into a pandas DataFrame
    df = pd.read_csv(StringIO(response.text))
    
    # Clean column names (remove leading/trailing spaces and convert to lowercase)
    df.columns = df.columns.str.strip().str.lower()
else:
    print(f"Failed to retrieve data. HTTP Status Code: {response.status_code}")
    df = pd.DataFrame()  # Empty dataframe if failed

# Define Font Awesome icons for the Titanic dataset
ICONS = {
    "ship": fa.icon_svg("ship"),  # Titanic ship icon
    "person": fa.icon_svg("user"),  # Gender related
    "ticket": fa.icon_svg("ticket"),  # Pclass related
    "calendar": fa.icon_svg("calendar"),  # Age related
}

# Sidebar Layout using ui.sidebar for filtering options
sidebar = ui.sidebar(
    # Removed the "Titanic Data Filters" heading
    # ui.h5(ui.TagList("Titanic Data Filters ", ICONS['ship'])),  # Title for sidebar

    # Pclass Selectize dropdown with ticket icon, adding "Select All" option
    ui.input_selectize(
        "selected_pclass", 
        ui.TagList("Select Pclass ", ICONS['ticket']),  
        choices=["1", "2", "3", "All"],  
        selected=["1"],  
        multiple=True  
    ),

    # Gender Selectize dropdown with person icon, adding "Select All" option
    ui.input_selectize(
        "selected_sex", 
        ui.TagList("Select Gender ", ICONS['person']),  
        choices=["male", "female", "All"],  
        selected=["male", "female"],  
        multiple=True  
    ),

    # Age range slider with calendar icon
    ui.input_slider(
        "age_range", 
        ui.TagList("Select Age Range ", ICONS['calendar']),  
        min=0, 
        max=100, 
        value=[20, 50], 
        step=1  
    ),
    
    # Dropdown to select plot type
    ui.input_select(
        "selected_plot", 
        "Select Plot Type", 
        choices=["Scatterplot: Age vs Fare", "Histogram: Age Distribution", "Dataset Table", "Box Plot: Titanic Dataset by Survived"],
        selected="Scatterplot: Age vs Fare"
    )
)

# UI Definition using ui.page_sidebar() for main content layout
app_ui = ui.page_sidebar(
    sidebar,  # Sidebar content (previously defined)
    
    # Main content area using ui.page_fluid() for fluid layout
    ui.page_fluid(
        # Title for the page
        ui.h2("Interactive Titanic Data Insights", align="center"),  # New title

        # Dynamic output based on selected plot type
        ui.row(
            ui.column(12,
                ui.card(
                    ui.card_header(ui.TagList("Titanic Data Visualizations", ICONS['ship'])),
                    ui.card_body(ui.output_ui("selected_visualization"))
                )
            )
        )
    )
)

# Server function: where all the interactivity happens
def server(input, output, session):

    # Reactive calculation to simulate data updates or filtering based on inputs
    @reactive.Calc
    def filtered_data():
        # Get the inputs correctly
        selected_pclass = input.selected_pclass()  # Get passenger class
        selected_sex = input.selected_sex()  # Get gender
        age_range = input.age_range()  # Get age range

        # Filter data based on inputs
        filtered_df = df.copy()

        # Handle "Select All" logic for passenger class and gender filters
        if "All" in selected_pclass:
            selected_pclass = ["1", "2", "3"]  # Treat "All" as all classes
        if "All" in selected_sex:
            selected_sex = ["male", "female"]  # Treat "All" as all genders
        
        # Apply passenger class filter (ensure the input is iterable)
        if selected_pclass:
            filtered_df = filtered_df[filtered_df['pclass'].isin(map(int, selected_pclass))]
        
        # Apply gender filter (ensure the input is iterable)
        if selected_sex:
            filtered_df = filtered_df[filtered_df['sex'].isin(selected_sex)]
        
        # Apply age range filter
        if age_range:
            filtered_df = filtered_df[(filtered_df['age'] >= age_range[0]) & (filtered_df['age'] <= age_range[1])]

        return filtered_df

    # Render the selected visualization (scatterplot, histogram, table, or box plot)
    @output
    @render.ui
    def selected_visualization():
        # Get the selected plot type
        plot_type = input.selected_plot()

        if plot_type == "Scatterplot: Age vs Fare":
            return age_vs_fare_scatterplot()
        
        elif plot_type == "Histogram: Age Distribution":
            return age_distribution_histogram()
        
        elif plot_type == "Dataset Table":
            return data_grid()
        
        elif plot_type == "Box Plot: Titanic Dataset by Survived":
            return box_plot_survived()

    # Render the Plotly Scatterplot for Age vs Fare with custom axis ticks
    def age_vs_fare_scatterplot():
        filtered_df = filtered_data()  # Directly call the reactive filtered data
        fig = px.scatter(filtered_df, x='age', y='fare', color='survived', title='Age vs Fare (Titanic Dataset)')
        
        # Customize the x-axis and y-axis with specific tick values
        fig.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=[0, 20, 40, 60],  # Custom tick values for age
                ticktext=['0', '20', '40', '60']  # Custom tick labels for age
            ),
            yaxis=dict(
                tickmode='array',
                tickvals=[10, 20, 30, 40, 50, 60, 70],  # Custom tick values for fare
                ticktext=['10', '20', '30', '40', '50', '60', '70']  # Custom tick labels for fare
            )
        )
        return ui.HTML(fig.to_html(full_html=False))  # Render Plotly figure as HTML

    # Render the Plotly Histogram for Age Distribution
    def age_distribution_histogram():
        filtered_df = filtered_data()  # Directly call the reactive filtered data
        fig = px.histogram(filtered_df, x='age', nbins=20, title='Age Distribution of Titanic Passengers')  # Corrected title
        return ui.HTML(fig.to_html(full_html=False))  # Render Plotly histogram as HTML

    # Render the Data Grid for Titanic Dataset (without row index)
    def data_grid():
        filtered_df = filtered_data()  # Directly call the reactive filtered data
        # Make sure the filtered dataframe has data before rendering
        if filtered_df.empty:
            return ui.markdown("No data to display with the selected filters.")
        
        # Render the filtered data table, excluding the index
        return ui.HTML(filtered_df.to_html(classes='table table-striped table-bordered', index=False))  # Exclude the row index

    # Render a Box Plot for the Titanic dataset grouped by the "survived" column
    def box_plot_survived():
        filtered_df = filtered_data()  # Directly call the reactive filtered data
        fig = px.box(filtered_df, x="survived", y="age", title="Box Plot: Titanic Dataset by Survived")
        return ui.HTML(fig.to_html(full_html=False))  # Render Plotly figure as HTML

# Create the app object
app = App(app_ui, server)

if __name__ == "__main__":
    app.run()