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
    likes_elements = browser.find_elements_by_xpath('//div[@class="fsl fwb fcb"]/a')
    data = []
    for element in likes_elements:
        data.append({
            'text' : element.text,
            'href': element.get_attribute('href')
        })
    return data

def create_driver():
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.default_content_setting_values.notifications" : 2}
    chrome_options.add_experimental_option("prefs",prefs)
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

        i = 0
        for friend in friends:
            if i >= 10:
                break
            i += 1
            browser.get(friend['profile'] + '/likes')
            time.sleep(1)
            scroll_down(browser)
            friend['likes'] = get_likes(browser)


        for name in (a['name'] for a in friends):
            print(name)
        with open('dane.json', 'r+') as f:
            f.truncate(0)
            current_data = []
            current_data.extend(friend for friend in friends)
            f.write(json.dumps(current_data))
    finally:
        browser.quit()


if __name__ == '__main__':
    main()

