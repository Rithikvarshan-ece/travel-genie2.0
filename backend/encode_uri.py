import urllib.parse
password = "Rithik@1025"
encoded = urllib.parse.quote_plus(password)
print("Encoded password:", encoded)
print("Full URI:")
print(f"mongodb+srv://Rithik:{encoded}@travelgenie.rinicso.mongodb.net/?appName=TravelGenie")
