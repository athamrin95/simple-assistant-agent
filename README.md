A simple assistant agent using OpenRouter API. The assistant agent is allowed to use the provided function/tool to call during its task execution.<br>

Note:<br>
This project has been tested with Python 3.15<br>
Dependencies required can be found in the file "requirements.txt"<br>
Rename the file ".env.example" to ".env" and fill in OPENROUTER_API_KEY with your actual api key<br>
You may change the AI model with a different one that's available in OpenRouter by changing the value of OPENROUTER_MODEL

Changelog:
- Version 4:<br>
Added the feature to save the state of the message history to an external file called "riwayat.json" when user exits the script by typing "/keluar".<br>
The script will attempt to load back in the saved messages from "riwayat.json" during startup. This would result in the agent still remembering
the user's last two queries before exiting the script previously.<br>

- Version 3:<br>
Added several safeguards for this version. The agent is instructed to only do one round of function/tool call per user query. A safeguard is also added in case if the agent tried to initiate multiple tool calls.<br>
Added a limit to the message history so the agent would remember only the two most recent queries to limit ballooning cost over protracted chat sessions. To showcase this limit to message history, a restriction on
what sort of questions you are allowed to ask of the agent has been lifted.<br>
Added a language instruction for the agent to only reply in Bahasa Indonesia.<br>
Added the "/" local command style prompt. Current local command has:<br>
"/keluar": exit the chat session.<br>
"/history": acts as a debugger tool to see all messages to and from the agent that is currently retained "in-memory".<br>
"/barang:": shows all the item currently stored in the "database".<br>

- Version 2:<br>
Increased the scope of the tools it can use to more than just one.<br>
For this version, the call is configured in a way that the agent is allowed to call one or two tools for its needs.<br>

- Version 1:<br>
This script involves the agent using the provided tool 'list_items' to search for the items stored in the database. This is done to answer any of the user's query related to the database and items that are stored there.<br>
Though for the sake of simplicity, this project will simply use a dict variable to store all of the items' information (For real life scenarios, you will most likely use an actual database).<br>
This current version of the script remembers your previously sent messages (as is required due to how the api call is structured due to the usage of 'tools').

