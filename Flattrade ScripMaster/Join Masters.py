import pandas as pd
import os
import glob
import time

# Folder containing input files
input_folder = r'C:\API'

# Output file path
output_file = r'C:\API\ScripMaster.csv'

# Step 1: Delete output file if it exists
if os.path.exists(output_file):
    print(f"Deleting existing file: {output_file}")
    os.remove(output_file)

# Step 2: Get list of all files ending with 'Master.csv' in input folder
input_files = glob.glob(os.path.join(input_folder, '*Master.csv'))

# Step 3: Join all matching files and remove duplicates
def join_files(input_files, output_file):
    combined_df = pd.DataFrame()

    for file in input_files:
        print(f"Reading: {file}")
        df = pd.read_csv(file)
        combined_df = pd.concat([combined_df, df], ignore_index=True)

    if not combined_df.empty:
        # Remove duplicates based on the 'Token' column
        combined_df.drop_duplicates(subset='Token', inplace=True)
        
        combined_df.to_csv(output_file, index=False)
        print(f"Combined file saved as {output_file} (duplicates removed based on 'Token')")
    else:
        print("No matching input files found. No output generated.")

join_files(input_files, output_file)

# Optional delay before exit
time.sleep(3)
