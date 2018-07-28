from selenium import webdriver
from bs4 import BeautifulSoup as bs
import time
import json

def get_name(driver, user_profile):
    current_url = driver.current_url
    driver.get(user_profile)
    name,surname = driver.find_element_by_name('q').get_attribute('value').split(' ')
    name = name.capitalize()
    surname = surname.capitalize()
    driver.get(current_url)
    return (name,surname)

def login(driver, email, password):
    print('Locating elements')
    login_element = driver.find_element_by_id("email")
    password_element = driver.find_element_by_id("pass")
    login_button = driver.find_element_by_id("u_0_2")

    print('Logging in')
    login_element.clear()
    login_element.send_keys(email)

    password_element.clear()
    password_element.send_keys(password)

    login_button.click()

def scroll_down(browser):
    SCROLL_PAUSE_TIME = 1.5
    # Get scroll height
    last_height = browser.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def get_all_friends(browser):
    friends_elements = browser.find_elements_by_xpath('//li[@class="_698"]/div[@data-testid="friend_list_item"]//div[@class="fsl fwb fcb"]/a')
    friends = []
    for f in friends_elements:
        users_url = f.get_attribute('href')[:-len('?fref=pb&hc_location=friends_tab')]
        name = f.text
        friends.append({
            'name': name,
            'profile': users_url
        })
    return friends

def get_likes(browser):
    #likes_elements = browser.find_elements_by_css_selector('.fsl.fwb.fcb')
    likes_elements = browser.find_elements_by_xpath('//div[@class="fsl fwb fcb"]')
    data = []
    for element in likes_elements:
        text_and_href_element = element.find_element_by_xpath('./a')
        text = text_and_href_element.text
        href = text_and_href_element.get_attribute('href')
        target_type = element.find_element_by_xpath('../div[2]').text
        data.append({
            'text' : text
            'type' : target_type,
            'href': href
        })
    return data

def create_chrome_options():
    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "profile.managed_default_content_settings.images": 2, #disable images
        "profile.default_content_setting_values.notifications": 2 #disable notifications
        }
    # https://stackoverflow.com/questions/28070315/python-disable-images-in-selenium-google-chromedriver
    chrome_options.add_experimental_option("prefs",prefs)
    return chrome_options

def create_driver():
    chrome_options = create_chrome_options()
    path_to_chromedrive = "./chromedriver"
    return webdriver.Chrome(executable_path = path_to_chromedrive, chrome_options=chrome_options)


def main():
    try:    
        print('Reading login and password from file')
        with open('personal_data.txt', 'r') as f:
            data = json.loads(f.read())
            email = data['login']
            password = data['password']

        browser = create_driver()

        print('Going to facebook login page')
        browser.get("https://www.facebook.com/?stype=lo&jlou=AfdVJ-hrL71br5PLvtyLDuyE9EP-3-NjOXpkRz-6S2AV6OKkTpciseqJ-FOU7VGw1m7jTryYRTlpLbDRlKEdKavfZD9OR7ekYGshNPzAu34sng&smuh=25889&lh=Ac8eAmcxz0TXngxG")

        login(browser, email, password)

        print("Getting user's name and surname")
        browser.get("https://www.facebook.com/profile")
        name,surname = get_name(browser, browser.current_url)

        print('Going into friends tab')
        browser.get('https://www.facebook.com/' + name.lower() + '.' + surname.lower() + '/friends/')

        time.sleep(2)
        print('Scrolling down')
        scroll_down(browser)

        print('Getting all friends')
        #friends_elements = browser.find_elements_by_xpath('//li/div[@data-testid="friend_list_item"]/a[@href]')
        friends = get_all_friends(browser)

        for friend in friends:
            if friend['profile'].startswith('https://www.facebook.com/profile.php?id='):
                browser.get(friend['profile'] + '&sk=likes')
            else:
                browser.get(friend['profile'] + '/likes')
            time.sleep(1)
            scroll_down(browser)
            friend['likes'] = get_likes(browser)


        for name in (a['name'] for a in friends):
            print(name)

    finally:
        with open(f"dane_{time.strftime('%d-%m-%Y-%H-%M-%S')}.json", 'a+') as f:
            current_data = []
            current_data.extend(friend for friend in friends)
            f.write(json.dumps(current_data))
        browser.quit()


if __name__ == '__main__':
    main()

