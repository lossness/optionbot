def discord_error_check():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument('--disable-gpu')
    # chrome_options.add_argument('--log-level=3')
    chrome_options.debugger_address = '127.0.0.1:9222'
    discord_driver = webdriver.Chrome(executable_path=DISCORD_DRIVER_PATH,
                                      options=chrome_options)
    error_producer_classic(discord_driver)