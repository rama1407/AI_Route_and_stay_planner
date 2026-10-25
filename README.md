# AI Travel Planner & Sightseeing Finder

An educational Streamlit application for exploring tourist attractions in India and building estimated single-city or multi-city itineraries. It combines prepared city, attraction, and hotel datasets with geographic distance calculations and itinerary heuristics. It is a planning aid, not a booking service or a source of live travel information.

> **Before publishing:** The current hotel CSV files have unresolved email-pattern matches and their redistribution permissions have not been verified. In particular, `hotels_final.csv` is required by the application but must not be committed publicly until the data has been reviewed, sanitized where appropriate, and cleared for redistribution. See [Dataset privacy and licensing](#dataset-privacy-and-licensing).

## Problem statement

Planning a sightseeing trip can involve comparing attractions, estimating travel between locations, and arranging visits across multiple days or cities. This project demonstrates how prepared travel data and geographic heuristics can support that planning process in one interactive application.

## Project objectives

- Provide an interactive way to browse attractions and hotel records.
- Group nearby attractions and estimate distances from their coordinates.
- Produce a practical, day-wise sightseeing schedule from selected places.
- Demonstrate estimated multi-city itinerary planning.
- Provide a travel checklist and downloadable PDF itinerary.
- Make the data preparation and application components understandable for a student project.

## Key features

- Browse and select tourist attractions from the prepared attractions dataset.
- Group attractions geographically using DBSCAN with a haversine distance metric.
- Estimate straight-line distances using the Haversine formula.
- Order visits using a nearest-neighbour-based heuristic.
- Split selected attractions into days and estimate local travel and visit times.
- Plan multi-city trips using estimated distances, transfers, and city order.
- Browse hotel records and rank nearby candidates using rating and distance inputs. These are dataset-based suggestions, not verified endorsements or bookings.
- Use the Smart Travel Checklist. Its checked and custom items are held in Streamlit session state and are not permanently stored by this application.
- Download a generated itinerary PDF. The PDF is created in memory when requested.

## Technologies used

- Python
- Streamlit for the interactive web UI
- Pandas and NumPy for tabular data and numeric/geographic calculations
- scikit-learn for DBSCAN clustering
- ReportLab for PDF generation
- CSV files for prepared city, attraction, hotel, and optional enrichment data

The application modules also use Python standard-library functionality. The preprocessing notebooks use additional tools and external data services; those are not required to launch the Streamlit app.

## Project architecture

| File or folder | Purpose |
| --- | --- |
| `app.py` | Streamlit entry point, page rendering, data loading, and single-/multi-city user flows. |
| `planner_lib.py` | Loads `hotels_final.csv`; implements Haversine distance, attraction clustering, hotel ranking, attraction ordering, day splitting, and simulated room availability. |
| `multi_city_planner.py` | Estimates inter-city distances/transfers, orders cities, allocates trip dates, and schedules transfer days. |
| `travel_checklist.py` | Renders the checklist page using Streamlit session state. |
| `pdf_generator.py` | Generates downloadable itinerary PDFs in memory with ReportLab; no separate PDF template is required. |
| `.streamlit/config.toml` | Optional Streamlit theme configuration. |
| `assets/` | Optional local city and attraction images. Their rights and attribution must be checked before public distribution. |
| `tests/` | Development tests; not needed to run the application. |
| `backend/` | Contains schemas and a separate backend requirements file. It is not imported by the current Streamlit application. |

The CSV paths in the application are relative to the working directory. Run the launch command from the project root.

## Datasets

The app reads the following files directly:

| File | Role |
| --- | --- |
| `cities.csv` | Required city keys, names, coordinates, attraction counts, nearby hotel counts, and planning limits. |
| `attractions_geo.csv` | Required prepared attraction data, including locations and fields used for filtering and itinerary scheduling. |
| `hotels_final.csv` | Required prepared hotel data used by `planner_lib.py` to browse and rank hotel candidates and estimate room availability. This file is currently subject to the privacy and licensing gate below. |

The following files are optional enrichments: `cities_supplement.csv`, `attractions_supplement.csv`, `destination_links.csv`, `destination_links_supplement.csv`, and `attraction_image_manifest.csv`. The app checks for these files and continues without them, with fewer entries, links, or local-image matches as applicable. It also checks for optional `image_override.csv` and `image_links.csv`; those files are not currently present.

The notebooks use source datasets such as `goibibo.csv`, `places.csv`, and `Top Indian Places to Visit.csv`, plus intermediate geocoding, Wikipedia, and preprocessing outputs. These are not required to launch the app. Keep them only if needed for a documented reproduction workflow and only after reviewing their contents and redistribution terms. The current repository does not establish licenses for those source datasets.

## Setup

The source uses built-in generic type annotations such as `list[str]`, so Python 3.9 or newer is indicated by the code. A specific Python version has not been tested or documented; test in a clean environment before publishing a supported-version claim.

### 1. Create and activate an environment

**Windows PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS or Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install application dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The requirements are currently unpinned. Confirm compatibility with the chosen Python version in a clean environment before pinning package versions.

### 3. Provide the required data

Place `cities.csv`, `attractions_geo.csv`, and a reviewed, sanitized, redistributable `hotels_final.csv` in the project root. The current hotel file is excluded from public tracking while its contents and redistribution rights remain unresolved. Without an approved `hotels_final.csv`, the application cannot start.

### 4. Launch the app

From the project root, run:

```bash
streamlit run app.py
```

No API key or environment variable was identified as necessary for the current Streamlit runtime. Re-running preprocessing notebooks may require internet access to external geocoding or Wikipedia services and must comply with those services' terms.

## Known limitations

- Hotel records and any derived rankings depend on the supplied dataset; they are not live hotel inventory, bookings, or verified current prices.
- Room availability is simulated from room-count and seasonal/weekday assumptions. It is not connected to hotel systems.
- Hotel browsing/ranking is based on stored review and geographic fields; it should not be interpreted as an independently verified recommendation.
- Attraction and hotel coordinates may be incomplete or inaccurate.
- Haversine distances are straight-line estimates. The multi-city planner scales those distances to estimate road distance and transfer time; it does not use traffic-aware routing, road-network routes, transit schedules, or current conditions.
- Estimated travel times and schedules may differ substantially from real-world travel.
- The nearest-neighbour route heuristic is not guaranteed to find the globally shortest route.
- Checklist progress is held in the current Streamlit session and is not permanently saved.
- Preprocessing results can depend on external services, source-data versions, and manual corrections.

## Dataset privacy and licensing

The project audit detected email-pattern matches in `hotel_description` at data rows **1741** and **3768** (row numbers exclude the header) in each of `goibibo.csv`, `cleaned_hotels.csv`, and `hotels_final.csv`. The values are not reproduced here. Because they occur in descriptive text, they may be contact information embedded in hotel descriptions; ownership and context have not been verified, so they cannot safely be treated as harmless false positives.

`planner_lib.py` loads `hotels_final.csv` at import time, so that file is required for the current app to run. Do not publish any of the flagged hotel CSVs until the matches have been reviewed, any sensitive data has been sanitized where appropriate, and permission to redistribute both source and derived data has been confirmed. A `.gitignore` rule is only a safeguard against accidental tracking; it does not sanitize data or grant redistribution rights.

The attraction image manifest records a mix of Wikimedia Commons license labels, user-supplied photos, and Alamy preview entries. Verify and retain attribution and comply with the applicable license for each image; do not distribute images without permission. `assets/city_images/ATTRIBUTION.md` states that the city images are from Unsplash, but retain the attribution note and verify the image sources and applicable rights before publication.

The project files inspected do not establish redistribution permissions for the hotel or original attraction datasets. Review each source's actual license/terms before putting its data in a public repository. Do not infer permission from a dataset being available online or already present locally.

## Data sources and attribution

- `places.csv`, `Top Indian Places to Visit.csv`, and `goibibo.csv` are used as notebook inputs. Their provenance and redistribution licenses are not verified in the project files inspected.
- Preprocessing notebooks call Wikipedia and Nominatim/OpenStreetMap geocoding services. If reproducing or redistributing derived data, check the applicable attribution, licensing, and service-use requirements.
- Image attribution and license metadata are maintained in `attraction_image_manifest.csv` and `assets/city_images/ATTRIBUTION.md`; those records still require review for the flagged image categories.

## Future enhancements

- Add a documented, reproducible data pipeline with source citations and license records.
- Separate approved public sample data from any private or unlicensed source data.
- Add validation for missing or implausible coordinates and clearer uncertainty indicators.
- Integrate licensed road-network or transit routing data for more realistic travel estimates.
- Add user-controlled persistence for checklist and itinerary preferences, with appropriate privacy safeguards.
- Add automated clean-environment setup and tests for supported Python/dependency versions.
