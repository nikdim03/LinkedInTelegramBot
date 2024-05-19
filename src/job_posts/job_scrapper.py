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

# Importing BeautifulSoup to parse the job description.
from bs4 import BeautifulSoup

# Importing markdownify to convert HTML to Markdown.
from markdownify import MarkdownConverter

# Importing datetime to parse timestamp
from datetime import datetime, timedelta

# Importing re to parse timestamp
import re

# Getting default job title.
DEFAULT_JOB_TITLE = config("DEFAULT_JOB_TITLE")

# Getting default location.
DEFAULT_LOCATION = config("DEFAULT_LOCATION")

# Getting fetch interval (default = 24 hours & 3 minutes)
if config("FETCH_JOBS_INTERVAL") != '':
    FETCH_JOBS_INTERVAL = config("FETCH_JOBS_INTERVAL")
else:
    FETCH_JOBS_INTERVAL = '86580'

# Creating a custom MarkdownConverter that uses one asterisk for strong/bold text.
class SingleAsteriskBoldConverter(MarkdownConverter):
    """
    Create a custom MarkdownConverter that uses one asterisk for strong/bold text.
    """
    
    def convert_strong(self, el, text, convert_as_inline):
        return '*' + text + '*' if text else ''
    
    def convert_b(self, el, text, convert_as_inline):
        return self.convert_strong(el, text, convert_as_inline)

# Convert HTML to Markdown using the custom converter
def md(html, **options):
    return SingleAsteriskBoldConverter(**options).convert(html)


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

    _job_tile: str = DEFAULT_JOB_TITLE

    _location: str = DEFAULT_LOCATION

    _fetch_jobs_interval: str = FETCH_JOBS_INTERVAL

    # The url to send request to and get data back.
    url: str = "https://www.linkedin.com/jobs/search?keywords={JOB_TITLE}&location={LOCATION}&f_TPR=r{FETCH_JOBS_INTERVAL}"

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
        self.url = self.url.format(JOB_TITLE=self._job_tile, LOCATION=self._location, FETCH_JOBS_INTERVAL = self._fetch_jobs_interval)

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

            # Get the page source
            page_source = requests.get(apply_link).content

            # Parse the page source with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract ago text
            ago_text_element = soup.find('span', class_='posted-time-ago__text')
            # Check if the element was found before accessing .text
            if ago_text_element:
                ago_text = ago_text_element.text.strip()
            else:
                ago_text = "Unknown"

            # Ectract the number from ago text
            num = 0
            match = re.search(r'\d+', ago_text)
            if match:
                num = int(match.group())

            # Calculate post time
            timestamp = datetime.now()
            if 'minute' in ago_text:
                timestamp = datetime.now() - timedelta(minutes=num)
            elif 'hour' in ago_text:
                timestamp = datetime.now() - timedelta(hours=num)
            elif 'day' in ago_text:
                timestamp = datetime.now() - timedelta(days=num)

            # Rename ago text for better understanding
            if ago_text.lower() == '1 day ago':
                ago_text = '24 hours ago'

            # Find and remove 'Show more' and 'Show less' buttons
            for button in soup.find_all('button'):
                if button.text.strip() in ['Show more', 'Show less']:
                    button.decompose()

            # Extract job description in Markdown format
            description_div = soup.find('div', {'class': 'description__text description__text--rich'})
            job_description_md = ''
            if description_div:
                # Convert the inner HTML of description_div to Markdown
                job_description_md = md(str(description_div), bullets=['•'])

            # Check if specified job title is found in either the job title or job description
            if self._job_tile.lower() in job_title.lower() or self._job_tile in job_description_md.lower():
                # Appending the job details to class variable list as a tuple
                self.parsed_data.append((job_title, job_company, job_location, self.replace_md_spaces(job_description_md), apply_link, timestamp.astimezone(), ago_text))

    def format_data(self):
        """This Method formats data after being parsed into a desired format"""
        # Getting the data out of the instance variable for clarity.
        data = self.parsed_data

        # Sorting the data based on the timestamp (earliest to latest)
        data.sort(key=lambda job: job[5])

        # Looping over the parsed data and formatting it, to be used by the TgJobPost class to create jobs posting posts for telegram.
        for job in data:
            # For each job in the data create a dict object that holds each job detail in a separate key.
            job_details = {
                "job_title": job[0],
                "job_company": job[1],
                "job_location": job[2],
                "about_job": self.limit_newlines(job[3]).strip(),
                "apply_link": job[4],
                "timestamp": job[6]
            }
            # Adding this dict to the formatted_data instance variable.
            self.formatted_data.append(job_details)


    def replace_md_spaces(self, text):
        # Replace lines that consist solely of attributed spaces, with the ones consisting of plain spaces
        text = re.sub(r'^(?:\s*\*\s*\*\s*)+$', ' ', text, flags=re.MULTILINE)
        text = re.sub(r'^(?:\s*_\s*_\s*)+$', ' ', text, flags=re.MULTILINE)
        return text

    def limit_newlines(self, text, max_newlines=4):
        """
        Replace sequences of more than max_newlines newline or whitespace-only lines with exactly max_newlines newlines.

        Args:
            text (str): The input text.
            max_newlines (int): The maximum number of consecutive newlines allowed.

        Returns:
            str: The modified text.
        """
        # Create a regex pattern to match sequences of more than max_newlines newlines or whitespace-only lines
        pattern = re.compile(r'(\s*\n\s*){' + str(max_newlines + 1) + r',}')
        
        # Replace these sequences with exactly max_newlines newlines
        replacement = '\n' * max_newlines
        return pattern.sub(replacement, text)
