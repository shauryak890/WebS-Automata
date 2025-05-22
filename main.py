"""
Main entry point for the LangChain AutoMailer application.
"""

import os
import argparse
import json
import time
import re
import csv
from dotenv import load_dotenv
from lead_finder import LeadFinder
from lead_analyzer import LeadAnalyzer
from email_generator import EmailGenerator
import colorama
from colorama import Fore, Style
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Initialize colorama
colorama.init()

# Initialize rich console
console = Console()

# Load environment variables
load_dotenv()

def print_banner():
    """
    Print a fancy banner for the application.
    """
    console.print(Panel("""
[bold blue]██╗      █████╗ ███╗   ██╗ ██████╗  ██████╗██╗  ██╗ █████╗ ██╗███╗   ██╗[/bold blue]
[bold blue]██║     ██╔══██╗████╗  ██║██╔════╝ ██╔════╝██║  ██║██╔══██╗██║████╗  ██║[/bold blue]
[bold blue]██║     ███████║██╔██╗ ██║██║  ███╗██║     ███████║███████║██║██╔██╗ ██║[/bold blue]
[bold blue]██║     ██╔══██║██║╚██╗██║██║   ██║██║     ██╔══██║██╔══██║██║██║╚██╗██║[/bold blue]
[bold blue]███████╗██║  ██║██║ ╚████║╚██████╔╝╚██████╗██║  ██║██║  ██║██║██║ ╚████║[/bold blue]
[bold blue]╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝[/bold blue]
                                                                        
[bold green] █████╗ ██╗   ██╗████████╗ ██████╗ ███╗   ███╗ █████╗ ██╗██╗     ███████╗██████╗ [/bold green]
[bold green]██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗████╗ ████║██╔══██╗██║██║     ██╔════╝██╔══██╗[/bold green]
[bold green]███████║██║   ██║   ██║   ██║   ██║██╔████╔██║███████║██║██║     █████╗  ██████╔╝[/bold green]
[bold green]██╔══██║██║   ██║   ██║   ██║   ██║██║╚██╔╝██║██╔══██║██║██║     ██╔══╝  ██╔══██╗[/bold green]
[bold green]██║  ██║╚██████╔╝   ██║   ╚██████╔╝██║ ╚═╝ ██║██║  ██║██║███████╗███████╗██║  ██║[/bold green]
[bold green]╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚═╝  ╚═╝[/bold green]
""", title="[bold yellow]Lead Generation & Personalized Email Outreach[/bold yellow]", border_style="yellow"))

def get_user_inputs():
    """
    Get interactive inputs from the user.
    """
    print_banner()
    
    console.print("\n[bold]Welcome to LangChain AutoMailer![/bold]")
    console.print("This tool helps you find leads, analyze their needs, and create personalized outreach emails.")
    
    # Ask if user wants to use local LLM
    use_local_llm = questionary.confirm(
        "Do you want to use a local LLM instead of OpenAI?",
        default=True
    ).ask()
    
    local_llm_type = None
    if use_local_llm:
        local_llm_type = questionary.select(
            "Which local LLM provider do you want to use?",
            choices=[
                "lm_studio",
                "ollama"
            ],
            default="lm_studio"
        ).ask()
        
        if local_llm_type == "lm_studio":
            console.print("\n[yellow]Make sure LM Studio is running with a model loaded![/yellow]")
            console.print("[yellow]Default URL: http://localhost:1234/v1[/yellow]")
            console.print("[red]IMPORTANT: Clear any existing text before entering your URL![/red]")
            
            # Ask for the base URL without the /v1 suffix
            lm_studio_base = questionary.text(
                "Enter LM Studio base URL (without /v1):",
                default="http://localhost:1234"
            ).ask()
            
            # Clean up URL - remove any accidental concatenation
            if "http://" in lm_studio_base and lm_studio_base.count("http://") > 1:
                # Keep only the last URL if multiple are concatenated
                parts = lm_studio_base.split("http://")
                if len(parts) > 1:
                    lm_studio_base = "http://" + parts[-1]
            
            # Ensure URL doesn't already have /v1
            if lm_studio_base.endswith("/v1"):
                lm_studio_base = lm_studio_base[:-3]
                
            # Construct the full URL
            lm_studio_url = f"{lm_studio_base}/v1"
            console.print(f"[green]Using LM Studio URL: {lm_studio_url}[/green]")
            os.environ["LM_STUDIO_BASE_URL"] = lm_studio_url
    
    # Ask about search method
    search_method = questionary.select(
        "Which search method would you like to use?",
        choices=[
            "google_profile - Use Google with a logged-in profile (recommended)",
            "serpapi - Use SerpAPI (requires API key)",
            "direct - Use fallback methods"
        ],
        default="google_profile - Use Google with a logged-in profile (recommended)"
    ).ask().split(" - ")[0]
    
    os.environ["SEARCH_METHOD"] = search_method
    
    if search_method == "google_profile":
        console.print("\n[yellow]Google profile search requires a Chrome profile path.[/yellow]")
        console.print("[yellow]See GOOGLE_PROFILE_SETUP.md for instructions.[/yellow]")
        console.print("[red]IMPORTANT: Clear any existing text before entering your path![/red]")
        
        # Get default path based on OS
        default_path = ""
        if os.name == "nt":  # Windows
            default_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data", "Default")
        elif os.name == "posix":  # macOS or Linux
            if os.path.exists("/Applications"):  # macOS
                default_path = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default")
            else:  # Linux
                default_path = os.path.expanduser("~/.config/google-chrome/Default")
        
        profile_path = questionary.text(
            "Enter Chrome profile path:",
            default=default_path
        ).ask()
        
        # Clean up path - remove any accidental concatenation
        if "User Data" in profile_path and profile_path.count("User Data") > 1:
            parts = profile_path.split("User Data")
            if len(parts) > 2:
                # Keep the first occurrence of User Data and the last part
                profile_path = parts[0] + "User Data" + parts[-1]
        
        console.print(f"[green]Using Chrome profile path: {profile_path}[/green]")
        os.environ["GOOGLE_PROFILE_PATH"] = profile_path
    
    # Get service type
    service_type = questionary.text(
        "What type of service are you offering? (e.g., web_development, marketing, design):",
        default="web_development"
    ).ask()
    
    # Get command
    command = questionary.select(
        "What would you like to do?",
        choices=[
            "search - Search for leads",
            "analyze - Analyze leads",
            "email - Generate emails",
            "api - Start API server"
        ]
    ).ask().split(" - ")[0]
    
    return {
        "use_local_llm": use_local_llm,
        "local_llm_type": local_llm_type,
        "service_type": service_type,
        "command": command,
        "search_method": search_method
    }

def interactive_search():
    """
    Interactive search for leads.
    """
    console.print("\n[bold]Search for Leads[/bold]")
    console.print("[yellow]This will search for actual business leads with contact information, not directory listings.[/yellow]")
    
    # Get search parameters
    keywords = questionary.text(
        "Enter keywords to search for (e.g., 'dentist', 'web developer'):",
        default="dentist"
    ).ask()
    
    platform = questionary.text(
        "Enter platform to search on (leave empty for general web search, or specify like 'instagram.com', 'linkedin.com'):",
        default=""
    ).ask()
    
    # Validate platform format
    if platform and not ("." in platform):
        console.print("[red]Warning: Platform should be a domain like 'instagram.com', not just 'instagram'[/red]")
        console.print("[yellow]Using as location filter instead...[/yellow]")
        location = platform
        platform = ""
    else:
        # Get location separately if platform was valid or empty
        location = questionary.text(
            "Enter location to filter by (e.g., 'New York', 'London'):",
            default=""
        ).ask()
    
    contact_info = questionary.text(
        "Enter contact info to search for (helps find emails):",
        default="@gmail.com OR @hotmail.com OR contact OR email"
    ).ask()
    
    limit = questionary.text(
        "Maximum number of results:",
        default="5"
    ).ask()
    
    # Add options for output format
    output_format = questionary.select(
        "Choose output format:",
        choices=[
            "json - Save as JSON file",
            "csv - Save as CSV file",
            "both - Save as both JSON and CSV",
            "none - Display results only"
        ],
        default="both - Save as both JSON and CSV"
    ).ask().split(" - ")[0]
    
    output = ""
    if output_format != "none":
        output = questionary.text(
            "Output file path (without extension):",
            default="leads"
        ).ask()
    
    # Build query parameters
    query_params = {
        "keywords": keywords,
        "limit": int(limit),
        "contact_info": contact_info
    }
    
    if platform:
        query_params["platform"] = platform
    
    if location:
        query_params["location"] = location
    
    return {
        "query_params": query_params,
        "output": output,
        "output_format": output_format
    }

def interactive_analyze():
    """
    Interactive analysis of leads.
    """
    console.print("\n[bold]Analyze Leads[/bold]")
    
    # Get input format and file
    input_format = questionary.select(
        "Choose input format:",
        choices=[
            "json - Analyze leads from JSON file",
            "csv - Analyze leads from CSV file"
        ],
        default="json - Analyze leads from JSON file"
    ).ask().split(" - ")[0]
    
    input_file = questionary.text(
        f"Enter input file with leads (with {input_format} extension):",
        default=f"leads.{input_format}"
    ).ask()
    
    # Add options for visiting social media and websites
    visit_sites = questionary.confirm(
        "Visit websites for deeper analysis?",
        default=True
    ).ask()
    
    visit_social = questionary.confirm(
        "Visit social media profiles for deeper analysis?",
        default=True
    ).ask()
    
    # Get output format
    output_format = questionary.select(
        "Choose output format:",
        choices=[
            "json - Save as JSON file",
            "csv - Save as CSV file",
            "both - Save as both JSON and CSV",
            "none - Display results only"
        ],
        default="both - Save as both JSON and CSV"
    ).ask().split(" - ")[0]
    
    output = ""
    if output_format != "none":
        output = questionary.text(
            "Output file path (without extension):",
            default="analyzed_leads"
        ).ask()
    
    return {
        "input": input_file,
        "input_format": input_format,
        "output": output,
        "output_format": output_format,
        "visit_sites": visit_sites,
        "visit_social": visit_social
    }

def interactive_email():
    """
    Interactive email generation.
    """
    console.print("\n[bold]Generate Emails[/bold]")
    
    # Get input format and file
    input_format = questionary.select(
        "Choose input format:",
        choices=[
            "json - Generate emails from JSON file",
            "csv - Generate emails from CSV file"
        ],
        default="json - Generate emails from JSON file"
    ).ask().split(" - ")[0]
    
    input_file = questionary.text(
        f"Enter input file with analyzed leads (with {input_format} extension):",
        default=f"analyzed_leads.{input_format}"
    ).ask()
    
    # Get email template options
    use_advanced_templates = questionary.confirm(
        "Use advanced templates with social media and website insights?",
        default=True
    ).ask()
    
    variations = questionary.text(
        "Number of email variations per lead:",
        default="2"
    ).ask()
    
    # Get output format
    output_format = questionary.select(
        "Choose output format:",
        choices=[
            "json - Save as JSON file",
            "csv - Save as CSV file",
            "both - Save as both JSON and CSV",
            "none - Display results only"
        ],
        default="both - Save as both JSON and CSV"
    ).ask().split(" - ")[0]
    
    output = ""
    if output_format != "none":
        output = questionary.text(
            "Output file path (without extension):",
            default="generated_emails"
        ).ask()
    
    return {
        "input": input_file,
        "input_format": input_format,
        "output": output,
        "output_format": output_format,
        "variations": int(variations),
        "use_advanced_templates": use_advanced_templates
    }

def interactive_api():
    """
    Interactive API server setup.
    """
    console.print("\n[bold]Start API Server[/bold]")
    
    # Get host and port
    host = questionary.text(
        "Enter host to bind to:",
        default="127.0.0.1"
    ).ask()
    
    port = questionary.text(
        "Enter port to bind to:",
        default="8000"
    ).ask()
    
    return {
        "host": host,
        "port": int(port)
    }

def main():
    """
    Main entry point for the application.
    """
    # Get user inputs
    inputs = get_user_inputs()
    
    # Set environment variables
    os.environ["SERVICE_TYPE"] = inputs["service_type"]
    os.environ["USE_LOCAL_LLM"] = str(inputs["use_local_llm"]).lower()
    
    # Execute command
    if inputs["command"] == "search":
        search_params = interactive_search()
        search_leads(inputs, search_params)
    elif inputs["command"] == "analyze":
        analyze_params = interactive_analyze()
        analyze_leads(inputs, analyze_params)
    elif inputs["command"] == "email":
        email_params = interactive_email()
        generate_emails(inputs, email_params)
    elif inputs["command"] == "api":
        api_params = interactive_api()
        start_api(inputs, api_params)
    else:
        console.print("[bold red]Invalid command![/bold red]")

def search_leads(inputs, params):
    """
    Search for leads based on parameters.
    """
    query_params = params["query_params"]
    output = params["output"]
    output_format = params["output_format"]
    
    # Determine platform for display
    platform_text = query_params.get("platform", "the web")
    if not platform_text:
        platform_text = "the web"
    
    console.print(f"\n[bold]Searching for {query_params['keywords']} leads on {platform_text}...[/bold]")
    console.print("[yellow]This may take a few minutes as we search for and analyze individual business websites.[/yellow]")
    
    # Check if LM Studio is available if using local LLM
    if inputs.get("use_local_llm") and inputs.get("local_llm_type") == "lm_studio":
        try:
            import requests
            lm_studio_url = os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
            # Try a simple models list request to check if LM Studio is running
            response = requests.get(f"{lm_studio_url}/models")
            if response.status_code == 200:
                console.print("[green]LM Studio is available[/green]")
                models = response.json()
                if "data" in models and len(models["data"]) > 0:
                    console.print(f"[green]Found {len(models['data'])} models loaded in LM Studio[/green]")
                else:
                    console.print("[yellow]Warning: No models loaded in LM Studio. Please load a model in the LM Studio interface.[/yellow]")
                    console.print("[green]Will use rule-based extraction instead of LLM[/green]")
            elif response.status_code == 404 and "No models loaded" in response.text:
                console.print("[yellow]LM Studio is running but no models are loaded.[/yellow]")
                console.print("[green]Will use rule-based extraction instead of LLM[/green]")
                # Print instructions for loading models
                console.print("[blue]To load models in LM Studio:[/blue]")
                console.print("[blue]1. Open LM Studio application[/blue]")
                console.print("[blue]2. Go to the Models tab[/blue]")
                console.print("[blue]3. Download or select a model and click 'Load'[/blue]")
            else:
                console.print(f"[red]Warning: LM Studio returned status code {response.status_code}. Contact extraction will use rule-based methods only.[/red]")
                try:
                    error_info = response.json()
                    console.print(f"[red]Error testing LM Studio: {error_info}[/red]")
                except:
                    console.print(f"[red]Error testing LM Studio: {response.text}[/red]")
        except Exception as e:
            console.print(f"[red]Warning: Could not connect to LM Studio: {e}. Contact extraction will use rule-based methods only.[/red]")
    
    # Initialize lead finder
    lead_finder = LeadFinder(
        use_local_llm=inputs["use_local_llm"],
        local_llm_type=inputs["local_llm_type"]
    )
    
    # Set search method - prioritize google_profile for better results
    search_method = inputs.get("search_method", "google_profile")
    os.environ["SEARCH_METHOD"] = search_method
    
    console.print(f"[cyan]Using search method: {search_method}[/cyan]")
    
    try:
        # Search for leads and extract contact information in one step
        csv_output = None
        if output_format in ["csv", "both"] and output:
            csv_output = f"{output}.csv"
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task("[cyan]Searching for leads and extracting contact info...", total=None)
            # Use the combined function that both searches and extracts contact info
            enriched_leads = lead_finder.find_and_extract_leads(query_params, csv_output)
            progress.update(task, completed=True)
        
        console.print(f"[green]Found {len(enriched_leads)} leads.[/green]")
        
        # Display results in a table
        table = Table(title="Found Leads")
        table.add_column("Title/Business", style="cyan", no_wrap=False)
        table.add_column("Link", style="blue", no_wrap=False)
        table.add_column("Emails", style="green", no_wrap=False)
        table.add_column("Phone", style="yellow", no_wrap=False)
        table.add_column("Source", style="magenta", no_wrap=False)
        
        for lead in enriched_leads:
            title = lead.get("business_name", "") or lead.get("title", "")
            emails = ", ".join(lead.get("emails", []))
            phones = ", ".join(lead.get("phones", []))
            source = lead.get("source", "")
            
            table.add_row(
                title[:50] + "..." if len(title) > 50 else title,
                lead.get("link", "")[:50] + "..." if len(lead.get("link", "")) > 50 else lead.get("link", ""),
                emails[:50] + "..." if len(emails) > 50 else emails if emails else "None",
                phones if phones else "None",
                source
            )
        
        console.print(table)
        
        # Save results as JSON if requested
        if output_format in ["json", "both"] and output:
            json_output = f"{output}.json"
            with open(json_output, "w") as f:
                json.dump(enriched_leads, f, indent=2)
            console.print(f"[green]Saved leads to {json_output}[/green]")
        
        # CSV output is handled directly in the find_and_extract_leads method
        if csv_output:
            console.print(f"[green]Saved leads to {csv_output}[/green]")
            
        return enriched_leads
    finally:
        # Close the browser when done
        lead_finder.close_browser()

def analyze_leads(inputs, params):
    """
    Analyze leads based on parameters.
    """
    input_file = params["input"]
    input_format = params.get("input_format", "json")
    output = params["output"]
    output_format = params.get("output_format", "json")
    visit_sites = params.get("visit_sites", True)
    visit_social = params.get("visit_social", True)
    
    console.print(f"\n[bold]Analyzing leads from {input_file} for {inputs['service_type']} services...[/bold]")
    
    # Initialize lead analyzer
    analyzer = LeadAnalyzer(
        use_local_llm=inputs["use_local_llm"],
        service_type=inputs["service_type"],
        local_llm_type=inputs["local_llm_type"]
    )
    
    try:
        # Load leads from file based on format
        if input_format == "csv":
            from utils.helpers import load_leads_from_csv
            leads = load_leads_from_csv(input_file)
        else:
            # Default to JSON
            with open(input_file, "r") as f:
                leads = json.load(f)
        
        console.print(f"[green]Loaded {len(leads)} leads.[/green]")
        
        # Define analyzer based on parameters
        if input_format == "csv" and visit_sites:
            # For CSV input and visiting sites, use the dedicated method
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=False
            ) as progress:
                task = progress.add_task("[cyan]Analyzing leads...", total=None)
                analyzed_leads = analyzer.analyze_leads_from_csv(input_file)
                progress.update(task, completed=True)
        else:
            # Analyze each lead individually
            analyzed_leads = []
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=False
            ) as progress:
                task = progress.add_task("[cyan]Analyzing leads...", total=len(leads))
                
                for i, lead in enumerate(leads):
                    progress.update(task, description=f"[cyan]Analyzing lead {i+1}/{len(leads)}...")
                    
                    # Skip website and social analysis if requested
                    if not visit_sites and "website_analysis" in lead:
                        del lead["website_analysis"]
                    
                    if not visit_social and "social_analysis" in lead:
                        del lead["social_analysis"]
                    
                    analyzed_lead = analyzer.analyze_lead(lead)
                    analyzed_leads.append(analyzed_lead)
                    progress.update(task, advance=1)
        
        # Display results
        table = Table(title="Analyzed Leads")
        table.add_column("Title/Name", style="cyan")
        table.add_column("Business", style="yellow")
        table.add_column("Industry", style="blue")
        table.add_column("Primary Service", style="green")
        table.add_column("Opportunities", style="magenta")
        
        for lead in analyzed_leads:
            title = lead.get("title", "") or lead.get("name", "")
            business = lead.get("business_name", "")
            
            # Try to extract industry from website analysis
            industry = ""
            if "website_analysis" in lead and isinstance(lead["website_analysis"], dict):
                industry = lead["website_analysis"].get("industry", "")
            
            # Get primary service recommendation
            primary_service = ""
            if "recommendations" in lead and isinstance(lead["recommendations"], dict):
                primary_service = lead["recommendations"].get("primary_service", "")
            
            # Get opportunities
            opportunities = []
            if "website_analysis" in lead and isinstance(lead["website_analysis"], dict) and "opportunities" in lead["website_analysis"]:
                website_opps = lead["website_analysis"]["opportunities"]
                if isinstance(website_opps, list):
                    opportunities.extend(website_opps[:2])
            
            opps_text = "\n".join(opportunities[:2]) if opportunities else "None found"
            
            table.add_row(
                title,
                business if business else "Unknown",
                industry if industry else "Unknown",
                primary_service if primary_service else "General services",
                opps_text
            )
        
        console.print(table)
        
        # Save results based on format
        if output_format in ["json", "both"] and output:
            json_output = f"{output}.json"
            with open(json_output, "w") as f:
                json.dump(analyzed_leads, f, indent=2)
            console.print(f"[green]Saved analyzed leads to {json_output}[/green]")
        
        if output_format in ["csv", "both"] and output:
            csv_output = f"{output}.csv"
            from utils.helpers import export_leads_to_csv
            export_leads_to_csv(analyzed_leads, csv_output)
            console.print(f"[green]Saved analyzed leads to {csv_output}[/green]")
            
        return analyzed_leads
    finally:
        # Close the browser when done
        analyzer.close_browser()

def generate_emails(inputs, params):
    """
    Generate emails based on parameters.
    """
    input_file = params["input"]
    input_format = params.get("input_format", "json")
    output = params["output"]
    output_format = params.get("output_format", "json")
    variations = params["variations"]
    use_advanced_templates = params.get("use_advanced_templates", True)
    
    console.print(f"\n[bold]Generating emails for leads in {input_file}...[/bold]")
    
    # Initialize email generator
    email_generator = EmailGenerator(
        use_local_llm=inputs["use_local_llm"],
        service_type=inputs["service_type"],
        local_llm_type=inputs["local_llm_type"]
    )
    
    # Ensure templates exist
    email_generator.create_default_templates()
    
    # Load leads based on format
    if input_format == "csv":
        from utils.helpers import load_leads_from_csv
        leads = load_leads_from_csv(input_file)
    else:
        # Default to JSON
        with open(input_file, "r") as f:
            leads = json.load(f)
    
    console.print(f"[green]Loaded {len(leads)} leads.[/green]")
    
    # Generate emails
    all_emails = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=False
    ) as progress:
        task = progress.add_task("[cyan]Generating emails...", total=len(leads))
        
        for i, lead in enumerate(leads):
            progress.update(task, description=f"[cyan]Generating email for lead {i+1}/{len(leads)}...")
            
            try:
                # Choose between direct method or variations based on parameters
                if input_format == "csv" and use_advanced_templates:
                    # Only generate one email per lead with this method to avoid duplicates
                    # We'll customize it further below if variations > 1
                    emails = [email_generator.generate_email_content(lead, "social_template.txt")]
                else:
                    # Generate variations
                    emails = email_generator.generate_email_variations(lead, variations)
                
                # Add lead info to each email
                for email in emails:
                    email["lead_id"] = i
                    email["lead_name"] = lead.get("name", "") or lead.get("title", "")
                    email["lead_link"] = lead.get("link", "")
                    email["lead_email"] = lead.get("email", "")
                    all_emails.append(email)
                
                # If we need more variations with advanced templates
                if input_format == "csv" and use_advanced_templates and variations > 1:
                    for j in range(1, variations):
                        # Add a variation hint
                        variation_hints = [
                            "Focus on pain points and urgency",
                            "Emphasize case studies and results",
                            "Use a question-based approach",
                            "Focus on ROI and business value"
                        ]
                        
                        template_name = ["basic_template.txt", "personalized_template.txt"][j % 2]
                        lead_copy = lead.copy()
                        hint = variation_hints[j % len(variation_hints)]
                        lead_copy["variation_hint"] = hint
                        
                        email = email_generator.generate_email_content(lead_copy, template_name)
                        email["lead_id"] = i
                        email["lead_name"] = lead.get("name", "") or lead.get("title", "")
                        email["lead_link"] = lead.get("link", "")
                        email["lead_email"] = lead.get("email", "")
                        email["variation"] = hint
                        all_emails.append(email)
                
            except Exception as e:
                console.print(f"[red]Error generating email for lead {i+1}: {e}[/red]")
            
            progress.update(task, advance=1)
    
    console.print(f"[green]Generated {len(all_emails)} emails.[/green]")
    
    # Display results
    table = Table(title="Generated Emails")
    table.add_column("Lead", style="cyan")
    table.add_column("Subject", style="green")
    table.add_column("Email Preview", style="yellow")
    
    for i, email in enumerate(all_emails[:10]):  # Show only the first 10 emails
        lead_name = email.get("lead_name", "") or email.get("to_name", "")
        subject = email.get("subject", "")
        body = email.get("body", "")
        body_preview = body.split("\n\n")[0] + "..." if body else ""
        
        table.add_row(
            lead_name,
            subject,
            body_preview
        )
    
    if len(all_emails) > 10:
        table.caption = f"Showing 10 of {len(all_emails)} emails"
    
    console.print(table)
    
    # Save results based on format
    if output_format in ["json", "both"] and output:
        json_output = f"{output}.json"
        with open(json_output, "w") as f:
            json.dump(all_emails, f, indent=2)
        console.print(f"[green]Saved emails to {json_output}[/green]")
    
    if output_format in ["csv", "both"] and output:
        csv_output = f"{output}.csv"
        with open(csv_output, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["lead_id", "lead_name", "lead_link", "lead_email", 
                         "to_name", "to_business", "subject", "body", "variation"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for email in all_emails:
                writer.writerow(email)
        console.print(f"[green]Saved emails to {csv_output}[/green]")
        
    return all_emails

def start_api(inputs, params):
    """
    Start the API server.
    """
    host = params["host"]
    port = params["port"]
    
    console.print(f"\n[bold]Starting API server on {host}:{port} for {inputs['service_type']} services...[/bold]")
    
    # Set service type environment variable
    os.environ["SERVICE_TYPE"] = inputs["service_type"]
    os.environ["USE_LOCAL_LLM"] = str(inputs["use_local_llm"]).lower()
    if inputs["use_local_llm"] and inputs["local_llm_type"]:
        os.environ["LOCAL_LLM_TYPE"] = inputs["local_llm_type"]
    
    # Import and run the API
    try:
        import uvicorn
        console.print("[yellow]Press Ctrl+C to stop the server[/yellow]")
        uvicorn.run("api:app", host=host, port=port, reload=True)
    except ImportError:
        console.print("[bold red]Error: uvicorn is not installed. Please install it with 'pip install uvicorn'.[/bold red]")

if __name__ == "__main__":
    main() 