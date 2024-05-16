# ----- IMPORTING REQUIRED MODULES ----- #

# Importing abstract class and abstractmethod.
from abc import ABC, abstractmethod

# Importing data class and field for the linkedin dataclass.
from dataclasses import dataclass, field

# Importing requests to send requests to linkedin.
import requests

# Importing BeautifulSoup to parse the html.
from bs4 import BeautifulSoup

# Importing decouple to get the search keyword from the .env file.
from decouple import config

# Importing webdriver from selenium to scrape the job description.
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# Importing BeautifulSoup to parse the job description.
from bs4 import BeautifulSoup

# Creating an abstract class for Scrappers.
class Scrapper(ABC):
    """Abstract scrapper class."""

    @abstractmethod
    def collect_data(self):
        """This Method collects data."""

    @abstractmethod
    def parse_data(self):
        """This Method parses data."""

    @abstractmethod
    def format_data(self):
        """This Method formats data."""


@dataclass(slots=True)
class LinkedinScrapper(Scrapper):
    """_summary_ : This data class scraps linkedin for the specified search key word and location in the .ev file."""

    _job_tile: str = "Android"

    _location: str = "USA"

    # The url to send request to and get data back.
    url: str = "https://www.linkedin.com/jobs/search?keywords={JOB_TITLE}&location={LOCATION}&f_TPR=r90000"

    # Default list to hold raw html data.
    raw_data: list[dict] = field(default_factory=list)

    # Default list to hold parsed data.
    parsed_data: list[tuple[str, str, str, str, str]] = field(default_factory=list)

    # Default list to hold final formatted data ready for use.
    formatted_data: list[dict] = field(default_factory=list)

    def set_search_params(self, job_tile: str, location: str) -> None:
        """_summary_ :  This method sets the search parameters for the linkedin jobs.

        Parameters
        ----------
        job_tile : str
            _description_ : The jobs title to search linkedin jobs for.
        location : str
            _description_ : The location to search for jobs in.
        """
        # Setting the job title instance variable.
        self._job_tile = job_tile
        # Setting the location instance variable.
        self._location = location

    def scrape_jobs(self) -> None:
        """This method start the scrapping process."""

        # Formatting the url with the job title and location.
        self.url = self.url.format(JOB_TITLE=self._job_tile, LOCATION=self._location)

        # Collecting the data.
        self.collect_data()
        # Parsing the data.
        self.parse_data()
        # Formatting the data.
        self.format_data()

    def collect_data(self):
        """This Method sends calls the url using the request lib and gets back the data from linkedin"""
        # Getting the response from the website.
        response = requests.get(self.url)

        # Parsing the response.
        soup = BeautifulSoup(response.content, "html.parser")

        # Getting the job cards.
        html_data = soup.find_all(
            "div",
            class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card",
        )

        # Returning the raw collected html data.
        self.raw_data = html_data

    def parse_data(self):
        """This Method parses data and extracts the job's details."""

        # Getting the data out of the instance variable for clarity.
        data = self.raw_data

        # Looping over the raw html page data and extracting jobs details.
        for job in data:
            # Getting the job title.
            job_title = job.find("h3", class_="base-search-card__title").text.strip()

            # Getting the company name.
            job_company = job.find(
                "h4", class_="base-search-card__subtitle"
            ).text.strip()

            # Getting the job location.
            job_location = job.find(
                "span", class_="job-search-card__location"
            ).text.strip()

            # Getting the job link.
            apply_link = job.find("a", class_="base-card__full-link")["href"]

            # Set up the Chrome WebDriver options
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')  # Run headlessly
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            # Initialize the WebDriver
            driver = webdriver.Chrome(options=options)

            # Open the URL
            driver.get(apply_link)

            # Get the page source
            page_source = driver.page_source

            # Parse the page source with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract job description
            description_div = soup.find('div', {'class': 'description__text description__text--rich'})
            job_description = ''
            if description_div:
                section = description_div.find('section', {'class': 'show-more-less-html'})
                if section:
                    # Get all text nodes within the section, excluding "Show more" and "Show less"
                    text_nodes = [node.get_text(strip=True) for node in section.find_all(text=True) if node.parent.name != 'button']
                    job_description = '\n'.join(text_nodes).rstrip()

            # Appending the job details to class variable list as a tuple.
            self.parsed_data.append((job_title, job_company, job_location, job_description, apply_link))

    def format_data(self):
        """This Method formats data after being parsed into a desired format"""

        # Getting the data out of the instance variable for clarity.
        data = self.parsed_data

        # Looping over the parsed data and formatting it, to be used by the TgJobPost class to create jobs posting posts for telegram.
        for job in data:
            # For each job in the data create a dict object that holds each job detail in a separate key.
            job_details = {
                # Getting the job title from the first item in the tuple.
                "job_title": job[0],
                # Getting the job company from the second item in the tuple
                "job_company": job[1],
                # Getting the job location from the third item in the tuple
                "job_location": job[2],
                # Getting the "about job" from the fourth item in the tuple
                "about_job": job[3],
                # Getting the job link from the fifth item in the tuple
                "apply_link": job[4],
            }
            # Adding this dict to the formatted_data instance variable.
            self.formatted_data.append(job_details)
