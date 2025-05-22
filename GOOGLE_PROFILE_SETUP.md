# Setting Up Google Profile Search for LangChain AutoMailer

This guide will help you set up a Google Chrome profile to use with the LangChain AutoMailer application to avoid captchas and bans when searching for leads.

## Why Use a Google Profile?

When automating Google searches, you may encounter captchas or temporary bans due to Google's anti-bot measures. Using a logged-in Google profile can help reduce these issues because:

1. Google trusts logged-in accounts more than anonymous searches
2. Your search history and behavior establish you as a legitimate user
3. Google provides personalized results which can be more relevant

## Setup Instructions

### 1. Create a Dedicated Google Account

It's recommended to create a dedicated Google account for this purpose:

1. Go to [Google Account Creation](https://accounts.google.com/signup)
2. Follow the steps to create a new account
3. Complete the profile with realistic information
4. Add a profile picture and fill out basic details

### 2. Set Up a Chrome Profile

1. Open Google Chrome
2. Click on the profile icon in the top-right corner
3. Click "Add" to create a new profile
4. Sign in with your dedicated Google account
5. Use Chrome normally with this profile for a few days to establish a browsing history
6. Perform manual searches related to your target keywords to build search history

### 3. Find Your Chrome Profile Path

#### Windows
1. Type `%LOCALAPPDATA%\Google\Chrome\User Data\` in File Explorer
2. Look for folders named "Profile 1", "Profile 2", etc.
3. The path will be something like: `C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data\Profile 1`

#### macOS
1. The path is typically: `~/Library/Application Support/Google/Chrome/Profile 1`

#### Linux
1. The path is typically: `~/.config/google-chrome/Profile 1`

### 4. Configure LangChain AutoMailer

1. Open your `.env` file
2. Set the following variables:
   ```
   SEARCH_METHOD=google_profile
   GOOGLE_PROFILE_PATH=<your_chrome_profile_path>
   ```
3. Replace `<your_chrome_profile_path>` with the path you found in step 3

## Best Practices to Avoid Bans

1. **Gradual Usage**: Start with a small number of searches per day and gradually increase
2. **Human-like Behavior**: The system includes random delays to mimic human behavior
3. **Avoid Excessive Searches**: Limit to 20-30 searches per day
4. **Diversify Search Patterns**: Vary your search queries and times
5. **Use a VPN**: Consider using a VPN to rotate your IP address

## Troubleshooting

### Chrome Crashes or Doesn't Start
- Make sure Chrome is not already running with the same profile
- Try using a different profile
- Check that the profile path is correct

### Still Getting Captchas
- Use the profile manually for a while to build more trust
- Try logging in to more Google services (YouTube, Gmail, etc.)
- Reduce the frequency of automated searches
- Consider using a different IP address

### Browser Visible During Searches
- The current implementation shows the browser window during searches
- If you want to run it headlessly, you can modify the code to add `chrome_options.add_argument("--headless")` in `lead_finder.py`

## Data Used for Personalized Emails

The system extracts and uses the following data to personalize emails:

1. **Contact Information**: Email addresses and social media handles
2. **Business Details**: Name, business name, professional title, industry
3. **Website Analysis**: Current state of their services, opportunities for improvement, pain points
4. **Service Recommendations**: Personalized service suggestions based on their needs

This data is processed by the LLM to generate highly personalized outreach emails that address the specific needs and opportunities of each lead. 