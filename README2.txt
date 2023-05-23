Starting The Bot:
To start using the Trading Bot, follow the steps outlined below:

# Step 1: Folder Setup
When you download all the folders, you must open the folder called: "Final_Bot_Binance". 

There you will find the following files: 
"btctusd_bot.py", "rewriting_the_code.py", "credits.py" and "requierements.txt"

# Step 2: API Configuration
Locate the file named credits.py in the folder and open it.
Add your API and API secret keys to the designated fields in the file. These keys are required to connect to the trading platform and execute trades. Make sure to obtain valid keys from Binance.
Save and close the credits.py file.

Step 3: Installation
Open the terminal or command prompt in your development environment.

Run the following command to install the required dependencies:
pip install -r requirements.txt
--- IF YOU GET ERRORS AFTER INSTALLING "requirements.txt" ---
1 - pip install --upgrade pip
2 - pip install python-binance
3 - pip install ccxt
4 - pip install pandas
5 - pip install numpy
6 - pip install websocket_client

Step 4: Starting the Application
Depending on your trading preference, open one of the following files:

For paper trading (simulated trading with no real money), open rewriting_the_code.py.
For real trading with actual funds, open btctusd_bot.py.
Before running the chosen file, ensure you have completed Step 2 and configured the API keys in the credits.py file.

Run the selected file. You can use the following command:
python rewriting_the_code.py or python btctusd.py
or just press Ctrl + f5

The program will now start, and a message stating "Connection opened" will appear in the console.
The bot will continuously monitor the market and execute trades when the predefined criteria are met.

Customization
Symbol
By default, the Trading Bot is set to trade with the BTC/TUSD symbol.
If you wish to change the trading symbol, you can modify it within the code of the selected file (rewriting_the_code.py or btctusdt_bot.py).

Time Frame
The Trading Bot operates on a specific time frame, which determines the duration of 
each candlestick used for analysis. You have the option to customize the time frame based on your trading strategy. 
To do this, modify the corresponding parameter within the code of the selected file.



----------------------->                          !DISCLAIMER!                 <----------------------------



IMPORTANT: The Trading Bot is a Prototype. Use at Your Own Risk.

The Trading Bot provided in this project is intended for educational and experimental purposes only. 
It is a prototype designed to demonstrate the concept of automated trading and algorithmic strategies.
By using the Trading Bot, you acknowledge and accept the following:

No Guaranteed Profits: Trading in financial markets involves inherent risks, including the potential for
financial loss. The Trading Bot does not guarantee any profits or specific trading results. The performance of 
the bot is subject to market conditions, algorithmic strategies, and other factors beyond its control.

Not Financial Advice: The information and content provided in this project, 
including the Trading Bot, do not constitute financial advice, investment recommendations, or any form of financial service.
The Trading Bot should not be considered as a substitute for professional financial advice or consultation.
It is your responsibility to conduct thorough research and seek advice from qualified professionals before making any financial decisions.

Risk Disclosure: Trading financial instruments carries a high level of risk and may not be suitable
for all investors. The use of the Trading Bot involves the risk of financial loss. You should carefully consider your
investment objectives, risk tolerance, and financial situation before using the Trading Bot. You are solely responsible for assessing 
the risks associated with your trading activities and accepting the consequences.

No Liability: I, as the creator of the Trading Bot, shall not be held responsible or liable 
for any losses, damages, or expenses incurred as a result of using the Trading Bot. This includes, but is not limited to,
direct or indirect losses, financial loss, trading losses, and any other damages arising from the use or misuse of the Trading Bot.

Simulation and Backtesting: The Trading Bot may utilize simulated or historical market data
for testing and evaluation purposes. The past performance of the bot, whether simulated or historical, is not indicative of future results.
Market conditions can change rapidly, and the Trading Bot's performance in real-time trading may differ significantly from its simulated or historical performance.

User Responsibility: As a user of the Trading Bot, you are solely responsible for your trading decisions and actions. 
You should carefully review and validate the bot's algorithms, strategies, and parameters before initiating any trades.
It is recommended to thoroughly test the Trading Bot in a controlled environment and with simulated funds before using real money.

By using the Trading Bot, you agree to the terms and conditions outlined in this disclaimer. 
If you do not agree with any part of this disclaimer, you should refrain from using the Trading Bot.

Remember that trading in financial markets carries risks, and it is crucial to exercise caution, 
conduct proper research, and seek professional advice. Only trade with funds that you can afford to lose.

If you have any questions or concerns regarding this disclaimer, please seek professional guidance.

Best regards,

Georgi Kirov
My E-mail: georgikirov70@gmail.com
