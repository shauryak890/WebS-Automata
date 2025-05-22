"""
Email Generator Module - Generates personalized emails based on lead analysis.
"""

import os
import re
from typing import Dict, List, Optional
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import jinja2
import json
import csv
from utils.helpers import load_leads_from_csv, format_email

# Load environment variables
load_dotenv()

class EmailGenerator:
    """
    A class to generate personalized emails based on lead analysis.
    """
    
    def __init__(self, template_dir: str = "templates", use_local_llm: bool = False, service_type: str = "general", local_llm_type: str = "lm_studio"):
        """
        Initialize the EmailGenerator.
        
        Args:
            template_dir: Directory containing email templates
            use_local_llm: Whether to use a local LLM instead of OpenAI
            service_type: Type of service being offered (e.g., "web_development", "design", "marketing")
            local_llm_type: Type of local LLM to use ("ollama" or "lm_studio")
        """
        self.template_dir = template_dir
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        self.service_type = service_type
        
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
                    temperature=0.7
                )
        else:
            self.llm = ChatOpenAI(temperature=0.7)
    
    def create_default_templates(self):
        """
        Create default email templates if they don't exist.
        """
        os.makedirs(self.template_dir, exist_ok=True)
        
        # Create a basic template
        basic_template = """
Subject: Enhance Your {{ industry }} Business with Professional {{ service_type }}

Hi {{ name }},

I noticed your {{ platform }} account and website, and I'm impressed with your work in the {{ industry }} industry. 

{% if current_state %}
Based on my analysis, I see some opportunities to enhance your {{ service_type }}:
{% for opportunity in opportunities %}
- {{ opportunity }}
{% endfor %}
{% endif %}

Our {{ primary_service }} service could help you:
{% for benefit in benefits %}
- {{ benefit }}
{% endfor %}

I'd love to discuss how we could work together to improve your business.

Would you be available for a quick 15-minute call this week?

Best regards,
{{ sender_name }}
{{ sender_title }}
{{ sender_contact }}
"""
        
        # Write the template to a file
        with open(os.path.join(self.template_dir, "basic_template.txt"), "w") as f:
            f.write(basic_template)
        
        # Create a more personalized template
        personalized_template = """
Subject: {{ personalized_subject }}

Hi {{ name }},

I've been following your work at {{ business_name }} and I'm particularly impressed with your approach to {{ industry }}.

{% if current_state %}
I noticed your current {{ service_type }} and wanted to share some thoughts on how it could be enhanced:

{{ personalized_analysis }}
{% else %}
I noticed some opportunities to improve your {{ service_type }}, and wanted to share how professional services could benefit your business:

{{ personalized_value_proposition }}
{% endif %}

Our {{ primary_service }} service is designed specifically for {{ industry }} professionals like you who want to:
{% for benefit in benefits %}
- {{ benefit }}
{% endfor %}

{{ personalized_pitch }}

I'd love to discuss this further. Would you be available for a quick call this week?

Best regards,
{{ sender_name }}
{{ sender_title }}
{{ sender_contact }}
"""
        
        # Write the template to a file
        with open(os.path.join(self.template_dir, "personalized_template.txt"), "w") as f:
            f.write(personalized_template)
            
        # Create an advanced personalized template with social media insights
        social_template = """
Subject: {{ personalized_subject }}

Hi {{ name }},

I recently came across your {{ business_name }} {{ platform }} profile and website, and I was impressed by your work in the {{ industry }} space.

{% if social_insights %}
I noticed on your social media that {{ social_insights }}. This clearly shows your dedication to quality and customer service.

{% endif %}
{% if website_insights %}
From your website, I could see that {{ website_insights }}. This made me think about how our services could complement your current approach.

{% endif %}
After looking at your online presence, I believe there are some specific opportunities to enhance your {{ service_type }}:

{% for opportunity in opportunities %}
- {{ opportunity }}
{% endfor %}

Our {{ primary_service }} service would be particularly valuable for your business because:
{{ personalized_value_proposition }}

Specifically, we could help you with:
{% for benefit in benefits %}
- {{ benefit }}
{% endfor %}

{{ personalized_pitch }}

I'd love to discuss how we might work together. Would you be available for a brief call this week to explore these ideas further?

Best regards,
{{ sender_name }}
{{ sender_title }}
{{ sender_contact }}
"""
        
        # Write the template to a file
        with open(os.path.join(self.template_dir, "social_template.txt"), "w") as f:
            f.write(social_template)
    
    def generate_email_content(self, lead_data: Dict, template_name: str = "basic_template.txt") -> Dict:
        """
        Generate email content based on lead data and template.
        
        Args:
            lead_data: Dictionary containing lead information
            template_name: Name of the template to use
            
        Returns:
            Dictionary containing email subject and body
        """
        try:
            # Load the template
            template = self.template_env.get_template(template_name)
            
            # Extract relevant information from lead data
            name = lead_data.get("name", "")
            if not name:
                # Try to extract name from title or other fields
                title = lead_data.get("title", "")
                if " - " in title:
                    name = title.split(" - ")[0].strip()
                elif " | " in title:
                    name = title.split(" | ")[0].strip()
                else:
                    name = "there"  # Default fallback
            
            business_name = lead_data.get("business_name", "your business")
            
            # Try to determine industry
            industry = ""
            if "industry" in lead_data:
                industry = lead_data["industry"]
            elif "website_analysis" in lead_data and isinstance(lead_data["website_analysis"], dict):
                industry = lead_data["website_analysis"].get("industry", "")
            
            if not industry:
                # Fall back to keywords or title for industry hints
                keywords = lead_data.get("keywords", "")
                if keywords:
                    industry = keywords.split()[0]  # Just use the first keyword
                else:
                    industry = "your industry"
            
            # Determine platform
            platform = lead_data.get("source", "website").split(".")[0]
            if platform in ["com", "org", "net"]:
                platform = "website"
            
            # Get recommendations and analysis
            recommendations = lead_data.get("recommendations", {})
            website_analysis = lead_data.get("website_analysis", {})
            social_analysis = lead_data.get("social_analysis", {})
            
            # Extract social media insights
            social_insights = ""
            if social_analysis:
                # Try to extract insights from the first available platform
                if isinstance(social_analysis, dict):
                    for platform_data in social_analysis.values():
                        if isinstance(platform_data, dict):
                            # Look for business focus or target audience
                            if "business_focus" in platform_data:
                                social_insights += f"you focus on {platform_data['business_focus']} "
                            if "target_audience" in platform_data:
                                social_insights += f"and target {platform_data['target_audience']} "
                            # Look for content patterns
                            if "recommended_strategies" in platform_data and isinstance(platform_data["recommended_strategies"], list):
                                social_insights += f"and could benefit from {platform_data['recommended_strategies'][0]}"
                            break
            
            # Extract website insights
            website_insights = ""
            if website_analysis and isinstance(website_analysis, dict):
                if "current_state" in website_analysis:
                    website_insights = website_analysis["current_state"]
                elif "target_audience" in website_analysis:
                    website_insights = f"you're targeting {website_analysis['target_audience']}"
            
            # Prepare template variables
            template_vars = {
                "name": name,
                "business_name": business_name,
                "industry": industry,
                "platform": platform,
                "service_type": self.service_type,
                "sender_name": os.getenv("SENDER_NAME", "Your Name"),
                "sender_title": os.getenv("SENDER_TITLE", "Professional Service Provider"),
                "sender_contact": os.getenv("SENDER_CONTACT", "your@email.com | (123) 456-7890"),
                "social_insights": social_insights,
                "website_insights": website_insights
            }
            
            # Add recommendations data
            primary_service = recommendations.get("primary_service", f"{self.service_type.title()} Services")
            template_vars["primary_service"] = primary_service
            
            # Add website analysis data if available
            if "current_state" in website_analysis:
                template_vars["current_state"] = website_analysis["current_state"]
            
            if "opportunities" in website_analysis and isinstance(website_analysis["opportunities"], list):
                template_vars["opportunities"] = website_analysis["opportunities"]
            
            if "benefits" in website_analysis and isinstance(website_analysis["benefits"], list):
                template_vars["benefits"] = website_analysis["benefits"]
            elif "service_benefits" in social_analysis and isinstance(social_analysis["service_benefits"], list):
                template_vars["benefits"] = social_analysis["service_benefits"]
            elif "benefits" in recommendations and isinstance(recommendations["benefits"], list):
                template_vars["benefits"] = recommendations["benefits"]
            else:
                # Fallback benefits
                template_vars["benefits"] = [
                    f"Improve your {self.service_type} to attract more customers",
                    f"Save time and resources with professional {self.service_type}",
                    f"Stand out from competitors with high-quality {self.service_type}"
                ]
            
            # Generate personalized subject and content using LLM
            prompt = PromptTemplate(
                input_variables=["lead_data", "service_type"],
                template="""
                You are a professional email copywriter specializing in outreach for {service_type} services.
                
                Based on the following lead data, create a personalized email subject line and analysis paragraph.
                
                Lead data: {lead_data}
                
                Return a JSON object with these fields:
                - personalized_subject: An attention-grabbing, personalized email subject line
                - personalized_analysis: A paragraph analyzing their current {service_type} and suggesting improvements
                - personalized_value_proposition: A paragraph explaining the value of professional {service_type} for their business
                - personalized_pitch: A brief, compelling pitch paragraph tailored to their specific needs
                """
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            result = chain.invoke({"lead_data": lead_data, "service_type": self.service_type})
            
            # Try to parse LLM output
            try:
                personalization = json.loads(result["text"])
                for key, value in personalization.items():
                    template_vars[key] = value
            except:
                # If parsing fails, try to extract JSON from the text
                json_match = re.search(r'(\{.*\})', result["text"], re.DOTALL)
                if json_match:
                    try:
                        personalization = json.loads(json_match.group(1))
                        for key, value in personalization.items():
                            template_vars[key] = value
                    except:
                        # If still failing, add raw text
                        template_vars["personalized_subject"] = f"Improve Your {industry} {self.service_type}"
                        template_vars["personalized_analysis"] = result["text"]
                else:
                    # If still failing, add raw text
                    template_vars["personalized_subject"] = f"Improve Your {industry} {self.service_type}"
                    template_vars["personalized_analysis"] = result["text"]
            
            # Render the template
            email_body = template.render(**template_vars)
            
            # Extract subject from the first line
            subject_line = email_body.strip().split('\n')[0]
            if subject_line.startswith('Subject:'):
                subject = subject_line[8:].strip()
                # Remove the Subject line from the body
                email_body = email_body.replace(subject_line, '', 1).strip()
            else:
                subject = template_vars.get("personalized_subject", f"Improve Your {industry} {self.service_type}")
            
            return {
                "subject": subject,
                "body": email_body,
                "to_name": name,
                "to_business": business_name
            }
            
        except Exception as e:
            print(f"Error generating email content: {e}")
            return {
                "subject": f"Error: {str(e)}",
                "body": f"Error generating email content: {str(e)}"
            }
    
    def generate_email_variations(self, lead_data: Dict, num_variations: int = 2) -> List[Dict]:
        """
        Generate multiple variations of emails for a lead.
        
        Args:
            lead_data: Dictionary containing lead information
            num_variations: Number of email variations to generate
            
        Returns:
            List of dictionaries containing email variations
        """
        variations = []
        
        # First variation uses the basic template
        basic_email = self.generate_email_content(lead_data, "basic_template.txt")
        variations.append(basic_email)
        
        # Second variation uses the personalized template
        if num_variations >= 2:
            personalized_email = self.generate_email_content(lead_data, "personalized_template.txt")
            variations.append(personalized_email)
        
        # Third variation uses the social template if social data is available
        if num_variations >= 3 and "social_analysis" in lead_data:
            social_email = self.generate_email_content(lead_data, "social_template.txt")
            variations.append(social_email)
        
        # Additional variations with different prompts
        for i in range(len(variations), num_variations):
            # Create a copy of the lead data to avoid modifying the original
            lead_copy = lead_data.copy()
            
            # Add a variation hint
            variation_hints = [
                "Focus on pain points and urgency",
                "Emphasize case studies and results",
                "Use a question-based approach",
                "Focus on ROI and business value",
                "Use a more casual, friendly tone"
            ]
            
            hint = variation_hints[i % len(variation_hints)]
            lead_copy["variation_hint"] = hint
            
            # Generate a custom email with the hint
            custom_email = self.generate_email_content(lead_copy, "personalized_template.txt")
            custom_email["variation"] = hint
            variations.append(custom_email)
        
        return variations
    
    def generate_emails_from_csv(self, csv_path: str, output_path: Optional[str] = None, 
                               num_variations: int = 1) -> List[Dict]:
        """
        Generate emails for leads loaded from a CSV file.
        
        Args:
            csv_path: Path to the CSV file containing lead data
            output_path: Optional path to save the generated emails
            num_variations: Number of email variations to generate per lead
            
        Returns:
            List of dictionaries containing the generated emails
        """
        # Load leads from CSV
        leads = load_leads_from_csv(csv_path)
        print(f"Loaded {len(leads)} leads from {csv_path}")
        
        # Generate emails
        all_emails = []
        for lead in leads:
            try:
                # Choose template based on available data
                template = "basic_template.txt"
                if "website_analysis" in lead and "social_analysis" in lead:
                    template = "social_template.txt"
                elif "website_analysis" in lead:
                    template = "personalized_template.txt"
                
                # Generate variations
                emails = self.generate_email_variations(lead, num_variations)
                for email in emails:
                    email["lead_id"] = lead.get("id", "")
                    email["lead_link"] = lead.get("link", "")
                    email["lead_email"] = lead.get("email", "")
                    all_emails.append(email)
            except Exception as e:
                print(f"Error generating email for lead: {e}")
        
        # Save to output file if specified
        if output_path:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["lead_id", "lead_link", "lead_email", "to_name", 
                                                     "to_business", "subject", "body", "variation"])
                writer.writeheader()
                for email in all_emails:
                    writer.writerow(email)
            print(f"Saved {len(all_emails)} emails to {output_path}")
        
        return all_emails 