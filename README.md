A simple assistant agent using OpenRouter API. The assistant agent is allowed to use the one provided function/tool to call during its task execution.

Note:<br>
This project has been tested with Python 3.15<br>
Dependencies required can be found in the file "requirements.txt"<br>
Rename the file ".env.example" to ".env" and fill in OPENROUTER_API_KEY with your actual api key<br>
You may change the AI model with a different one that's available in OpenRouter by changing the value of OPENROUTER_MODEL

This script involves requiring the agent to use the provided tool 'list_items' to search for the items stored in the database. This is done to answer any of the user's query related to the database and items that are stored there.<br>
Though for the sake of simplicity, this project will simply use a dict variable to store all of the items' information (For real life scenarios, you will most likely use an actual database).<br>
This current version of the script remembers your previously sent messages (as is required due to how the api call is structured due to the usage of 'tools').