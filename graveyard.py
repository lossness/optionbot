
def click_channel(channel_name: str):
    try:
        channel = WebDriverWait(DRIVER, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//*[@aria-label='{channel_name}']")))
        channel.click()
    except TimeoutException as e:
        raise RuntimeError("Lobby channel not located.")


class Updates:
    def __init__(self, channels):
        self.channels = channels
        self.not_found = True
        self.new_updates = []

    def __call__(self, channel):
        for channel in self.channels:
            try:
                channel_element = WebDriverWait(DRIVER, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, f"//*[@aria-label='{channel}']")))
                if channel_element:
                    self.not_found = True
            except (NoSuchElementException, TimeoutException):
                self.not_found = False
                self.new_updates += channel


def find_channel_updates(channels_list: list) -> bool:
    updates = Updates(channels_list)
    if updates.not_found:
        return False
    if not updates.not_found:
        return True



LOBBY_CHANEL = "lobby (text channel)"

LIVE_CHANNELS = {
    "maria (text channel)": "channels-7",
    "jennyb-riskyaf (text channel)": "channels-9",
    "thuhkang (text channel)": "channels-10"
}
TEST_CHANNELS = {
    "lobby (text channel)": "channels-0",
    "apex-kill-leaderboards (text channel)": "channels-1",
    "bot-dev-talk (text channel)": "channels-2"

def message_tracker():
    # messages variable is a list of elements that contain a message in the chatroom (last 54 messages)
    messages = DRIVER.find_elements_by_xpath("//*[@role='group']")
    for message in messages:
        print(message.text)


def click_server():
    # clicks the server icon
    test_server_name = "vidyagaymers"
    live_server_name = "BlackBox"
    try:
        server = WebDriverWait(DRIVER, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//a[@aria-label='{live_server_name}']")))
        server.click()
    except TimeoutException as e:
        raise RuntimeError("Server icon not located.")

def discord_driver():
    # Chrome setup
    os.startfile(CHROME)
    CHROME_OPTIONS = Options()
    CHROME_OPTIONS.debugger_address = "127.0.0.1:9222"
    driver = webdriver.Chrome(options=CHROME_OPTIONS,
                              executable_path=DRIVER_PATH)
    ACTION = ActionChains(driver)
    return driver

def create_image(trade):
    (in_or_out, ticker, datetime, strike_price, call_or_put, buy_price,
     user_name, expiration) = trade
    expiration = expiration.replace(r'/', '.')
    img = Image.new('RGB', (1080, 1080), color=(73, 109, 137))
    draw = ImageDraw.Draw(img)
    draw.text(
        (100, 100),
        f'{ticker.upper()}: Get {in_or_out.upper()}. Strike price: {strike_price.upper()} Type: {call_or_put.upper()} Price: {buy_price} Expiration: {expiration}',
        fill=(0, 0, 0))
    path = f'{in_or_out}.{ticker}.{strike_price}.{call_or_put}.{expiration}.png'
    img.save(path)
    return path


# def verify_channel_order(channels_dict: dict):
#     for channel_name, channel_position in channels_dict.items():
#         channel_order_ok = False
#         channel_name_ok = False
#         try:
#             channel_element_position = WebDriverWait(DRIVER, 5).until(
#                 EC.presence_of_element_located(
#                     (By.XPATH, f"//*[@id='{channel_position}']")))

#             if channel_element_position:
#                 channel_order_ok = True

#             channel_element_name = WebDriverWait(DRIVER, 5).until(
#                 EC.presence_of_element_located(
#                     (By.XPATH, f"//*[@aria-label='{channel_name}']")))

#             if channel_element_name:
#                 channel_name_ok = True

#         except TimeoutException as e:
#             print(f"{channel_name} not located")
#             continue
#         finally:
#             print(channel_order_ok, channel_name_ok)
#             return (channel_order_ok, channel_name_ok)

        # if "Today" in item:
        #     remove_spaces = re.sub(r" ", "", item)
        #     today_result = re.findall(
        #         r'\d{1,2}(?:(?:am|pm)|(?::\d{1,2})(?:AM|PM)?)',
        #         remove_spaces)
        #     double_split_result.remove(item)

        # with open('NASDAQandNYSE.txt', 'r') as file:
        #     for line in file:
        #         clean_line = line.replace('\n', '')
        #         if clean_line in item:
        #             trade_ticker = clean_line
        # print("done")


# def test_message_grabber():
#     CHATROOM_ELEMENTS_LIST = DRIVER.find_elements_by_xpath(
#         "//*[@role='group']")
#     for message in CHATROOM_ELEMENTS_LIST:
#         for trader in traders:
#             if trader in message.text:
#             if message.text.startswith("In"):
#                 print(message.text)

# def find_new_message():

# a string containing the last 54 messages in the selected text channel (unparsed)
# CHATROOM_TEXT_STRING = DRIVER.find_element_by_xpath("//*[@id='messages']").text
# CHATROOM_ELEMENTS_LIST = DRIVER.find_elements_by_xpath("//*[@role='group']")
# def message_updater():
#    if CHATROOM_TEXT_FULL != DRIVER.find_element_by_xpath("//*[@id='messages']").text:

def login(driver, username, password, login_func, click_server_func, click_channel_func):
    """Logins to the discord server.

    Raises:
        NoSuchEelementException: When the login fields or server button are not loaded
        on the page.
    """
    if login_func:
        print("Already logged in")
        click_server_func()
    else:
        try:
            # login box
            login_username = driver.find_element_by_xpath(
                "//input[@name='email']")
            # password box
            login_password = driver.find_element_by_xpath(
                "//input[@name='password']")
            # types the username and password slowly
            for letter in username:
                login_username.send_keys(letter)
                time.sleep(.5)

            for letter in password:
                login_password.send_keys(letter)
                time.sleep(.5)
            # locates the login button and clicks it
            login_button = driver.find_element_by_xpath(
                "//button[@type='submit']")
            login_button.click()
            click_server_func()
            time.sleep(5)
            click_channel_func(LOBBY_CHANEL)
        except NoSuchElementException as e:
            raise RuntimeError(
                "One or multiple elements in the login process we're not found.")


def login_check(driver) -> bool:
    driver.get("https://discord.com/login")
    try:
        login_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@name='email']")))
        if login_field:
            return False
    except TimeoutException as e:
        return True