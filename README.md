A simple assistant agent using OpenRouter API. The assistant agent is allowed to use the provided function/tool to call during its task execution.<br>
There are multiple different versions of script that is present in this project.<br>

Note:<br>
This project has been tested with Python 3.15<br>
Dependencies required can be found in the file "requirements.txt"<br>
Rename the file ".env.example" to ".env" and fill in OPENROUTER_API_KEY with your actual api key<br>
You may change the AI model with a different one that's available in OpenRouter by changing the value of OPENROUTER_MODEL

For "assistant_agent.py":<br>
This script involves the agent using the provided tool 'list_items' to search for the items stored in the database. This is done to answer any of the user's query related to the database and items that are stored there.<br>
Though for the sake of simplicity, this project will simply use a dict variable to store all of the items' information (For real life scenarios, you will most likely use an actual database).<br>
This current version of the script remembers your previously sent messages (as is required due to how the api call is structured due to the usage of 'tools').

For "assistant_agent_v2.py:<br>
This script is pretty much the same as "assistant_agent.py", except that we've increased the scope of the tools it can use to more than just one.<br>
For this version, the call is configured in a way that the agent is allowed to call one or two tools for its needs.