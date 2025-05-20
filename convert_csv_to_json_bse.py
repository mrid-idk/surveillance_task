import csv
import json
import os

INPUT_FOLDER = "bse_data_files1/csv_files"
OUTPUT_FOLDER = "docs/bse_json"

# Create output folder if it doesn't exist
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def clean_header(header):
    return header.strip().replace("\ufeff", "")  # Remove BOM, extra spaces

def convert_file(input_path, output_path, date_str):
    formatted_date = f"20{date_str[-2:]}-{date_str[2:4]}-{date_str[0:2]}"
    converted = []

    with open(input_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        reader.fieldnames = [clean_header(h) for h in reader.fieldnames]

        # Determine the slice range for desired columns
        start_index = reader.fieldnames.index("ScripId")
        end_column = "High low price variation_150_percentage_12 months"
        end_index = reader.fieldnames.index(end_column) + 1  # +1 because slice is exclusive

        selected_headers = reader.fieldnames[start_index:end_index]

        for row in reader:
            symbol = row.get("ScripId", "").strip()
            if not symbol:
                continue

            item = {"DATE": formatted_date}
            for key in selected_headers:
                item[key] = row.get(key, "").strip()

            converted.append(item)

    with open(output_path, "w", encoding='utf-8') as f:
        json.dump(converted, f, indent=2)

def main():
    index_list = []

    for filename in os.listdir(INPUT_FOLDER):
        if filename.startswith("REG1_IND") and filename.endswith(".csv"):
            date_part = filename.replace("REG1_IND", "").replace(".csv", "")
            input_file = os.path.join(INPUT_FOLDER, filename)
            output_file = os.path.join(OUTPUT_FOLDER, f"IND{date_part}.json")
            convert_file(input_file, output_file, date_part)
            index_list.append(f"bse_json/IND{date_part}.json")

    with open(os.path.join(OUTPUT_FOLDER, "index_bse.json"), "w", encoding='utf-8') as f:
        json.dump(index_list, f, indent=2)

    print(f"✅ Converted {len(index_list)} files. index_bse.json updated.")

if __name__ == "__main__":
    main()
