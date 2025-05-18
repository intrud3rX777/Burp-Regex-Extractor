🔍 Regex Extractor (Burp Suite Extension)
Regex Extractor is a Burp Suite extension that allows you to extract matches from HTTP responses using custom regular expressions. It provides a user-friendly GUI for creating, saving, and reusing regex patterns, and it can process multiple responses in parallel for efficient data extraction.

✨ Features
. ✅ Extract regex matches from selected HTTP responses
. 💾 Save and manage multiple regex patterns with friendly names
. 📋 Load saved patterns on Burp Suite startup
. 🧹 Automatically deduplicates requests using response length
. 🚀 Fast processing using a background thread (SwingWorker)
. 🧰 Supports GUI-based pattern creation and dropdown selection

🖥️ Installation
1. Clone this repository or download the extension file (regext.py).
2. Open Burp Suite.
3. Go to the Extender tab → Extensions.
4. Click Add → Select Extension type: Python.
5. Load regext.py as the extension file.

💡 Ensure Jython is configured in Burp: Go to Extender → Options → Python Environment → Set path to jython.jar.

🛠️ Usage
1. Open the Regex Extractor tab in Burp Suite.
2. Create a new pattern:
   . Enter a pattern name.
   . Enter the regex (e.g. https?://[^\s"']+).
   . Click "Save Pattern".
3. Interact with a target to capture responses in Burp.
4. Select one or more HTTP requests in the Proxy/HTTP History tab.
5. Right-click → Select "Extract Regex Matches from Responses".
6. Matches will be displayed in the output console at the bottom.

🧠 How It Works
. Extracts only unique HTTP responses (based on response length).
. Runs matching in a background thread to avoid UI freezing.
. Regex patterns are saved to a JSON file named saved_regex_patterns.json.
. Reloads saved patterns every time Burp starts.



