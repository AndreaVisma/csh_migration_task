# Insights from the American Community Survey (ACS): metro area-to-metro area migration flows 2015-19

The code stored here downloads the ACS survey data on metro area to metro area migration flows (https://www.census.gov/data/tables/2019/demo/geographic-mobility/metro-to-metro-migration.html), 
processes them and produces some charts and insights used to compile a small report for the Complexity Science Hub.

### The structure of the repository is the following: 
(NB, the codes are to be run in order)
- **1_download_survey_data** : downloads the ACS data, does some processing and stores a few dataframes for different features of the data
- **2_plot_maps**: plots the inflows and outflows maps and distribution charts, and the chart on the correlation between inflow nad permanent population size of each MSA
- **3_movement_distance**: plots the chord chart of migration flow from macro geographic areas, calculates migration distance and produces the relative boxplot
