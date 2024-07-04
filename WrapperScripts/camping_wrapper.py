import subprocess
import time
from datetime import datetime
import argparse
import sys

# Function to run the camping.py script and get the output
def run_camping_script(start_date, end_date, parks, nights):
    cmd = [
        "python3", "camping.py",
        "--start-date", start_date,
        "--end-date", end_date,
        "--parks"
    ] + parks + ["--nights", str(nights), "--show-campsite-info"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    # print("Raw output from camping.py:\n", result.stdout)  # Debug print
    return result.stdout

# Function to parse the output of the camping.py script
def parse_campsite_info(output):
    lines = output.split('\n')
    campsite_info = {}
    campground = None
    current_site = None

    for line in lines:
        if 'site(s) available out of' in line:
            campground = line.split(":")[0].strip()
            # print("Campground identified:", campground)  # Debug print
        elif '* Site' in line and campground:
            parts = line.split()
            current_site = parts[2]
            # print("Site identified:", current_site)  # Debug print
        elif current_site and 'available on the following dates' not in line:
            dates = line.split()
            for date in dates:
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    date_str = date_obj.strftime("%Y-%m-%d")
                    # print("Parsed site and date:", current_site, date_str)  # Debug print
                    if date_str not in campsite_info:
                        campsite_info[date_str] = []
                    campsite_info[date_str].append((current_site, campground))
                    # print(f"Added site info: {campground} {current_site} on {date_str}")  # Debug print
                except ValueError:
                    continue  # Ignore parts that are not valid dates
        elif 'available on the following dates' in line:
            continue  # Skip this line

    # print("Parsed campsite info:\n", campsite_info)  # Debug print
    return campsite_info

# Function to format the date and return the information
def format_info(date, site_info):
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    day = date_obj.strftime("%A").upper()
    if day not in ["FRIDAY", "SATURDAY"]:
        # print(f"Skipping {day} {date}")  # Debug print
        return []  # Skip days other than Friday and Saturday
    formatted_date = date_obj.strftime("%Y-%m-%d")
    formatted_info = []
    for site, campground in site_info:
        formatted_info.append((day, formatted_date, site, campground))
    return formatted_info

# Function to print the differences in campsite availabilities
def print_differences(new_info, old_info):
    new_sites = {f"{date} {site}" for date, sites in new_info.items() for site in sites}
    old_sites = {f"{date} {site}" for date, sites in old_info.items() for site in sites}

    added_sites = new_sites - old_sites
    removed_sites = old_sites - new_sites

    all_formatted_info = []

    if added_sites:
        print("Newly available sites:")
        sys.stdout.flush()  # Flush the output buffer
        for site in added_sites:
            parts = site.split(maxsplit=2)
            date = parts[0]
            info = " ".join(parts[1:])
            print(f"Processing added site: {site}, {date}, {info}")  # Debug print
            formatted_info = format_info(date, [(parts[1], parts[2])])
            if formatted_info:  # Check if formatted_info is not empty
                all_formatted_info.extend(formatted_info)

    if removed_sites:
        print("\nNo longer available sites:")
        sys.stdout.flush()  # Flush the output buffer
        for site in removed_sites:
            parts = site.split(maxsplit=2)
            date = parts[0]
            info = " ".join(parts[1:])
            print(f"Processing removed site: {site}, {date}, {info}")  # Debug print
            formatted_info = format_info(date, [(parts[1], parts[2])])
            if formatted_info:  # Check if formatted_info is not empty
                all_formatted_info.extend(formatted_info)

    # Sort all formatted info by campground first, then by date
    all_formatted_info.sort(key=lambda x: (x[3], x[1]))

    # Print the header
    print(f"{'Day':<10} {'Date':<12} {'Site':<10} {'Campground'}")
    sys.stdout.flush()  # Flush the output buffer

    # Print the formatted info
    for line in all_formatted_info:
        day, date, site, campground = line
        print(f"{day:<10} {date:<12} {site:<10} {campground}")
        sys.stdout.flush()  # Flush the output buffer

# Main function to run the wrapper script every 5 minutes
def main():
    parser = argparse.ArgumentParser(description='Check campsite availability.')
    parser.add_argument('--start-date', required=True, help='Start date for the search (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date for the search (YYYY-MM-DD)')
    parser.add_argument('--parks', required=True, nargs='+', help='List of park IDs')
    parser.add_argument('--nights', type=int, default=1, help='Number of nights (default: 1)')
    
    args = parser.parse_args()

    previous_info = {}

    while True:
        output = run_camping_script(args.start_date, args.end_date, args.parks, args.nights)
        current_info = parse_campsite_info(output)
        
        print_differences(current_info, previous_info)
        
        previous_info = current_info
        
        print("\nWaiting for 5 minutes...\n")
        sys.stdout.flush()  # Flush the output buffer
        time.sleep(300)  # Sleep for 5 minutes

if __name__ == "__main__":
    main()

