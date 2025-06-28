import requests
import time
import re
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urlparse, parse_qs
from config import Config
from ratelimit import limits, sleep_and_retry
import random
from bs4 import BeautifulSoup

class LinkedInDiscovery:
    def __init__(self):
        self.api_key = Config.RAPIDAPI_KEY
        self.base_url = "https://fresh-linkedin-profile-data.p.rapidapi.com/google-full-profiles"
        self.headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": "fresh-linkedin-profile-data.p.rapidapi.com",
            "x-rapidapi-key": self.api_key
        }
    
    @sleep_and_retry
    @limits(calls=Config.SEARCH_RATE_LIMIT, period=60)
    def search_linkedin_profiles(self, job_description: str, limit: int = 10) -> List[Dict]:
        # Improved parsing: extract job title, location, and keywords as a list
        job_title, location, _ = self._parse_job_description(job_description)
        keywords = self._extract_search_terms(job_description)
        keywords_str = ', '.join(keywords) if keywords else ''
        
        payload = {
            "name": "",  # Not using name for generic search
            "company_name": "",
            "job_title": job_title,
            "location": location,
            "keywords": job_description[:120],  # Truncate to stay under 128 char limit
            "limit": limit
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ API Error: {response.text}")
                return []
                
            response.raise_for_status()
            data = response.json()
            profiles = []
            for item in data.get("data") or []:
                profiles.append({
                    "name": item.get("full_name"),
                    "linkedin_url": item.get("linkedin_url"),
                    "headline": item.get("headline"),
                    "location": item.get("location"),
                    "current_company": item.get("company"),
                    "job_title": item.get("job_title")
                })
            return profiles
        except Exception as e:
            print(f"Error searching LinkedIn profiles via RapidAPI: {e}")
            return []
    
    def _parse_job_description(self, job_description: str):
        # Improved parsing for job titles
        job_title = ""
        location = ""
        keywords = job_description
        
        # Try to extract job title - look for common patterns
        job_title_patterns = [
            r"([A-Z][a-zA-Z]+( [A-Z][a-zA-Z]+)*)",  # Original pattern
            r"([A-Z][a-z]+( [A-Z][a-z]+)*)",  # Simpler pattern
            r"([A-Z][a-zA-Z]+)",  # Single capitalized word
        ]
        
        for pattern in job_title_patterns:
            match = re.search(pattern, job_description)
            if match:
                job_title = match.group(0)
                # Clean up the job title
                job_title = job_title.strip()
                if len(job_title) > 3:  # Make sure it's not too short
                    break
        
        # If no job title found, use the first few words
        if not job_title:
            words = job_description.split()[:3]
            job_title = " ".join(words)
        
        # Extract location (look for country/state abbreviations)
        location_match = re.search(r"\b(US|USA|United States|UK|Canada|India|Germany|France|Remote)\b", job_description, re.IGNORECASE)
        location = location_match.group(0) if location_match else ""
        
        return job_title, location, keywords
    
    def _extract_search_terms(self, job_description: str) -> List[str]:
        """Extract key search terms from job description."""
        # Simple keyword extraction - in production, use more sophisticated NLP
        keywords = []
        
        # Common job titles and skills
        common_terms = [
            'software engineer', 'developer', 'manager', 'director', 'lead',
            'python', 'javascript', 'java', 'react', 'node.js', 'aws',
            'data scientist', 'analyst', 'product manager', 'designer',
            'senior', 'full stack', 'backend', 'frontend', 'devops'
        ]
        
        job_lower = job_description.lower()
        for term in common_terms:
            if term in job_lower:
                keywords.append(term)
        
        # Extract company names (simple pattern matching)
        company_pattern = r'\b[A-Z][a-zA-Z\s&]+(?:Inc|Corp|LLC|Ltd|Company|Technologies|Systems|Startup)\b'
        companies = re.findall(company_pattern, job_description)
        keywords.extend(companies[:3])  # Limit to 3 companies
        
        # If no keywords found, use basic terms
        if not keywords:
            keywords = ['professional', 'experience']
        
        return keywords[:5]  # Limit to 5 keywords
    
    def _parse_google_results(self, html_content: str) -> List[Dict]:
        """Parse Google search results to extract LinkedIn profiles."""
        profiles = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find search result links
        search_results = soup.find_all('a', href=True)
        
        for result in search_results:
            href = result.get('href', '')
            
            # Check if it's a LinkedIn profile URL
            if 'linkedin.com/in/' in href:
                # Extract LinkedIn URL from Google redirect
                linkedin_url = self._extract_linkedin_url(href)
                if linkedin_url and self._is_valid_linkedin_url(linkedin_url):
                    # Extract name and headline from the result
                    name = self._extract_name(result)
                    headline = self._extract_headline(result)
                    
                    # Only add if we have a valid name
                    if name and name != "Unknown" and name != "click here":
                        profiles.append({
                            'name': name,
                            'linkedin_url': linkedin_url,
                            'headline': headline
                        })
        
        return profiles[:Config.MAX_SEARCH_RESULTS]
    
    def _is_valid_linkedin_url(self, url: str) -> bool:
        """Check if the URL is a valid LinkedIn profile URL."""
        if not url:
            return False
        
        # Must be a proper LinkedIn profile URL
        if not url.startswith('http'):
            return False
        
        # Must contain linkedin.com/in/ and have a profile identifier
        if 'linkedin.com/in/' not in url:
            return False
        
        # Extract the profile identifier
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.split('/')
            if len(path_parts) < 3 or not path_parts[2]:  # /in/username
                return False
        except:
            return False
        
        return True
    
    def _extract_linkedin_url(self, google_url: str) -> Optional[str]:
        """Extract LinkedIn URL from Google search result URL."""
        try:
            # Google search results often redirect through google.com
            if 'google.com/url?' in google_url:
                # Extract the actual URL from Google's redirect
                parsed = urlparse(google_url)
                query_params = parse_qs(parsed.query)
                if 'q' in query_params:
                    url = query_params['q'][0]
                    if 'linkedin.com/in/' in url:
                        return url
            elif 'linkedin.com/in/' in google_url:
                return google_url
        except Exception as e:
            print(f"Error extracting LinkedIn URL: {e}")
        
        return None
    
    def _extract_name(self, result_element) -> str:
        """Extract name from search result element."""
        # Look for the main text content
        text = result_element.get_text(strip=True)
        if text:
            # Simple name extraction - first part before common separators
            name = text.split(' - ')[0].split(' | ')[0].split(' at ')[0]
            name = name.strip()
            
            # Filter out common non-name text
            if name.lower() in ['click here', 'unknown', 'linkedin', 'profile']:
                return "Unknown"
            
            return name
        return "Unknown"
    
    def _extract_headline(self, result_element) -> str:
        """Extract headline from search result element."""
        text = result_element.get_text(strip=True)
        if ' - ' in text:
            return text.split(' - ')[1].split(' | ')[0]
        elif ' | ' in text:
            return text.split(' | ')[1]
        return "No headline available"
    
    def get_profile_details(self, linkedin_url: str) -> Optional[Dict]:
        """
        Get detailed profile information from LinkedIn URL.
        Note: This is a simplified version. In production, you'd need proper LinkedIn API access.
        """
        try:
            response = requests.get(linkedin_url, headers=self.headers, timeout=Config.SEARCH_TIMEOUT)
            response.raise_for_status()
            
            # Parse the profile page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract basic information (this is simplified)
            profile_data = {
                'name': self._extract_profile_name(soup),
                'headline': self._extract_profile_headline(soup),
                'location': self._extract_profile_location(soup),
                'summary': self._extract_profile_summary(soup),
                'experience': self._extract_profile_experience(soup),
                'education': self._extract_profile_education(soup),
                'skills': self._extract_profile_skills(soup)
            }
            
            return profile_data
            
        except Exception as e:
            print(f"Error getting profile details for {linkedin_url}: {e}")
            return None
    
    def _extract_profile_name(self, soup) -> str:
        """Extract name from LinkedIn profile page."""
        # Look for common name selectors
        name_selectors = [
            'h1.text-heading-xlarge',
            '.text-heading-xlarge',
            'h1[data-section="name"]',
            '.pv-text-details__left-panel h1'
        ]
        
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return "Unknown"
    
    def _extract_profile_headline(self, soup) -> str:
        """Extract headline from LinkedIn profile page."""
        headline_selectors = [
            '.text-body-medium.break-words',
            '.pv-text-details__left-panel .text-body-medium',
            '[data-section="headline"]'
        ]
        
        for selector in headline_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return "No headline available"
    
    def _extract_profile_location(self, soup) -> str:
        """Extract location from LinkedIn profile page."""
        location_selectors = [
            '.text-body-small.inline.t-black--light.break-words',
            '.pv-text-details__left-panel .text-body-small'
        ]
        
        for selector in location_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return "Location not specified"
    
    def _extract_profile_summary(self, soup) -> str:
        """Extract summary from LinkedIn profile page."""
        summary_selectors = [
            '.pv-shared-text-with-see-more',
            '.pv-about__summary-text',
            '[data-section="summary"]'
        ]
        
        for selector in summary_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ""
    
    def _extract_profile_experience(self, soup) -> List[Dict]:
        """Extract experience from LinkedIn profile page."""
        experience = []
        # This is a simplified extraction - in production, you'd need more sophisticated parsing
        experience_sections = soup.find_all('section', {'data-section': 'experience'})
        
        for section in experience_sections:
            # Extract job details (simplified)
            job_elements = section.find_all('li', class_='artdeco-list__item')
            for job in job_elements:
                title_elem = job.find('h3')
                company_elem = job.find('p', class_='pv-entity__secondary-title')
                
                if title_elem and company_elem:
                    experience.append({
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True),
                        'duration': '',
                        'description': ''
                    })
        
        return experience
    
    def _extract_profile_education(self, soup) -> List[str]:
        """Extract education from LinkedIn profile page."""
        education = []
        education_sections = soup.find_all('section', {'data-section': 'education'})
        
        for section in education_sections:
            school_elements = section.find_all('h3')
            for school in school_elements:
                education.append(school.get_text(strip=True))
        
        return education
    
    def _extract_profile_skills(self, soup) -> List[str]:
        """Extract skills from LinkedIn profile page."""
        skills = []
        skills_sections = soup.find_all('section', {'data-section': 'skills'})
        
        for section in skills_sections:
            skill_elements = section.find_all('span', class_='pv-skill-category-entity__name-text')
            for skill in skill_elements:
                skills.append(skill.get_text(strip=True))
        
        return skills

    def search_linkedin_profiles_via_google(self, job_description: str, limit: int = 10) -> List[Dict]:
        """Search Google for LinkedIn profiles relevant to the job description."""
        # Build Google search query
        query = f'site:linkedin.com/in {job_description}'
        url = f'https://www.google.com/search?q={quote_plus(query)}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            profiles = self._parse_google_results(resp.text)
            return profiles[:limit]
        except Exception as e:
            print(f"Error scraping Google for LinkedIn profiles: {e}")
            return []

    def search_linkedin_profiles_with_fallback(self, job_description: str, limit: int = 10) -> List[Dict]:
        """Try Google scraping first, then fall back to RapidAPI if no candidates found."""
        profiles = self.search_linkedin_profiles_via_google(job_description, limit=limit)
        if profiles:
            return profiles
        print("🔄 Falling back to RapidAPI...")
        return self.search_linkedin_profiles(job_description, limit=limit) 