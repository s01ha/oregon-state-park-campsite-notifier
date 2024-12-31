# Oregon State Park Campsite Notifier

This program checks the availability of campsites in Oregon State Parks and sends notifications to a Telegram chat.

## Usage

### Prerequisites

- Docker
- Docker Compose

### Setup

1. Clone the repository:
    ```sh
    git clone https://github.com/amoros/oregon-state-park-campsite-notifier.git
    cd oregon-state-park-campsite-notifier
    ```

2. Create and configure the `.env` file with your Telegram bot token and chat ID:
    ```sh
    BOT_TOKEN=your_bot_token
    CHAT_ID=your_chat_id
    ```

    - **Telegram Bot Token**: You can obtain the bot token by creating a new bot on Telegram using the [BotFather](https://core.telegram.org/bots#botfather).
    - **Chat ID**: You can obtain the chat ID by starting a chat with your bot and then using the [Telegram API](https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates) to get the chat ID from the updates.

3. Configure the `park_info.json` file to specify which state parks will be checked:
    ```json
    [
        {"park_id": "402235", "park_name": "Silver Falls State Park"},
        {"park_id": "402486", "park_name": "Tumalo State Park"},
        {"park_id": "402446", "park_name": "Cove Palisades State Park"},
        {"park_id": "402241", "park_name": "Detroit Lake State Recreation Area"},
        {"park_id": "402155", "park_name": "Beachside State Recreation Site"},
        {"park_id": "402461", "park_name": "Prineville Reservoir State Park"},
        {"park_id": "402479", "park_name": "LaPine State Park"},
        {"park_id": "402267", "park_name": "Memaloose State Park", "site_type": "TENT SITE"},
        {"park_id": "402465", "park_name": "Deschutes River State Recreation Area", "site_type": "PRIMITIVE"}
    ]
    ```

    - **park_id**: You can find the `park_id` in the URL when you visit the park's page on the reservation website. For example, the URL for Silver Falls State Park is:
      ```
      https://oregonstateparks.reserveamerica.com/camping/silver-falls-state-park/r/campgroundDetails.do?contractCode=OR&parkId=402235
      ```
      Here, the `parkId` parameter (`402235`) is what you set as the `park_id` in `park_info.json`.
    - **site_type**: Follow the campsite type selection options available on the reservation website.

### Running the Program

1. Build and run the Docker container using Docker Compose:
    ```sh
    docker-compose up -d --build
    ```

### Configuration

- **Interval of Running**: You can set the interval of running by changing the crontab file inside the Docker container. The default interval is set to 10 minutes.
- **Telegram Bot Token and Chat ID**: Set these in the `.env` file.
- **State Parks to Check**: Configure the `park_info.json` file to specify which state parks will be checked.

### Notes

- Ensure that the Docker daemon is running before executing the Docker Compose commands.
- The program will send notifications to the specified Telegram chat whenever there are changes in campsite availability.

For more information, refer to the source code and comments within the files.

## Donate

If you find this project useful, consider making a donation to support its development:

[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.com/donate/?business=YUHM53ZPKE6WN&no_recurring=0&item_name=Support+the+Developer%21+%E2%98%95+Buy+me+a+coffee+and+help+fuel+more+great+work%21&currency_code=USD)