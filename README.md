# OSRM Route Validator

A web application for validating OSRM routes by detecting significant distances between requested destinations and actual route endpoints.

## Key Features

- Store-DC mapping data upload and preparation
- OSRM route validation using multiple routing profiles
- Validation result analysis with visualizations and interactive map
- Problematic route detection based on distance threshold
- Result export in CSV format
- Custom OSRM API parameter configuration

## Installation

### Prerequisites

- Python 3.8 or newer
- pip (Python package manager)

### Installation Steps

1. Clone this repository or download as zip
   git clone
   cd osrm-validator

2. Create a virtual environment (optional but recommended)
   python -m venv venv

3. Activate virtual environment
   - Windows:
     venv\Scripts\activate

- macOS/Linux:
  source venv/bin/activate

4. Install required dependencies
   pip install -r requirements.txt

## Running the Application

1. Ensure your virtual environment is activated (if using one)

2. Run the Streamlit application
   streamlit run app.py

3. The application will open automatically in your web browser (typically at http://localhost:8501)

## Usage Workflow

1. In the "Data Upload & Preparation" tab:

   - Upload your CSV store-DC mapping file or All Locations & Consolidated Stores files
   - Process and clean the data

2. In the "OSRM Validation" tab:

   - Configure OSRM API settings (base URL, access token, profiles)
   - Set validation parameters (batch size, thread workers, etc.)
   - Run route validation

3. In the "Analysis" tab:
   - View validation statistics
   - Analyze distance distribution
   - Identify problematic routes with interactive map
   - Download results

## Input Data Formats

### Store-DC Mapping Format

CSV file with the following columns:

- `store_location`: Store location name
- `store_number`: Store number
- `dc_location`: Distribution center location name
- `dc_code`: Distribution center code
- `origin_lon`: Origin longitude (DC)
- `origin_lat`: Origin latitude (DC)
- `dest_lon`: Destination longitude (Store)
- `dest_lat`: Destination latitude (Store)

### All Locations Format

CSV file with the following columns:

- `Store Location`: Location name
- `Store Code`: Location code
- `Lat `: Latitude
- `Long`: Longitude

### Consolidated Stores Format

CSV file with the following columns:

- `StoreName`: Store name
- `StoreNumber`: Store number
- `LoadingDepot`: Loading depot code
- `Latitude`: Store latitude
- `Longitude`: Store longitude

## Troubleshooting

- If the application fails to run, ensure all dependencies are installed
- If OSRM validation fails, check your internet connection and OSRM API availability
- For other issues, please open an issue on the GitHub repository
  Installation Guide
  Step 1: Create Project Structure
  bash# Create main project directory
  mkdir -p osrm-validator
  cd osrm-validator

# Create folder structure

mkdir -p config utils modules/data_cleaning modules/osrm modules/analysis ui

# Create **init**.py files in each module directory

touch config/**init**.py utils/**init**.py modules/**init**.py
touch modules/data_cleaning/**init**.py modules/osrm/**init**.py modules/analysis/**init**.py ui/**init**.py
Step 2: Set Up Virtual Environment
bash# Create a virtual environment
python -m venv venv

# Activate virtual environment

# On Windows:

venv\Scripts\activate

# On macOS/Linux:

source venv/bin/activate

# Create requirements.txt

cat > requirements.txt << EOF
streamlit>=1.12.0
pandas>=1.4.0
numpy>=1.22.0
requests>=2.27.1
polyline>=1.4.0
matplotlib>=3.5.1
seaborn>=0.11.2
tqdm>=4.62.3
folium>=0.12.1
streamlit-folium>=0.6.15
EOF

# Install required dependencies

pip install -r requirements.txt

The application will automatically open in your default web browser at http://localhost:8501.
Key Features of the Implementation

User Customizable Parameters:

OSRM API settings (base URL, access token)
Routing profiles with editable name/value pairs
Validation parameters (batch size, workers, etc.)
Distance threshold for problematic route detection

Modular Architecture:

Separated data cleaning, validation, and analysis modules
Reusable utility functions in a dedicated module
Well-organized UI components
Maintainable and extensible code structure

Complete Workflow:

Data uploading and cleaning
OSRM route validation with progress tracking
Comprehensive analysis with visualizations
Interactive map for problematic routes
Export functionality for results
