"""
Social Media Search Module - Specialized search functionality for finding leads on social media platforms.
"""

import os
import time
import random
import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

class SocialMediaSearch:
    """
    A class to search for potential leads on social media platforms.
    """
    
    def __init__(self):
        """
        Initialize the SocialMediaSearch.
        """
        # List of realistic user agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        ]
        
        # Initialize session for requests
        self.session = requests.Session()
    
    def search_all_platforms(self, search_query: str, limit: int) -> List[Dict]:
        """
        Search across multiple social media platforms for leads.
        
        Args:
            search_query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of search results from social media platforms
        """
        results = []
        platforms_to_try = ["linkedin", "twitter", "instagram"]
        results_per_platform = max(2, limit // len(platforms_to_try))
        
        for platform in platforms_to_try:
            try:
                if platform == "linkedin":
                    platform_results = self.search_linkedin(search_query, results_per_platform)
                elif platform == "twitter":
                    platform_results = self.search_twitter(search_query, results_per_platform)
                elif platform == "instagram":
                    platform_results = self.search_instagram(search_query, results_per_platform)
                
                results.extend(platform_results)
                
                # If we have enough results, stop searching
                if len(results) >= limit:
                    break
            except Exception as e:
                print(f"Error searching {platform}: {e}")
        
        return results[:limit]
    
    def search_linkedin(self, search_query: str, limit: int) -> List[Dict]:
        """
        Search LinkedIn for potential leads.
        
        Args:
            search_query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of search results from LinkedIn
        """
        results = []
        
        try:
            # Construct search URL for LinkedIn people search
            search_terms = search_query.replace(" ", "%20")
            url = f"https://www.google.com/search?q=site:linkedin.com/in+{search_terms}"
            
            # Set random user agent
            headers = {"User-Agent": random.choice(self.user_agents)}
            
            # Make request
            response = self.session.get(url, headers=headers, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract search results
                search_results = soup.select("div.g")
                
                for result in search_results[:limit]:
                    try:
                        # Extract title and link
                        title_element = result.select_one("h3")
                        link_element = result.select_one("a")
                        
                        if title_element and link_element:
                            title = title_element.text
                            link = link_element.get("href")
                            
                            # Extract snippet if available
                            snippet_element = result.select_one("div.VwiC3b")
                            snippet = snippet_element.text if snippet_element else "No description available"
                            
                            # Create result dictionary
                            result_dict = {
                                "title": title,
                                "link": link,
                                "snippet": snippet,
                                "source": "linkedin",
                                "platform": "linkedin"
                            }
                            
                            results.append(result_dict)
                    except Exception as e:
                        print(f"Error extracting LinkedIn result: {e}")
                        continue
        except Exception as e:
            print(f"Error searching LinkedIn: {e}")
        
        return results
    
    def search_twitter(self, search_query: str, limit: int) -> List[Dict]:
        """
        Search Twitter for potential leads.
        
        Args:
            search_query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of search results from Twitter
        """
        results = []
        
        try:
            # Construct search URL for Twitter profiles
            search_terms = search_query.replace(" ", "%20")
            url = f"https://www.google.com/search?q=site:twitter.com+{search_terms}"
            
            # Set random user agent
            headers = {"User-Agent": random.choice(self.user_agents)}
            
            # Make request
            response = self.session.get(url, headers=headers, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract search results
                search_results = soup.select("div.g")
                
                for result in search_results[:limit]:
                    try:
                        # Extract title and link
                        title_element = result.select_one("h3")
                        link_element = result.select_one("a")
                        
                        if title_element and link_element:
                            title = title_element.text
                            link = link_element.get("href")
                            
                            # Skip if not a profile
                            if "/status/" in link:
                                continue
                                
                            # Extract snippet if available
                            snippet_element = result.select_one("div.VwiC3b")
                            snippet = snippet_element.text if snippet_element else "No description available"
                            
                            # Create result dictionary
                            result_dict = {
                                "title": title,
                                "link": link,
                                "snippet": snippet,
                                "source": "twitter",
                                "platform": "twitter"
                            }
                            
                            results.append(result_dict)
                    except Exception as e:
                        print(f"Error extracting Twitter result: {e}")
                        continue
        except Exception as e:
            print(f"Error searching Twitter: {e}")
        
        return results
    
    def search_instagram(self, search_query: str, limit: int) -> List[Dict]:
        """
        Search Instagram for potential leads.
        
        Args:
            search_query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of search results from Instagram
        """
        results = []
        
        try:
            # Construct search URL for Instagram profiles
            search_terms = search_query.replace(" ", "%20")
            url = f"https://www.google.com/search?q=site:instagram.com+{search_terms}"
            
            # Set random user agent
            headers = {"User-Agent": random.choice(self.user_agents)}
            
            # Make request
            response = self.session.get(url, headers=headers, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract search results
                search_results = soup.select("div.g")
                
                for result in search_results[:limit]:
                    try:
                        # Extract title and link
                        title_element = result.select_one("h3")
                        link_element = result.select_one("a")
                        
                        if title_element and link_element:
                            title = title_element.text
                            link = link_element.get("href")
                            
                            # Skip if not a profile
                            if "/p/" in link or "/explore/" in link:
                                continue
                                
                            # Extract snippet if available
                            snippet_element = result.select_one("div.VwiC3b")
                            snippet = snippet_element.text if snippet_element else "No description available"
                            
                            # Create result dictionary
                            result_dict = {
                                "title": title,
                                "link": link,
                                "snippet": snippet,
                                "source": "instagram",
                                "platform": "instagram"
                            }
                            
                            results.append(result_dict)
                    except Exception as e:
                        print(f"Error extracting Instagram result: {e}")
                        continue
        except Exception as e:
            print(f"Error searching Instagram: {e}")
        
        return results
    
    def filter_and_score_results(self, results: List[Dict], search_type: str = "social") -> List[Dict]:
        """
        Filter and score social media search results.
        
        Args:
            results: List of search results to filter and score
            search_type: Type of search (default is "social")
            
        Returns:
            Filtered and scored list of results
        """
        # Remove duplicates by URL
        unique_urls = set()
        filtered_results = []
        
        for result in results:
            url = result.get("link", "")
            
            # Skip if already seen
            if url in unique_urls:
                continue
                
            unique_urls.add(url)
            
            # Score the result
            score = 50  # Base score
            
            # Boost score for social media profiles
            if "linkedin.com/in/" in url:
                score += 30  # LinkedIn profiles are high quality leads
            elif "twitter.com/" in url and not "/status/" in url:
                score += 25  # Twitter profiles
            elif "instagram.com/" in url and not "/p/" in url:
                score += 20  # Instagram profiles
            elif "facebook.com/" in url and not "/posts/" in url:
                score += 20  # Facebook profiles
                
            # Look for profile indicators in title/snippet
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            
            # Check for professional indicators
            professional_terms = ["professional", "expert", "specialist", "consultant", 
                                 "manager", "director", "founder", "ceo", "owner"]
            
            if any(term in title.lower() or term in snippet.lower() for term in professional_terms):
                score += 15
                
            # Add the score to the result
            result["quality_score"] = score
            filtered_results.append(result)
            
        # Sort by quality score (highest first)
        sorted_results = sorted(filtered_results, key=lambda x: x.get("quality_score", 0), reverse=True)
        
        return sorted_results
