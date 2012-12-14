Readme
========


To run the server, go into the top-level directory and run

python movie_service.py

===============================================================================

Use Cases:

# Getting XML representation of school with id 360008304305
curl -L -H "Accept: application/xml" 127.0.0.1:8888/schools/360008304305

# Getting JSON representation of school with id 360008304305
curl -L -H "Accept:application/json" 127.0.0.1:8888/schools/360008304305

# Getting XML representation of list of schools
curl -L -H "Accept:application/xml" 127.0.0.1:8888/schools

# Getting JSON representation of list of schools
curl -L -H "Accept: application/json" 127.0.0.1:8888/schools

===============================================================================

View SAT Data:
- Navigate to the Charts Visualization Page (http://127.0.0.1:8888/)
- Below will be as scatterplot plotting the average SAT score (either Math, Critical Reading, or Writing) against some metric (i.e. Total Students, %Male Students, etc.). The SAT score is the Y-Axis while the Metric serves as the X-Axis. 
- To the left of the scatterplot is a configurator. This tool allows the user to change the particular SAT section being assessed and the metric the scores are compared to. 
- The user can drilldown by region by selecting the region dropdown menu. Selecting a region will only display data points from schools in that region. 
- To view the scatterplot data as a table, select the “View Data as Table” link or scroll down to the bottom of the Charts Visualization Page. The table displays each school’s name, the specified SAT section, and the specified metric. The table columns are sortable. 
- Additionally, the table is paginated only displaying 10 tuples from the table at a time. Click the “Prev”/‘Next” button to navigate through the table records. 

Browse Schools:
- Navigate to the Browse Schools Page (http://127.0.0.1:8888/regions).
- Below will be a list of regions within NYC (i.e. Brooklyn, Staten Island).
- Click on a Region to view the list of schools located in that particular region.
- Clicking on the name of a school from the Region’s school list will navigate the user to the school’s information page.

View All Schools: 
- Navigate to the Browse Schools Page (http://127.0.0.1:8888/regions).
- Before the list of regions is a link: “View All NYC Schools”.
- Clicking this link displays all the available schools in NYC.
- Clicking on the name of a school from the All Schools list will navigate the user to the school’s information page. 


View individual schools given the NCES number:
-Type in the browser (http://127.0.0.1:8888/schools/NCES#).
-View the general information of the school (a static map image is include).
-View the statistical data (AP scores, SAT scores) and the demographic information of the students at the school.