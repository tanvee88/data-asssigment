import polars as pl
import plotnine as p9
import geopandas as gpd
import pandas as pd

# Load the data
indicator_df = pl.read_csv("unicef_indicator_1.csv")
metadata_df = pl.read_csv("unicef_metadata.csv")

# Filter indicator for Total sex and rename columns for clarity
ind_clean = indicator_df.filter(
    pl.col("sex") == "Total"
).select(
    ["country", "alpha_3_code", "time_period", "obs_value"]
).rename({
    "time_period": "year",
    "obs_value": "infant_mortality_rate"
})

# Select relevant columns from metadata
meta_clean = metadata_df.select(
    ["alpha_3_code", "year", 
     "Population, total", 
     "GDP per capita (constant 2015 US$)", 
     "Life expectancy at birth, total (years)"]
).rename({
    "Population, total": "population",
    "GDP per capita (constant 2015 US$)": "gdp_per_capita",
    "Life expectancy at birth, total (years)": "life_expectancy"
})

# Join the datasets
merged_df = ind_clean.join(
    meta_clean, 
    on=["alpha_3_code", "year"], 
    how="inner"
)

# Convert to pandas for plotnine and geopandas compatibility
df_pd = merged_df.to_pandas()

# Filter for 2020
df_2020 = df_pd[df_pd['year'] == 2020]

# Load world map data
import urllib.request
import tempfile
import zipfile
import os

url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
temp_dir = tempfile.mkdtemp()
zip_path = os.path.join(temp_dir, "ne.zip")
urllib.request.urlretrieve(url, zip_path)
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(temp_dir)
world = gpd.read_file(os.path.join(temp_dir, "ne_110m_admin_0_countries.shp"))
world = world.rename(columns={'ADM0_A3': 'iso_a3'})

# Merge map data with our dataset
world_merged = world.merge(df_2020, left_on='iso_a3', right_on='alpha_3_code', how='left')

# Plot using plotnine
map_plot = (
    p9.ggplot(world_merged)
    + p9.geom_map(p9.aes(fill='infant_mortality_rate'), color='white', size=0.1)
    + p9.scale_fill_cmap(cmap_name='OrRd', na_value='lightgrey')
    + p9.theme_minimal()
    + p9.labs(
        title="Global Infant Mortality Rate (2020)",
        fill="Deaths per 1,000 live births"
    )
    + p9.theme(
        figure_size=(10, 6),
        panel_grid=p9.element_blank(),
        axis_text=p9.element_blank(),
        axis_ticks=p9.element_blank()
    )
)
map_plot.save("chart_1_map.png", width=10, height=6, dpi=300)

top_15 = df_2020.nlargest(15, 'infant_mortality_rate').copy()
top_15['country'] = pd.Categorical(top_15['country'], categories=top_15['country'][::-1], ordered=True)

bar_plot = (
    p9.ggplot(top_15, p9.aes(x='country', y='infant_mortality_rate', fill='infant_mortality_rate'))
    + p9.geom_col()
    + p9.coord_flip()
    + p9.scale_fill_cmap(cmap_name='OrRd')
    + p9.theme_minimal()
    + p9.labs(
        title="Top 15 Countries by Infant Mortality Rate (2020)",
        x="",
        y="Deaths per 1,000 live births",
        fill="Rate"
    )
)
bar_plot.save("chart_2_bar.png", width=8, height=6, dpi=300)

scatter_plot = (
    p9.ggplot(df_2020.dropna(subset=['gdp_per_capita', 'infant_mortality_rate']), 
              p9.aes(x='gdp_per_capita', y='infant_mortality_rate'))
    + p9.geom_point(alpha=0.6, color='blue')
    + p9.geom_smooth(method='lm', color='red', se=False)
    + p9.scale_x_log10()
    + p9.theme_minimal()
    + p9.labs(
        title="GDP per capita vs Infant Mortality Rate (2020)",
        x="GDP per capita (Constant 2015 US$, Log Scale)",
        y="Infant Mortality Rate"
    )
)
scatter_plot.save("chart_3_scatter.png", width=8, height=6, dpi=300)

selected_countries = ['United States', 'India', 'Nigeria', 'Brazil', 'Germany']
df_selected = df_pd[df_pd['country'].isin(selected_countries)]

time_series_plot = (
    p9.ggplot(df_selected, p9.aes(x='year', y='infant_mortality_rate', color='country'))
    + p9.geom_line(size=1)
    + p9.geom_point(size=1.5)
    + p9.theme_minimal()
    + p9.labs(
        title="Infant Mortality Trends (1960 - 2020)",
        x="Year",
        y="Infant Mortality Rate",
        color="Country"
    )
)
time_series_plot.save("chart_4_timeseries.png", width=8, height=6, dpi=300)
