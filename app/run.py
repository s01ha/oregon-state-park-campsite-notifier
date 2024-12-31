import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import json
import math
import argparse
import os

# Base URLs
base_url = "https://oregonstateparks.reserveamerica.com/"
filter_url = base_url + "campsiteFilterAction.do"
page_url = base_url + "campsitePaging.do"
calendar_url = base_url + "campsiteCalendar.do"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def parse_arguments():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Send images to a Telegram chat.')
    parser.add_argument('--bot-token', type=str, required=True, help='The bot token for the Telegram bot.')
    parser.add_argument('--chat-id', type=str, required=True, help='The chat ID to send images to.')

    # Parse the arguments
    return parser.parse_args()

def extract_dates(soup):
    extracted_dates = []  # Initialize list to store dates

    if soup:
        calendar_elements = soup.find_all('div', class_=lambda x: x and 'calendar' in x)

        now = datetime.now()

        for element in calendar_elements:
            current_month = now.month
            current_year = now.year
            current_day = now.day

            date = int(element.find('div', class_='date').text.strip())
            weekday = element.find('div', class_='weekday').text.strip()

            if date >= current_day:
                # Use current month
                pass
            else:
                # Use next month
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1

            formatted_date = datetime(current_year, current_month, date).strftime(f"%Y-%m-%d")
            extracted_dates.append(formatted_date)  # Append to list instead of printing

    return extracted_dates

def extract_sites(soup):
    sites_data = []  # Initialize list to store site information

    if soup:
        site_rows = soup.find_all('div', class_='br')  # Assuming 'siteRow' is the class for site entries

        for site_row in site_rows:
            site_name = site_row.find('div', class_='siteListLabel').get_text(strip=True)
            loop_name = site_row.find('div', class_='loopName').get_text(strip=True)
            status_elements = site_row.find_all('div', class_='status')
            status = [elem.get_text(strip=True) for elem in status_elements]

            site_info = {
                'site_name': site_name,
                'loop': loop_name,
                'status': status,
                'status_num': len(status)
            }
            sites_data.append(site_info)

    return sites_data

# Function to fetch campsite availability for a given park ID, name, and site type
def fetch_campsite_availability(session, park_id, park_name, site_type="TENT SITE", start_date="1990-01-01", end_date="2099-12-31"):

    # Initialize variables
    total_items = 0
    batch_size = 25

    try:
        # Step 1: Load the filter page to set up cookies
        filter_params = {
            "sitefilter": site_type,
            "startIdx": "0",
            "contractCode": "OR",
            "parkId": park_id
        }
        filter_response = session.get(filter_url, params=filter_params)
        filter_response.raise_for_status()

        # Step 2: Load the calendar page for campsite availability
        calendar_params = {
            "page": "calendar",
            "contractCode": "OR",
            "parkId": park_id,
            "sitepage": "true",
            "startIdx": "0"
        }
        calendar_response = session.get(calendar_url, params=calendar_params)
        calendar_response.raise_for_status()

        # Extract the total number of items
        soup = BeautifulSoup(calendar_response.content, "html.parser")
        total_items_text = soup.find(id="resulttotal_dr_top").text
        total_items = int(total_items_text)

        # Calculate the number of batches needed
        num_batches = math.ceil(total_items / batch_size)

        # Dictionary to store results
        results = {}

        for batch in range(num_batches):
            start_idx = batch * batch_size
            page_params = {
                "contractCode": "OR",
                "parkId": park_id,
                "startIdx": str(start_idx)
            }
            calendar_response = session.get(page_url, params=page_params)
            calendar_response.raise_for_status()

            # Parse the HTML of the calendar page
            soup = BeautifulSoup(calendar_response.content, "html.parser")
            calendar_div = soup.find('div', id='calendar', class_='items')

            dates = extract_dates(calendar_div)
            sites_data = extract_sites(calendar_div)

            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d")

            for site in sites_data:
                available_dates = [datetime.strptime(dates[i], "%Y-%m-%d").strftime("%m/%d (%a)") for i, status in enumerate(site['status']) if status == 'A' and start_datetime <= datetime.strptime(dates[i], "%Y-%m-%d") <= end_datetime]
                print(available_dates)
                if available_dates:
                    # Add site and available dates to results dictionary
                    if site['site_name'] not in results:
                        results[site['site_name']] = available_dates
                    else:
                        results[site['site_name']].extend(available_dates)

        # Load previous JSON file
        file_name = os.path.join(SCRIPT_DIR, f"park_{park_id}_{site_type.replace(' ', '-')}_availability.json")
        print(f"Save file: {file_name}")

        try:
            with open(file_name, 'r') as json_file:
                previous_results = json.load(json_file)
        except FileNotFoundError:
            previous_results = {}

        changes_detected = False
        changes_messages = []
        dates_messages = []

        # Compare current data with previous data
        for site_name, current_dates in results.items():
            site_messages = []
            if site_name in previous_results:
                site_changed = False

                # If site existed previously
                previous_dates = set(previous_results[site_name])
                current_dates_set = set(current_dates)

                # Check for removed dates
                removed_dates = previous_dates - current_dates_set
                if removed_dates:
                    changes_detected = True
                    site_changed = True
                    site_messages.extend([f"- {site_name} 사이트의 날짜 {date}가 없어졌습니다." for date in removed_dates])

                # Check for new dates
                new_dates = current_dates_set - previous_dates
                if new_dates:
                    changes_detected = True
                    site_changed = True
                    site_messages.extend([f"+ {site_name} 사이트에 새로운 날짜 {date}가 나왔습니다." for date in new_dates])

                if site_changed:
                    dates_messages.append(f"✖ {site_name} 사이트의 예약 가능 날짜: {', '.join(current_dates)}")
            else:
                # If site is new
                if current_dates:
                    changes_detected = True
                    site_messages.append(f"+ 새로운 사이트 {site_name}의 날짜 {', '.join(current_dates)}가 나왔습니다.")
                    dates_messages.append(f"✖ {site_name} 사이트의 예약 가능 날짜: {', '.join(current_dates)}")

            changes_messages.extend(site_messages)

        # Check for sites that existed previously but not currently
        for site_name in previous_results:
            if site_name not in results:
                changes_detected = True
                changes_messages.append(f"- {site_name} 사이트가 사라졌습니다.")

        # Print change messages
        for message in changes_messages:
            print(message)

        # Print available dates messages
        for message in dates_messages:
            print(message)

        # Save results to JSON file
        with open(file_name, 'w') as json_file:
            json.dump(results, json_file, indent=4)

        if not changes_detected:
            print("변경 사항이 없습니다.")
        else:
            print(f"Results saved to {file_name}")

        if not changes_messages and not dates_messages:
            return None
        else:
            output_messages = "\n".join(changes_messages + dates_messages)
            return output_messages

        return output_messages


    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {park_name} (ID: {park_id}): {str(e)}")
        return None

def escape_markdown(text):
    """Escape markdown special characters"""
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])

def main() -> None:

    args = parse_arguments()

    BOT_TOKEN = args.bot_token
    CHAT_ID = args.chat_id

    # Load the park_info data from the JSON file
    park_info_file = os.path.join(SCRIPT_DIR, 'park_info.json')
    with open(park_info_file, 'r') as json_file:
        park_info = json.load(json_file)

    # Use the loaded park_info data
    print(park_info)

    # Session to handle cookies
    session = requests.Session()

    # Loop through each park info and fetch availability
    for park in park_info:
        park_id = park["park_id"]
        park_name = park["park_name"]
        site_type = park.get("site_type", "TENT SITE")
        start_date = park.get("start_date", "1900-01-01")
        end_date = park.get("end_date", "2099-12-31")
        print(f"Fetching availability for {park_name} / {start_date} ~ {end_date} (ID: {park_id}, TYPE: {site_type})...")
        messages = fetch_campsite_availability(session, park_id, park_name, site_type, start_date, end_date)

        if messages is not None:
            
            # Assuming start_date and end_date are defined elsewhere in the code
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d")

            # Check if start_date and end_date are not the default values
            if start_datetime != datetime(1900, 1, 1) and end_datetime != datetime(2099, 12, 31):
                date_range = f" | {start_datetime.strftime('%m/%d (%a)')} ~ {end_datetime.strftime('%m/%d (%a)')}"
            else:
                date_range = ""

            title = f"{park_name} ({park_id}) | {site_type}{date_range}\n"
            full_message = title + messages
            # Send the full_message to the Telegram chat in Markdown format
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": full_message
            }
            response = requests.post(url, data=data)
            response.raise_for_status()

        time.sleep(1)  # Add a small delay to be gentle on the server

    # Close the session
    session.close()

if __name__ == "__main__":
    main()