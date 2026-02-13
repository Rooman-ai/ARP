import pandas as pd
import os

# File path
file_path = "C:/Users/hp/Documents/ARP_sheets.xlsx"

# Read all sheets
all_sheets = pd.read_excel(file_path, sheet_name=None)

# Desired CSV names (in order)
csv_names = ["Renewals", "Totals", "New_leases"]

# Output folder (optional - keeps files organized)
output_folder = "output_csv"

# Create folder if not exists
os.makedirs(output_folder, exist_ok=True)


# Loop through sheets and save as CSV
for (sheet, df), csv_name in zip(all_sheets.items(), csv_names):

    # Basic cleaning
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")
    df.columns = df.columns.str.strip()

    # Print preview
    print(f"\nSheet: {sheet}")
    print(df.head())

    # Save as CSV
    output_path = os.path.join(output_folder, f"{csv_name}.csv")

    df.to_csv(output_path, index=False)

    print(f"Saved: {output_path}")


print("\nAll files saved successfully!")
