import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time

BASE_URL = "https://rera.odisha.gov.in"
PROJECT_LIST_URL = f"{BASE_URL}/projects/project-list"

def get_first_6_project_links():
    """Fetches the first 6 'View Details' links from the 'Projects Registered' section."""
    links = []
    try:
        print(f"Fetching project list from: {PROJECT_LIST_URL}")
        response = requests.get(PROJECT_LIST_URL, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        registered_projects_div = soup.find('div', id='project-list-responsive')
        if not registered_projects_div:
            print("Could not find the 'Projects Registered' section div.")
            return []

        table = registered_projects_div.find('table')
        if not table:
            print("Could not find the table within 'Projects Registered' section.")
            return []

        rows = table.find('tbody').find_all('tr')
        count = 0
        for row in rows:
            if count >= 6:
                break
            cells = row.find_all('td')
            if len(cells) > 0:
                link_tag = cells[-1].find('a', text='View Details')
                if link_tag and link_tag.has_attr('href'):
                    detail_url = BASE_URL + link_tag['href']
                    links.append(detail_url)
                    count += 1
        print(f"Found {len(links)} project detail links.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching project list: {e}")
    return links

def scrape_project_details(detail_url, driver):
    """Scrapes specific details from a single project's detail page."""
    print(f"Scraping details from: {detail_url}")
    project_data = {
        "Rera Regd. No": "Not Found",
        "Project Name": "Not Found",
        "Promoter Name": "Not Found",
        "Address of the Promoter": "Not Found",
        "GST No.": "Not Found"
    }

    try:
        driver.get(detail_url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'RERA Regd. No.')]"))
        )
        
        soup_project_tab = BeautifulSoup(driver.page_source, 'html.parser')
        rera_no_label = soup_project_tab.find('td', string=lambda t: t and 'RERA Regd. No.' in t)
        if rera_no_label and rera_no_label.find_next_sibling('td'):
            project_data["Rera Regd. No"] = rera_no_label.find_next_sibling('td').text.strip()
        project_name_label = soup_project_tab.find('td', string=lambda t: t and 'Name of Project' in t)
        if project_name_label and project_name_label.find_next_sibling('td'):
            project_data["Project Name"] = project_name_label.find_next_sibling('td').text.strip()
        promoter_tab_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='#promoter-details']"))
        )
        driver.execute_script("arguments[0].click();", promoter_tab_button)
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, "//div[@id='promoter-details']//td[contains(text(), 'Company Name')]"))
        )
        time.sleep(1)

        soup_promoter_tab = BeautifulSoup(driver.page_source, 'html.parser')
        promoter_details_div = soup_promoter_tab.find('div', id='promoter-details')

        if promoter_details_div:
            company_name_label = promoter_details_div.find('td', string=lambda t: t and 'Company Name' in t)
            if company_name_label and company_name_label.find_next_sibling('td'):
                project_data["Promoter Name"] = company_name_label.find_next_sibling('td').text.strip()

            address_label = promoter_details_div.find('td', string=lambda t: t and 'Registered Office Address' in t)
            if address_label and address_label.find_next_sibling('td'):
                project_data["Address of the Promoter"] = address_label.find_next_sibling('td').text.strip()

            gst_label = promoter_details_div.find('td', string=lambda t: t and 'GSTIN No' in t) 
            if gst_label and gst_label.find_next_sibling('td'):
                project_data["GST No."] = gst_label.find_next_sibling('td').text.strip()
        else:
            print(f"Could not find promoter details div for {detail_url}")
            
    except Exception as e:
        print(f"Error scraping details from {detail_url}: {e}")
    
    return project_data


if __name__ == "_main_":
    project_detail_links = get_first_6_project_links()
    all_projects_data = []

    if project_detail_links:
        # Setup Selenium WebDriver
        print("Setting up Selenium WebDriver...")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless") 
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
        
        try:
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
            print("WebDriver initialized.")

            for link in project_detail_links:
                data = scrape_project_details(link, driver)
                all_projects_data.append(data)
                print(f"Successfully scraped: {data.get('Project Name', 'N/A')}")
                time.sleep(1) # Small delay to be polite to the server

            driver.quit()
            print("WebDriver closed.")

        except Exception as e:
            print(f"An error occurred during WebDriver setup or operation: {e}")
            if 'driver' in locals() and driver:
                driver.quit()

    print("\nScraped Project Data")
    if all_projects_data:
        for i, project in enumerate(all_projects_data):
            print(f"\nProject {i+1}")
            for key, value in project.items():
                print(f"{key}: {value}")
    else:
        print("No data was scraped.")

    print("\nPip Install Requirements")
    print("requests")
    print("beautifulsoup4")
    print("selenium")
    print("webdriver-manager")
    
"""
Pip Install Requirements:
- requests
- beautifulsoup4
- selenium
- webdriver-manager
"""