from selenium import webdriver
import time
import json
import os
import platform

class BlockedUser(Exception):
    pass

if not "ignored" in os.listdir('.'):
    os.mkdir("./ignored")

def get_name(driver):
    name, surname = driver.find_element_by_name(
        'q').get_attribute('value').split(' ')
    name = name.capitalize()
    surname = surname.capitalize()
    return (name, surname)


def login(driver, email, password, credentials_file=None):
    try:
        with open(credentials_file, 'r') as file:
            data = json.loads(file.read())
            email = data['login']
            password = data['password']
    except (FileNotFoundError, json.JSONDecodeError) as exception:
        pass

    print('Going to facebook login page')
    driver.get('https://www.facebook.com/')
    print('Locating elements')
    login_element = driver.find_element_by_id("email")
    password_element = driver.find_element_by_id("pass")

    login_button = driver.find_element_by_xpath(
        "//input[@data-testid='royal_login_button']")

    print('Logging in')
    login_element.clear()
    login_element.send_keys(email)

    password_element.clear()
    password_element.send_keys(password)

    login_button.click()
    print('Logged in')

def check_if_blocked(driver):
    page_source = driver.page_source
    return "Jesteś tymczasowo zablokowany" in page_source or "You're temporarily blocked" in page_source

def scroll_down(browser):
    SCROLL_PAUSE_TIME = 2
    # Get scroll height
    last_height = browser.execute_script("return document.body.scrollHeight")
    last_time = time.time()
    while True:
        # Scroll down to bottom
        browser.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

        now = time.time()
        if now - last_time >= SCROLL_PAUSE_TIME:
            # Calculate new scroll height and compare with last scroll height
            new_height = browser.execute_script(
                "return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            last_time = now


def get_all_friends(browser):
    scroll_down(browser)
    friends_elements = browser.find_elements_by_xpath(
        '//li[@class="_698"]/div[@data-testid="friend_list_item"]//div[@class="fsl fwb fcb"]/a')
    friends = []
    for f in friends_elements:
        users_url = f.get_attribute(
            'href')[:-len('?fref=pb&hc_location=friends_tab')]
        name = f.text
        friends.append({
            'name': name,
            'profile': users_url
        })
    return friends


def go_to_group_members_page(driver):
    suffix = "members/" if driver.current_url.endswith('/') else "/members/"
    driver.get(driver.current_url + suffix)


def get_group_members(driver, group_page):
    print("Getting group members")
    current_url = driver.current_url
    try:
        driver.get(group_page)
        go_to_group_members_page(driver)
        members = []
        try:
            scroll_down(driver)
            members_elements = driver.find_elements_by_css_selector(
                '#groupsMemberSection_recently_joined ._60ri.fsl.fwb.fcb a:first-of-type')
            for m in members_elements:
                user_url = m.get_attribute('href')
                if user_url.startswith('https://www.facebook.com/profile.php'):
                    user_url = user_url.split('&')[0]
                else:
                    user_url = user_url.split('?')[0]
                name = m.text
                members.append({
                    'name': name,
                    'profile': user_url
                })
        except:
            pass
    finally:
        driver.get(current_url)
    return members


def get_user_likes(browser, user):
    current_url = browser.current_url
    if user['profile'].startswith('https://www.facebook.com/profile.php?id='):
        browser.get(user['profile'] + '&sk=likes')
    else:
        browser.get(user['profile'] + '/likes')
    
    if check_if_blocked(browser):
        raise BlockedUser

    if 'likes' in browser.current_url:
        data = []
        scroll_down(browser)
        likes_elements = browser.find_elements_by_xpath(
            '//div[@class="fsl fwb fcb"]')
        for element in likes_elements:
            text_and_href_element = element.find_element_by_xpath('./a')
            text = text_and_href_element.text
            href = text_and_href_element.get_attribute('href')
            target_type = element.find_element_by_xpath('../div[2]').text
            data.append({
                'text': text,
                'type': target_type,
                'href': href,
            })
        browser.get(current_url)
        return data
    else:
        return [{
                'text': 'User does not share this info',
                'type': None,
                'href': None,
                }]


def create_chrome_options(headless=False):
    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "profile.managed_default_content_settings.images": 2,  # disable images
        "profile.default_content_setting_values.notifications": 2  # disable notifications
    }
    if headless:
        chrome_options.add_argument('headless')
    chrome_options.add_argument('log-level=3')
    chrome_options.add_experimental_option("prefs", prefs)
    return chrome_options


def create_driver(headless=False):
    chrome_options = create_chrome_options(headless)
    system = platform.system()
    if system == 'Linux':
        path_to_chromedrive = "./chromedriver"
    elif system == 'Windows':
        path_to_chromedrive = 'chromedriver.exe'
    else:
        print('This OS is not supported')
        raise SystemExit

    return webdriver.Chrome(executable_path=path_to_chromedrive, chrome_options=chrome_options)


def create_driver_and_login(email, password, headless=False, file=None):
    d = create_driver(headless)
    login(d, email, password, file)
    return d


def scrap_users_data(driver, users, output_file):
    with open(output_file, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
    try:
        done_profiles = [user['profile'] for user in data]
        print("Done profiles", len(done_profiles))
        for user in users:
            print('Processing ' + user['name'], end='... ')
            if not user['profile'] in done_profiles:
                time_before = time.time()
                try:
                    data.append({
                        'name': user['name'],
                        'profile': user['profile'],
                        'likes': get_user_likes(driver, user),
                    })
                except BlockedUser:
                    print("You are now blocked")
                    break
                done_profiles.append(user['profile'])
                print(f'Done. Time: {int(time.time() - time_before)}s')
            else:
                print('Skipped')
    except:
        # silently catch KeyboardInterrupt
        pass
    finally:
        with open(output_file, "wt") as f:
            json.dump(data, f)
        print('\nFile saved')


def main():
    print(
        '''
    #Example usage
    d = create_driver_and_login("<your email>", "<your password>", [<Headless mode> True/False, <path to file with password and email>])
    members = get_group_members(d, <group's main page url, like: https://www.facebook.com/groups/gpython/ >)
    scrap_users_data(d, members, "output_file.txt") #this will skip already processed users in file and update it with new users
    #to stop at any time press Ctrl+C
    '''
    )


def foo():
    d = create_driver_and_login("", "", True, "ignored/personal_data.txt")
    members = get_group_members(
        d, "https://www.facebook.com/groups/PolitechnikaPoznanska2018/")
    scrap_users_data(d, members, "ignored/data/PP grupa/users.json")


if __name__ == '__main__':
    main()
