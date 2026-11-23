import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

# --- Configuration ---
# The name of your metadata file
METADATA_FILE_XLSX = "Data About Data - MetaData.xlsx"
METADATA_FILE_CSV = "Data About Data - MetaData.xlsx - Sheet1.csv"

# --- 1. Load Metadata ---
if os.path.exists(METADATA_FILE_XLSX):
    print(f"Loading metadata from {METADATA_FILE_XLSX}...")
    try:
        # reading the first sheet by default
        meta_df = pd.read_excel(METADATA_FILE_XLSX, sheet_name=0) 
    except ImportError:
        print("Error: 'openpyxl' library is missing. Install it via: pip install openpyxl")
        exit()
elif os.path.exists(METADATA_FILE_CSV):
    print(f"Loading metadata from {METADATA_FILE_CSV}...")
    meta_df = pd.read_csv(METADATA_FILE_CSV)
else:
    print("Error: Could not find the metadata file.")
    print(f"Checked for: '{METADATA_FILE_XLSX}' and '{METADATA_FILE_CSV}'")
    exit()

# Ensure we access the first column for station names, regardless of column header name
station_column_name = meta_df.columns[0]
print(f"Station column identified as: '{station_column_name}'")

# --- 2. Process Each Station ---
root_dir = os.getcwd()

for index, row in meta_df.iterrows():
    station_folder_name = str(row[station_column_name]).strip()
    
    print(f"Processing Station: {station_folder_name}...")
    
    station_path = os.path.join(root_dir, station_folder_name)
    
    # Check if the station folder exists
    if not os.path.exists(station_path):
        print(f"  [Warning] Folder not found: {station_path}")
        continue

    # Find all CSV files in the folder
    csv_files = glob.glob(os.path.join(station_path, "*.csv"))
    
    if not csv_files:
        print(f"  [Warning] No CSV files found in {station_folder_name}")
        continue

    station_data_list = []

    # --- 3. Join CSV Files ---
    for file_path in csv_files:
        try:
            # Updated: header=0 based on your sample file
            df = pd.read_csv(file_path, header=0)
            
            # Optional: Standardize column names (strip whitespace)
            df.columns = [c.strip() for c in df.columns]
            
            # Keep only relevant columns to save memory
            # We verify if columns exist to avoid errors if format varies slightly
            cols_of_interest = ['Timestamp', 'PM2.5 (µg/m³)', 'PM10 (µg/m³)']
            existing_cols = [c for c in cols_of_interest if c in df.columns]
            
            if 'Timestamp' in existing_cols:
                station_data_list.append(df[existing_cols])
            else:
                 print(f"  [Skipping] File missing 'Timestamp' column: {os.path.basename(file_path)}")

        except Exception as e:
            print(f"  Error reading file {os.path.basename(file_path)}: {e}")

    if not station_data_list:
        print("  No valid data found to combine.")
        continue

    # Combine all data for this station
    combined_df = pd.concat(station_data_list, ignore_index=True)

    # --- 4. Clean and Prepare Data ---
    # Convert Timestamp
    combined_df['Timestamp'] = pd.to_datetime(combined_df['Timestamp'], errors='coerce')
    
    # Drop rows with invalid timestamps
    combined_df = combined_df.dropna(subset=['Timestamp'])
    
    # Sort by time
    combined_df = combined_df.sort_values('Timestamp')

    # Convert PM values to numeric (coerces 'N/A' or 'None' to NaN)
    if 'PM2.5 (µg/m³)' in combined_df.columns:
        combined_df['PM2.5 (µg/m³)'] = pd.to_numeric(combined_df['PM2.5 (µg/m³)'], errors='coerce')
    if 'PM10 (µg/m³)' in combined_df.columns:
        combined_df['PM10 (µg/m³)'] = pd.to_numeric(combined_df['PM10 (µg/m³)'], errors='coerce')

    # --- 5. Plot Graphs ---
    # Creating 2 subplots (graphs) in one figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    
    # Plot PM2.5
    if 'PM2.5 (µg/m³)' in combined_df.columns:
        ax1.plot(combined_df['Timestamp'], combined_df['PM2.5 (µg/m³)'], color='tab:blue', linewidth=0.8)
        ax1.set_title(f"{station_folder_name} - PM2.5 Levels")
        ax1.set_ylabel("PM2.5 (µg/m³)")
        ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Plot PM10
    if 'PM10 (µg/m³)' in combined_df.columns:
        ax2.plot(combined_df['Timestamp'], combined_df['PM10 (µg/m³)'], color='tab:orange', linewidth=0.8)
        ax2.set_title(f"{station_folder_name} - PM10 Levels")
        ax2.set_ylabel("PM10 (µg/m³)")
        ax2.set_xlabel("Timestamp")
        ax2.grid(True, linestyle='--', alpha=0.7)
    else:
        ax2.text(0.5, 0.5, 'No PM10 Data Available', horizontalalignment='center', verticalalignment='center', transform=ax2.transAxes)

    plt.tight_layout()
    
    # Save the plot
    safe_name = station_folder_name.replace(" ", "_").replace(",", "").replace("-", "_")
    output_filename = f"Graph_{safe_name}.png"
    plt.savefig(output_filename)
    print(f"  Graph saved: {output_filename}")
    
    plt.close(fig)

print("Processing complete.")