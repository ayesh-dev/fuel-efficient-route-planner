# Fuel Efficient Route Planner API

A Django REST Framework (DRF) based API that calculates the most cost-effective fueling strategy for a driving route across the USA. Given a start and finish location, the system fetches the route coordinates using OpenRouteService, evaluates fuel stations along the path from a provided dataset, and determines the optimal stops considering vehicle range limits and fuel consumption.

---

##  What This Project Actually Does

1. **Accepts Route Inputs**: Takes starting and destination locations anywhere within the USA (e.g., `New York, NY` to `Los Angeles, CA`).
2. **Fetches Driving Route**: Calls the OpenRouteService API to retrieve driving distance, turn-by-turn waypoints, and route coordinates.
3. **Identifies Fuel Stations**: Cross-references the route geometry with an internal CSV dataset of fuel stations across the USA.
4. **Optimizes Fuel Stops**:
   * Assumes the vehicle has a **maximum range of 500 miles** per full tank (requires refueling before running out).
   * Filters and picks the **cheapest fuel stations** (`Retail Price`) along the route corridor.
5. **Calculates Total Cost**:
   * Uses a fixed fuel efficiency rate of **10 Miles Per Gallon (MPG)**.
   * Computes the total gallons needed and total cost spent on fuel in USD.
6. **Returns JSON Response**: Provides a structured response containing the total distance, total cost, optimal fuel stops, and route summary.

---

##  Features

- **Route Calculation**: Leverages OpenRouteService API to fetch route distance and path coordinates.
- **Cost & Distance Optimization**: Automatically finds stops near the 400–450 mile mark to keep within the 500-mile safety threshold while targeting the lowest gas prices.
- **Custom Data Management Command**: Custom Django command to import and index fuel price CSV data into the database.
- **RESTful Endpoints**: Built with Django REST Framework (DRF) for clean request/response handling.

---

## Tech Stack

- **Framework**: Django & Django REST Framework (DRF)
- **Language**: Python 3.10+
- **Database**: SQLite
- **External API**: OpenRouteService (Routing & Geocoding)
- **Data Handling**: Pandas / Python Standard CSV module

---

## Project Structure

```text
fuel-efficient-route-planner/
│
├── fuel_finder/
│   ├── management/
│   │   └── commands/
│   │       └── import_csv.py       # Command to ingest fuel price dataset into DB
│   ├── models.py                   # FuelStation database model
│   ├── views.py                    # Core API endpoint logic
│   ├── urls.py                     # App API routing
│   └── services.py                 # Routing & fuel optimization algorithm
│
├── fuel_planner/
│   ├── settings.py                 # Configuration & API keys
│   └── urls.py                     # Root URL routing
│
├── fuel-prices-for-be-assessment.csv # CSV dataset of US fuel stations
├── manage.py
├── requirements.txt
└── README.md
