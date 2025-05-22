"""
Lead Analyzer Module - Analyzes leads and gathers relevant information to personalize outreach.
"""

from typing import Dict, List, Optional
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import requests
from bs4 import BeautifulSoup
import re
import os
import time
import random
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Load environment variables
load_dotenv()

# List of realistic user agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
]

class LeadAnalyzer:
    """
    A class to analyze leads and gather relevant information for personalized outreach.
    """
    
    def __init__(self, use_local_llm: bool = False, service_type: str = "general", local_llm_type: str = "lm_studio"):
        """
        Initialize the LeadAnalyzer.
        
        Args:
            use_local_llm: Whether to use a local LLM instead of OpenAI.
            service_type: Type of service being offered (e.g., "web_development", "design", "marketing")
            local_llm_type: Type of local LLM to use ("ollama" or "lm_studio")
        """
        if use_local_llm:
            if local_llm_type == "ollama":
                from langchain_community.llms import Ollama
                self.llm = Ollama(model="llama3")
            elif local_llm_type == "lm_studio":
                # LM Studio typically runs on localhost:1234 and exposes an OpenAI-compatible API
                base_url = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model_name="local-model", # This can be any string for LM Studio
                    openai_api_key="lm-studio", # This can be any non-empty string
                    openai_api_base=base_url,
                    temperature=0.2
                )
        else:
            self.llm = ChatOpenAI(temperature=0.2)
        
        self.service_type = service_type
        self.driver = None
        self.profile_path = os.getenv("GOOGLE_PROFILE_PATH", "")
    
    def _init_browser(self):
        """
        Initialize the browser for web scraping if not already initialized.
        """
        if self.driver is None:
            chrome_options = Options()
            
            # Use an existing Chrome profile to maintain login state if available
            if self.profile_path:
                chrome_options.add_argument(f"user-data-dir={self.profile_path}")
            
            # Additional options to make Chrome more stable for automation
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--remote-debugging-port=9222")
            
            # Add a realistic user agent - rotate between options
            user_agent = random.choice(USER_AGENTS)
            chrome_options.add_argument(f"--user-agent={user_agent}")
            
            # Initialize the driver
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    def analyze_website_content(self, url: str) -> Dict:
        """
        Analyze website content to identify potential improvements or services needed.
        
        Args:
            url: The URL to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Check if URL is valid
            if not url or not url.startswith(('http://', 'https://')):
                return {"url": url, "error": "Invalid URL"}
            
            # Initialize browser if needed
            self._init_browser()
            
            print(f"Analyzing website content from {url}")
            
            # Navigate to the URL with the browser for a more accurate rendering
            try:
                self.driver.get(url)
                
                # Wait for page to load
                time.sleep(random.uniform(3, 5))
                
                # Extract text content
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Get the title
                title = self.driver.title
                
                # Extract meta description if available
                meta_desc = ""
                meta_tag = soup.find("meta", {"name": "description"})
                if meta_tag and meta_tag.get("content"):
                    meta_desc = meta_tag.get("content")
                
                # Extract text content from main elements
                main_content = ""
                for element in soup.find_all(["main", "article", "section", "div.content", "div.main"]):
                    main_content += element.get_text() + "\n\n"
                
                if not main_content:
                    # Fallback to body content
                    main_content = soup.body.get_text() if soup.body else ""
                
                # Clean up text
                text_content = re.sub(r'\s+', ' ', main_content).strip()
                
                # Try to find contact information
                contact_elements = soup.find_all(string=re.compile(r'contact|email|phone|call us', re.I))
                contact_text = ""
                for element in contact_elements:
                    if element.parent:
                        contact_section = element.parent.get_text()
                        contact_text += contact_section + "\n"
                
                # Add screenshots for visual analysis
                # This would be ideal but requires more complex handling
                # Instead, we'll simulate visual analysis with content analysis
                
                # Try to identify key business information
                about_elements = soup.find_all(string=re.compile(r'about us|about|mission|vision|team|story', re.I))
                about_text = ""
                for element in about_elements:
                    if element.parent:
                        about_section = element.parent.get_text()
                        about_text += about_section + "\n"
                
                # Try to identify products or services
                service_elements = soup.find_all(string=re.compile(r'services|products|what we do|offering', re.I))
                service_text = ""
                for element in service_elements:
                    if element.parent:
                        service_section = element.parent.get_text()
                        service_text += service_section + "\n"
                
                # Combine all relevant content
                combined_content = f"Title: {title}\n\nMeta Description: {meta_desc}\n\nAbout: {about_text}\n\nServices: {service_text}\n\nContact: {contact_text}\n\nMain Content Sample: {text_content[:2000]}"
                
                # Truncate content to avoid token limits
                truncated_content = combined_content[:4000]
                
                # Add random delay to avoid detection
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"Browser-based analysis failed: {e}")
                print("Falling back to requests method...")
                
                # Fall back to traditional request method
                response = requests.get(url, timeout=10, 
                                        headers={'User-Agent': random.choice(USER_AGENTS)})
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract text content
                text_content = soup.get_text()
                
                # Truncate content to avoid token limits
                truncated_content = text_content[:3000]
            
            # Use LLM to analyze website content
            prompt = PromptTemplate(
                input_variables=["content", "url", "service_type"],
                template="""
                You are a professional business analyst specializing in identifying opportunities for service providers.
                
                Analyze the following website content from {url} and identify:
                1. Current state of their {service_type} (if visible)
                2. Potential opportunities for improvement
                3. Specific pain points or challenges they might be facing
                4. How professional services could benefit this business
                5. Specific needs they might have related to {service_type}
                6. Any information about their industry, target market, or business goals
                
                Website content: {content}
                
                Return a JSON object with these fields:
                - business_name: The name of the business if you can identify it
                - industry: The industry or niche the business appears to be in
                - current_state: Brief assessment of their current {service_type}
                - opportunities: List of 3-5 specific opportunities for improvement
                - pain_points: List of 3-5 potential pain points or challenges
                - benefits: List of 3-5 benefits professional services could provide
                - specific_needs: List of 3-5 specific needs they might have
                - target_audience: Their apparent target audience or customer base
                """
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            result = chain.invoke({"content": truncated_content, "url": url, "service_type": self.service_type})
            
            # Try to parse LLM output
            try:
                analysis = json.loads(result["text"])
            except:
                # If parsing fails, try to extract JSON from the text
                json_match = re.search(r'(\{.*\})', result["text"], re.DOTALL)
                if json_match:
                    try:
                        analysis = json.loads(json_match.group(1))
                    except:
                        analysis = {"raw_analysis": result["text"]}
                else:
                    analysis = {"raw_analysis": result["text"]}
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing website content from {url}: {e}")
            return {"url": url, "error": str(e)}
    
    def analyze_social_profile(self, url: str, platform: str = None) -> Dict:
        """
        Analyze social media profile to identify potential improvements.
        
        Args:
            url: The URL of the social profile
            platform: The social media platform (auto-detected if not provided)
            
        Returns:
            Dictionary containing analysis results
        """
        # Detect platform from URL if not provided
        if not platform:
            if "instagram.com" in url:
                platform = "instagram"
            elif "linkedin.com" in url:
                platform = "linkedin"
            elif "facebook.com" in url:
                platform = "facebook"
            elif "twitter.com" in url or "x.com" in url:
                platform = "twitter"
            else:
                platform = "unknown"
        
        try:
            # Initialize browser if needed
            self._init_browser()
            
            print(f"Analyzing {platform} profile at {url}")
            
            profile_data = {}
            
            # Navigate to the URL
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(random.uniform(3, 5))
            
            # Extract content based on platform
            if platform == "instagram":
                # Extract Instagram profile data
                try:
                    # Get username
                    username_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "h2"))
                    )
                    username = username_element.text if username_element else ""
                    
                    # Get bio
                    bio_element = self.driver.find_element(By.CSS_SELECTOR, "div.-vDIg > span")
                    bio = bio_element.text if bio_element else ""
                    
                    # Get follower count
                    follower_element = self.driver.find_element(By.CSS_SELECTOR, "span.g47SY")
                    follower_count = follower_element.text if follower_element else ""
                    
                    # Get recent posts (first 6-8)
                    post_elements = self.driver.find_elements(By.CSS_SELECTOR, "div._9AhH0")
                    posts = []
                    for i, post in enumerate(post_elements[:6]):
                        try:
                            post.click()
                            time.sleep(random.uniform(1, 2))
                            
                            # Get post text
                            text_element = WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "div.C4VMK > span"))
                            )
                            post_text = text_element.text if text_element else ""
                            
                            posts.append(post_text)
                            
                            # Close post
                            close_button = self.driver.find_element(By.CSS_SELECTOR, "button.ckWGn")
                            close_button.click()
                            time.sleep(random.uniform(0.5, 1))
                        except:
                            continue
                    
                    profile_data = {
                        "username": username,
                        "bio": bio,
                        "follower_count": follower_count,
                        "recent_posts": posts
                    }
                    
                except Exception as e:
                    # Fall back to page source analysis
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    page_text = soup.get_text()
                    profile_data = {
                        "page_text": page_text[:3000]
                    }
            
            elif platform == "linkedin":
                # Extract LinkedIn profile data
                try:
                    # Get profile headline
                    headline_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.text-body-medium"))
                    )
                    headline = headline_element.text if headline_element else ""
                    
                    # Get about section
                    about_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.display-flex.ph5.pv3")
                    about = ""
                    for element in about_elements:
                        if "About" in element.text:
                            about = element.text
                            break
                    
                    # Get experience
                    experience_elements = self.driver.find_elements(By.CSS_SELECTOR, "li.artdeco-list__item")
                    experience = []
                    for element in experience_elements:
                        experience.append(element.text)
                    
                    profile_data = {
                        "headline": headline,
                        "about": about,
                        "experience": experience
                    }
                    
                except Exception as e:
                    # Fall back to page source analysis
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    page_text = soup.get_text()
                    profile_data = {
                        "page_text": page_text[:3000]
                    }
            
            else:
                # Generic analysis for other platforms
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                page_text = soup.get_text()
                
                # Clean up text
                text_content = re.sub(r'\s+', ' ', page_text).strip()
                
                profile_data = {
                    "platform": platform,
                    "page_text": text_content[:3000]
                }
            
            # Use LLM to analyze social profile
            profile_data_str = json.dumps(profile_data)
            
            prompt = PromptTemplate(
                input_variables=["platform", "profile_data", "service_type"],
                template="""
                You are a professional business analyst specializing in identifying opportunities for service providers.
                
                Analyze this {platform} profile data and identify:
                1. Potential opportunities for improved {service_type}
                2. Common issues businesses face on {platform} related to {service_type}
                3. How professional services could improve their presence
                4. Specific content or strategies that would perform well for them
                5. Their target audience and business focus based on the profile
                
                Profile data: {profile_data}
                
                Return a JSON object with these fields:
                - opportunities: List of 3-5 specific opportunities for improvement
                - common_issues: List of 3-5 common issues related to {service_type}
                - service_benefits: List of 3-5 ways professional services could help
                - recommended_strategies: List of 3-5 specific strategies that would perform well
                - target_audience: Their apparent target audience based on the profile
                - business_focus: The main focus or offerings of the business
                """
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            result = chain.invoke({
                "platform": platform, 
                "profile_data": profile_data_str, 
                "service_type": self.service_type
            })
            
            # Try to parse LLM output
            try:
                analysis = json.loads(result["text"])
            except:
                # If parsing fails, try to extract JSON from the text
                json_match = re.search(r'(\{.*\})', result["text"], re.DOTALL)
                if json_match:
                    try:
                        analysis = json.loads(json_match.group(1))
                    except:
                        analysis = {"raw_analysis": result["text"]}
                else:
                    analysis = {"raw_analysis": result["text"]}
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing {platform} profile from {url}: {e}")
            
            # Fall back to prompt-based analysis without live data
            handle = url.split("/")[-1]
            prompt = PromptTemplate(
                input_variables=["platform", "handle", "service_type"],
                template="""
                You are a professional business analyst specializing in identifying opportunities for service providers.
                
                Imagine you're analyzing a {platform} profile with the handle {handle}.
                
                Based on common patterns seen on {platform}, create a hypothetical analysis that includes:
                1. Potential opportunities for improved {service_type}
                2. Common issues businesses face on {platform} related to {service_type}
                3. How professional services could improve their presence
                4. Specific content or strategies that perform well on {platform}
                
                Return a JSON object with these fields:
                - opportunities: List of 3-5 specific opportunities for improvement
                - common_issues: List of 3-5 common issues related to {service_type}
                - service_benefits: List of 3-5 ways professional services could help
                - recommended_strategies: List of 3-5 specific strategies that perform well
                """
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            result = chain.invoke({"platform": platform, "handle": handle, "service_type": self.service_type})
            
            # Try to parse LLM output
            try:
                analysis = json.loads(result["text"])
            except:
                analysis = {"raw_analysis": result["text"]}
            
            analysis["error"] = str(e)
            return analysis
    
    def generate_service_recommendations(self, lead_data: Dict) -> Dict:
        """
        Generate personalized service recommendations based on lead data.
        
        Args:
            lead_data: Dictionary containing lead information
            
        Returns:
            Dictionary containing service recommendations
        """
        # Extract relevant information from lead data
        industry = lead_data.get("industry", "")
        keywords = lead_data.get("keywords", "")
        website_content = lead_data.get("website_analysis", {})
        social_analysis = lead_data.get("social_analysis", {})
        
        # Create a summary of the lead data for the LLM
        lead_summary = {
            "industry": industry,
            "keywords": keywords,
            "website_analysis": website_content,
            "social_analysis": social_analysis
        }
        
        # Use LLM to generate personalized service recommendations
        prompt = PromptTemplate(
            input_variables=["lead_data", "service_type"],
            template="""
            You are a professional {service_type} service provider. Based on the following lead data, 
            recommend specific services that would benefit this potential client.
            
            Lead data: {lead_data}
            
            Return a JSON object with these fields:
            - primary_service: The main service recommendation
            - service_description: Brief description of what this service entails
            - value_proposition: Why this service would be valuable to the client
            - pricing_tier: Recommended pricing tier (Basic, Standard, Premium)
            - additional_services: List of 2-3 complementary services
            - personalized_pitch: A brief, personalized pitch for this specific client
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = chain.invoke({"lead_data": lead_summary, "service_type": self.service_type})
        
        # Try to parse LLM output
        try:
            recommendations = json.loads(result["text"])
        except:
            # If parsing fails, try to extract JSON from the text
            json_match = re.search(r'(\{.*\})', result["text"], re.DOTALL)
            if json_match:
                try:
                    recommendations = json.loads(json_match.group(1))
                except:
                    recommendations = {"raw_recommendations": result["text"]}
            else:
                recommendations = {"raw_recommendations": result["text"]}
        
        return recommendations
    
    def analyze_lead(self, lead_data: Dict) -> Dict:
        """
        Analyze a lead using all available methods.
        
        Args:
            lead_data: Dictionary containing lead information
            
        Returns:
            Enriched lead data with analysis
        """
        enriched_data = lead_data.copy()
        
        # Analyze website if available
        if "link" in lead_data and lead_data["link"]:
            enriched_data["website_analysis"] = self.analyze_website_content(lead_data["link"])
        
        # Analyze social media profiles if available
        social_profiles = []
        
        # Look for social links in the lead data
        if "social_links" in lead_data:
            social_profiles = lead_data["social_links"]
        else:
            # Extract from link field if it's a social media URL
            link = lead_data.get("link", "")
            if any(domain in link for domain in ["instagram.com", "linkedin.com", "facebook.com", "twitter.com", "x.com"]):
                social_profiles.append(link)
        
        # Analyze the social profiles
        social_analyses = {}
        for profile in social_profiles:
            platform = "unknown"
            if "instagram.com" in profile:
                platform = "instagram"
            elif "linkedin.com" in profile:
                platform = "linkedin"
            elif "facebook.com" in profile:
                platform = "facebook"
            elif "twitter.com" in profile or "x.com" in profile:
                platform = "twitter"
            
            analysis = self.analyze_social_profile(profile, platform)
            social_analyses[platform] = analysis
        
        # Add social analysis if found
        if social_analyses:
            enriched_data["social_analysis"] = social_analyses
        
        # Generate service recommendations
        enriched_data["recommendations"] = self.generate_service_recommendations(enriched_data)
        
        return enriched_data
    
    def analyze_leads_from_csv(self, csv_path: str) -> List[Dict]:
        """
        Analyze leads from a CSV file.
        
        Args:
            csv_path: Path to the CSV file containing leads
            
        Returns:
            List of analyzed leads
        """
        from utils.helpers import load_leads_from_csv, export_leads_to_csv
        
        # Load leads from CSV
        leads = load_leads_from_csv(csv_path)
        
        # Analyze each lead
        analyzed_leads = []
        for lead in leads:
            analyzed_lead = self.analyze_lead(lead)
            analyzed_leads.append(analyzed_lead)
        
        # Save the analyzed leads back to a new CSV
        output_path = csv_path.replace(".csv", "_analyzed.csv")
        if output_path == csv_path:
            output_path = csv_path + "_analyzed.csv"
        
        export_leads_to_csv(analyzed_leads, output_path)
        
        return analyzed_leads
    
    def close_browser(self):
        """
        Close the browser if it's open.
        """
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __del__(self):
        """
        Ensure browser is closed when the object is destroyed.
        """
        self.close_browser() 