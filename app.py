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
    ui.input_selectize(
        "selected_pclass", 
        ui.TagList("Select Pclass ", ICONS['ticket']),  
        choices=["1", "2", "3", "All"],  
        selected=["1"],  
        multiple=True  
    ),
    ui.input_selectize(
        "selected_sex", 
        ui.TagList("Select Gender ", ICONS['person']),  
        choices=["male", "female", "All"],  
        selected=["male", "female"],  
        multiple=True  
    ),
    ui.input_slider(
        "age_range", 
        ui.TagList("Select Age Range ", ICONS['calendar']),  
        min=0, 
        max=100, 
        value=[20, 50], 
        step=1  
    ),
    ui.input_select(
        "selected_plot", 
        "Select Plot Type", 
        choices=["Scatterplot: Age vs Fare", "Histogram: Age Distribution", "Dataset Table", "Box Plot: Titanic Dataset by Survived"],
        selected="Scatterplot: Age vs Fare"
    )
)

# UI Definition using ui.page_sidebar() for main content layout
app_ui = ui.page_sidebar(
    sidebar,  
    ui.page_fluid(
        ui.h2("Interactive Titanic Data Insights", align="center"),
        ui.row(
            ui.column(12,
                ui.card(
                    ui.card_header(ui.TagList("Titanic Data Visualizations", ICONS['ship'])),
                    ui.card_body(ui.output_ui("selected_visualization"))
                )
            )
        ),
        # New live watch and ticket sold section
        ui.row(
            ui.column(12,
                ui.card(
                    ui.card_header("Live Watch and Ticket Sales"),
                    ui.card_body(ui.output_ui("live_watch"))
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
        selected_pclass = input.selected_pclass()
        selected_sex = input.selected_sex()
        age_range = input.age_range()

        filtered_df = df.copy()

        if "All" in selected_pclass:
            selected_pclass = ["1", "2", "3"]
        if "All" in selected_sex:
            selected_sex = ["male", "female"]
        
        if selected_pclass:
            filtered_df = filtered_df[filtered_df['pclass'].isin(map(int, selected_pclass))]
        
        if selected_sex:
            filtered_df = filtered_df[filtered_df['sex'].isin(selected_sex)]
        
        if age_range:
            filtered_df = filtered_df[(filtered_df['age'] >= age_range[0]) & (filtered_df['age'] <= age_range[1])]

        return filtered_df

    # Render the selected visualization (scatterplot, histogram, table, or box plot)
    @output
    @render.ui
    def selected_visualization():
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
        filtered_df = filtered_data()
        fig = px.scatter(filtered_df, x='age', y='fare', color='survived', title='Age vs Fare (Titanic Dataset)')
        
        fig.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=[0, 20, 40, 60],
                ticktext=['0', '20', '40', '60']
            ),
            yaxis=dict(
                tickmode='array',
                tickvals=[10, 20, 30, 40, 50, 60, 70],
                ticktext=['10', '20', '30', '40', '50', '60', '70']
            )
        )
        return ui.HTML(fig.to_html(full_html=False))

    # Render the Plotly Histogram for Age Distribution
    def age_distribution_histogram():
        filtered_df = filtered_data()
        fig = px.histogram(filtered_df, x='age', nbins=20, title='Age Distribution of Titanic Passengers')
        return ui.HTML(fig.to_html(full_html=False))

    # Render the Data Grid for Titanic Dataset (without row index)
    def data_grid():
        filtered_df = filtered_data()
        if filtered_df.empty:
            return ui.markdown("No data to display with the selected filters.")
        return ui.HTML(filtered_df.to_html(classes='table table-striped table-bordered', index=False))

    # Render a Box Plot for the Titanic dataset grouped by the "survived" column
    def box_plot_survived():
        filtered_df = filtered_data()
        fig = px.box(filtered_df, x="survived", y="age", title="Box Plot: Titanic Dataset by Survived")
        return ui.HTML(fig.to_html(full_html=False))

    # Live Watch and Ticket Counter Simulation
    @output
    @render.ui
    def live_watch():
        return ui.HTML("""
            <div id="live-watch" style="text-align: center; background-color: #f0f0f0; padding: 20px; border-radius: 8px;">
                🕒 Live Watch: <span id="time" style="font-weight: bold; color: #007BFF;">00:00</span> | 
                🎟️ Tickets Sold: <span id="ticket" style="font-weight: bold; color: #28a745;">0</span>
            </div>
            <script>
                let timeElapsed = 0;  // Time in seconds
                let ticketCount = 0;  // Ticket count
                let ticketInterval = 1000; // Simulate tickets being sold every 1000ms (1 ticket per second)
                let timeInterval = 1000;  // Simulate real-time passage of 1 second
                let timeDisplay = document.getElementById('time');
                let ticketDisplay = document.getElementById('ticket');
                
                // Format time in MM:SS format
                function formatTime(seconds) {
                    let minutes = Math.floor(seconds / 60);
                    let remainingSeconds = seconds % 60;
                    if (remainingSeconds < 10) {
                        remainingSeconds = '0' + remainingSeconds;
                    }
                    return minutes + ':' + remainingSeconds;
                }

                // Simulate the time passing
                setInterval(() => {
                    timeElapsed++;
                    timeDisplay.textContent = formatTime(timeElapsed);  // Update time every second
                }, timeInterval);  // Update time every 1000 ms

                // Simulate tickets being sold at a slower pace
                setInterval(() => {
                    ticketCount += 1;  // Increase ticket count
                    ticketDisplay.textContent = ticketCount;  // Update ticket display every ticketInterval ms
                }, ticketInterval);  // Update tickets every 1000 ms (slower pace)
            </script>
        """)
        
# Create the app object
app = App(app_ui, server)

if __name__ == "__main__":
    app.run()