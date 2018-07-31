from selenium import webdriver
import time
import json
import os
import platform

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
    
    login_button = driver.find_element_by_xpath("//input[@data-testid='royal_login_button']")

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
            'text' : text,
            'type' : target_type,
            'href': href,
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
    system = platform.system() 
    if system == 'Linux':
        path_to_chromedrive = "./chromedriver"
    elif system == 'Windows':
        path_to_chromedrive = 'chromedriver.exe'
    else:
        print('This OS is not supported')
        raise SystemExit

    return webdriver.Chrome(executable_path = path_to_chromedrive, chrome_options=chrome_options)


def main():
    try:    
        print('Reading login and password from file')
        try:
            with open('personal_data.txt', 'r') as f:
                data = json.loads(f.read())
                email = data['login']
                password = data['password']
        except:
            print("Looks like you don't have personal_data.txt file created or it is corrupted. Enter your facebook email and password and I'll create it for you")
            email = input('Email: ')
            password = input('Password: ')
            
            try:
                os.remove('personal_data.txt')
            except:
                pass

            with open('personal_data.txt', 'a+') as f:
                f.write(json.dumps({'login': email, 'password': password}))

        browser = create_driver()

        print('Going to facebook login page')
        browser.get("https://www.facebook.com/?stype=lo&jlou=AfdVJ-hrL71br5PLvtyLDuyE9EP-3-NjOXpkRz-6S2AV6OKkTpciseqJ-FOU7VGw1m7jTryYRTlpLbDRlKEdKavfZD9OR7ekYGshNPzAu34sng&smuh=25889&lh=Ac8eAmcxz0TXngxG")

        login(browser, email, password)

        print("Getting user's name and surname")
        browser.get("https://www.facebook.com/profile")
        name,surname = get_name(browser, browser.current_url)

        print('Going into friends tab')
        browser.get('https://www.facebook.com/profile')
        browser.get(browser.current_url[:-2] + '/friends/')

        time.sleep(2)
        print('Scrolling down')
        scroll_down(browser)

        print('Getting all friends')
        friends = get_all_friends(browser)
        
        old_dane = [f for f in os.listdir('.') if f.startswith('dane')]
        if len(old_dane) > 0:
            with open(sorted(old_dane)[-1], 'r') as od:
                text = od.read()
                if text is not '':
                    current_data = json.loads(text)
                else:
                    current_data = []
        else:
            current_data = []

        done_profiles = [user['profile'] for user in current_data]
        for friend in friends:
            print('Processing ' + friend['name'], end = '... ')
            if not friend['profile'] in done_profiles:
                if friend['profile'].startswith('https://www.facebook.com/profile.php?id='):
                    browser.get(friend['profile'] + '&sk=likes')
                else:
                    browser.get(friend['profile'] + '/likes')
                scroll_down(browser)
                current_data.append({
                    'name' : friend['name'],
                    'profile': friend['profile'],
                    'likes': get_likes(browser),
                })
                done_profiles.append(friend['profile'])
                print('Done')
            else:
                print('Skipped')

        for name in (a['name'] for a in friends):
            print(name)

    finally:
        try:
            new_file = f"dane_{time.strftime('%d-%m-%Y-%H-%M-%S')}.json"
            with open(new_file, 'a+') as f:
                json.dump(current_data, f)
        except:
            os.remove(new_file)
        browser.quit()
        

if __name__ == '__main__':
    main()

