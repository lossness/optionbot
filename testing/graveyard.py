
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



# def post_conductor(path, driver):
#     try:
#         upload_element = WebDriverWait(driver, 5).until(
#             EC.presence_of_element_located(
#                 (By.XPATH, "//*[@id='react-root']//button[2]")))
#         upload_element.send_keys('shazam')
#         upload_element.click()
#         time.sleep(.2)
#         pyperclip.copy(path)
#         KEYBOARD.press(Key.ctrl)
#         KEYBOARD.press('v')
#         KEYBOARD.release(Key.ctrl)
#         KEYBOARD.release('v')
#         KEYBOARD.press(Key.enter)
#         KEYBOARD.release(Key.enter)
#         next_button = WebDriverWait(driver, 5).until(
#             EC.presence_of_element_located(
#                 (By.XPATH, "//button[text()='Next']")))
#         next_button.click()
#         share_button = WebDriverWait(driver, 5).until(
#             EC.presence_of_element_located(
#                 (By.XPATH, "//button[text()='Share']")))
#         share_button.click()
#         #caption_field = WebDriverWait(driver, 5).until(
#         #    EC.presence_of_element_located((By.XPATH, "//textarea")))
#     finally:
#         driver.quit()


def insta_login(driver):
    try:
        login_username = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//input[@name='username']")))

        login_password = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//input[@name='password']")))
        for letter in INSTA_USERNAME:
            login_username.send_keys(letter)
            sleep_time = random.random()
            time.sleep(sleep_time)

        for letter in INSTA_PW:
            login_password.send_keys(letter)
            sleep_time = random.random()
            time.sleep(sleep_time)

        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//button[@type='submit']")))
        sleep_time = random.uniform(1.1, 2.9)
        time.sleep(sleep_time)
        login_button.click()
        print("Logged into instagram successfully.")
    except TimeoutException:
        print("Already logged into instagram.")


# def collect_match(trade:tuple, trades_list:list):
#     (in_or_out, ticker, strike_price, user_name, expiration) = trade
#     ticker = ticker.lower()
#     matched_trades = re.findall(
#                 rf'\(((?:[\'in\', \'out\'])+, (\'{ticker}\'), (\'{strike_price}\'), (\'{user_name}\'), (\'{expiration}\'))\)',
#                 str(trades_list))

# def complete_trade_match():
#     try:
#         con = db_connect()
#         cur = con.cursor()
#         filtered_trade_sql = "SELECT in_or_out, ticker, strike_price, user_name, expiration from trades"
#         cur.execute(filtered_trade_sql)
#         filtered_trades = cur.fetchall()
#         matched_trades_list = []
#         for trade in filtered_trades:
#             (in_or_out, ticker, strike_price, user_name, expiration) = trade
#             ticker = ticker.lower()
#             matched_trades = re.findall(
#                 rf'\(((?:[\'in\', \'out\'])+, (\'{ticker}\'), (\'{strike_price}\'), (\'{user_name}\'), (\'{expiration}\'))\)',
#                 str(filtered_trades))
#             if len(matched_trades) == 2:
#                 # delete_matched_trade_sql = "DELETE from trades WHERE (ticker, strike_price, user_name, expiration) = (?, ?, ?, ?)"
#                 # cur.execute(delete_matched_trade_sql,
#                 #             (ticker, strike_price, user_name, expiration))
#                 # con.commit()
#                 matched_trades_list.append(
#                     (matched_trades[0][0], matched_trades[1][0]))
#         return matched_trades_list

#     except ValueError:
#         pass

#     finally:
#         if (con):
#             con.close()
#             print('Trade match search completed')


def switch_to_mobile(driver):
    time.sleep(1)
    KEYBOARD.press(Key.ctrl)
    KEYBOARD.press(Key.shift)
    KEYBOARD.press('j')
    KEYBOARD.release(Key.ctrl)
    KEYBOARD.release(Key.shift)
    KEYBOARD.release('j')
    time.sleep(1)
    KEYBOARD.press(Key.ctrl)
    KEYBOARD.press(Key.shift)
    KEYBOARD.press('m')
    KEYBOARD.release(Key.ctrl)
    KEYBOARD.release(Key.shift)
    KEYBOARD.release('m')
    driver.refresh()
    driver.get('https://www.instagram.com/marginkings/')
    time.sleep(1)
    KEYBOARD.press(Key.ctrl)
    KEYBOARD.press(Key.shift)
    KEYBOARD.press('j')
    KEYBOARD.release(Key.ctrl)
    KEYBOARD.release(Key.shift)
    KEYBOARD.release('j')


# def prepare_post(path):
#     try:
#         # Chrome setup
#         chrome_options = Options()
#         chrome_options.debugger_address = "127.0.0.1:9223"
#         driver = webdriver.Chrome(options=chrome_options,
#                                   executable_path=DRIVER_PATH)
#         #driver.get('https://www.instagram.com/marginkings/')
#         upload_element = WebDriverWait(driver, 5).until(
#             EC.presence_of_element_located(
#                 (By.XPATH, "//*[@id='react-root']//button[2]")))
#         upload_element.send_keys(r"shaaaa")
#         upload_element.click()
#         pyperclip.copy(path)
#         KEYBOARD.press(Key.ctrl)
#         KEYBOARD.press('v')
#         KEYBOARD.release(Key.ctrl)
#         KEYBOARD.release('v')
#         KEYBOARD.press(Key.enter)
#         KEYBOARD.release(Key.enter)
#         next_button = driver.find_element_by_xpath("//button[text()='Next']")
#         next_button.click()
#         caption_field = WebDriverWait(driver, 5).until(
#             EC.presence_of_element_located((By.XPATH, "//textarea")))

#         print("stop")

#     finally:
#         driver.quit()
#         driver.close()


# def run_threaded(job_func):
#     job_thread = threading.Thread(target=job_func)
#     job_thread.start()

# schedule.every(1).seconds.do(run_threaded, check_discord)
# schedule.every(1).seconds.do(run_threaded, insta_poster)
# while 1:
#     schedule.run_pending()
#     time.sleep(1)

# def check_discord():
#     options = webdriver.ChromeOptions()
#     options.add_argument("start-maximized")
#     options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     options.add_experimental_option('useAutomationExtension', False)
#     driver = webdriver.Chrome(options=options, executable_path=DRIVER_PATH)
#     driver.execute_cdp_cmd(
#         "Page.addScriptToEvaluateOnNewDocument", {
#             "source":
#             """
#         Object.defineProperty(navigator, 'webdriver', {
#         get: () => undefined
#         })
#     """
#         })
#     driver.execute_cdp_cmd(
#         'Network.setUserAgentOverride', {
#             "userAgent":
#             'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'
#         })
#     print(driver.execute_script("return navigator.userAgent;"))
#     driver.get(
#         'https://discord.com/channels/290278814217535489/699253100174770176')
#     time.sleep(2)
#     parse(find_new_messages(driver))

# def post_trade(post_func, filename):
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")
#     chrome_options.add_argument('--disable-gpu')
#     chrome_options.add_argument('--log-level=3')
#     driver = webdriver.Chrome(executable_path=DRIVER_PATH,
#                               options=chrome_options)
#     #driver.get('https://www.instagram.com/marginkings/')
#     #time.sleep(2)
#     post_func(filename, driver)


def verify_trade(parsed_trade: tuple):
    try:
        #is_duplicate = None
        is_out = None
        is_duplicate = None
        has_matching_in = None
        trade_color = None
        #has_matching_in = None
        #trade_color = None
        n = 2
        con = db_connect()
        cur = con.cursor()
        load_filtered_trades_sql = "SELECT in_or_out, ticker, strike_price, user_name, expiration, color from trades"
        cur.execute(load_filtered_trades_sql)
        filtered_trades = cur.fetchall()

        load_trades_table_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, buy_price, user_name, expiration, color from trades"
        cur.execute(load_trades_table_sql)
        full_trades = cur.fetchall()

        is_out = is_trade_already_out(filtered_trades, tuple(parsed_trade))
        if is_out is True:
            raise TradeAlreadyOut
        is_duplicate = duplicate_check(filtered_trades, tuple(parsed_trade))
        if is_duplicate is True:
            raise DuplicateTrade

        has_matching_in = has_trade_match(filtered_trades, tuple(parsed_trade))

        trade_tuple_without_datetime = parsed_trade[:n] + parsed_trade[n + 1:]
        (in_or_out, ticker, strike_price, call_or_put, buy_price, user_name,
         expiration, color) = trade_tuple_without_datetime

         

        if full_trades == []:
            is_duplicate = False
            is_out = False
            has_matching_in = False
            trade_color = color
            return is_duplicate, is_out, has_matching_in, trade_color

        for row in full_trades:
            if in_or_out == 'in' and is_duplicate is not True:
                is_duplicate = False
                has_matching_in = False
                is_out = False
                trade_color = color
                return is_duplicate, has_matching_in, is_out, trade_color

            if in_or_out == 'out' and is_duplicate is not True and has_matching_in is True:
                trade_color = color
                is_duplicate = False
                is_out = False

        return is_duplicate, is_out, has_matching_in, trade_color

    except sqlite3.Error as error:
        logging.warning(error)
        return None, None, None, None

    except (DuplicateTrade, TradeAlreadyOut) as error:
        print(error)
        return is_duplicate, is_out, has_matching_in, trade_color

    finally:
        if (con):
            con.close()


def update_table(parsed_trade: tuple):
    try:
        con = db_connect()
        cur = con.cursor()
        load_filtered_trades_sql = "SELECT in_or_out, ticker, strike_price, user_name, expiration from trades"
        cur.execute(load_filtered_trades_sql)
        filtered_trades = cur.fetchall()
        trade_already_exited = is_trade_already_out(filtered_trades,
                                                    parsed_trade)
        load_trades_table_sql = "SELECT in_or_out, ticker, strike_price, call_or_put, buy_price, user_name, expiration from trades"
        cur.execute(load_trades_table_sql)
        full_trades = cur.fetchall()
        is_duplicate = False
        n = 2
        trade_tuple_without_datetime = parsed_trade[:n] + parsed_trade[n + 1:]
        for row in full_trades:
            if row == trade_tuple_without_datetime:
                is_duplicate = True
                raise KeyError("Duplicate trade detected!")

        if is_duplicate is False and trade_already_exited is False:
            trade_sql = "INSERT INTO trades (in_or_out, ticker, datetime, strike_price, call_or_put, buy_price, user_name, expiration) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            cur.execute(trade_sql,
                        (parsed_trade[0], parsed_trade[1], parsed_trade[2],
                         parsed_trade[3], parsed_trade[4], parsed_trade[5],
                         parsed_trade[6], parsed_trade[7]))
            con.commit()
            print("Trade added to the database ")
            print(parsed_trade)
            cur.close()
    except sqlite3.Error as error:
        print("Failed to update trade in sqlite table", error)
    except KeyError as error:
        pass
    finally:
        if (con):
            con.close()
            # print("the sqlite connection is closed")

def filter_message(variable):
    noise_words = ['BOT', r'BBS-TRADE-BOT\nBOT', 'BBS-TRADE-BOT', 'joel']
    if (variable in noise_words):
        return False
    else:
        return True

def filter_trader(variable):
    if (variable in TRADERS):
        return True
    else:
        return False

def has_trade_match(database_trades: list,
                    new_trade: tuple) -> (bool, str or None):
    '''
    This will check the database for a matching IN trade and return
    True or False depending if matched.
    '''
    try:
        if database_trades == []:
            return False, None

        (in_or_out, ticker, strike_price, user_name, expiration,
            color) = database_trade
        ticker = ticker.lower()
        matched_trades = re.findall(
            rf'\(((?:[\'in\', \'out\'])+, (\'{ticker}\'), (\'{strike_price}\'), (\'{user_name}\'), (\'{expiration}\'))\)',
            str(database_trades))

        if len(matched_trades) == 2:
            return True, color

        elif len(matched_trades) > 2:
            logging.warning(
                "More than 2 of the same trade saved to database!")
            return False, None
            
        else:
            return False, None
    except ValueError:
        pass



def get_trade_expiration(split_message_list: list, unsplit_message_list: list):
    expiration_date = []
    try:
        for split in split_message_list:
            expiration_date = re.findall(
                r"^(0?[1-9]|1[0-2])(.|/|\\|-)(0?[1-9]|[12][0-9]|3[01])$",
                split.replace(' ', ''))

            if expiration_date:
                expiration_date = ''.join(expiration_date[0])
                split_message_list.remove(split)
                return expiration_date, split_message_list

            if expiration_date == []:
                split_list = unsplit_message_list.split(" - ")
                for split in split_list:
                    expiration_date = re.findall(
                        r"^(0?[1-9]|1[0-2])(.|/|\\|-)(0?[1-9]|[12][0-9]|3[01])$",
                        split.replace(' ', ''))

                    if expiration_date:
                        expiration_date = ''.join(expiration_date[0])
                        split_list.remove(split)
                        return expiration_date, split_list

        if expiration_date == []:
            raise KeyError("Could not determine expiration of trade!")

    except KeyError as e:
        logger.warning(e)
        return 'error', split_message_list

