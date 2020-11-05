# WikiBot - A python bot for useful information
This bot uses NLTK to analyze and tokenize blocks of text. Using these tokens the bot searches 

wikipedia for the relating article, and provides the summary for each key term.

## Setup:

Install PRAW, and NLTK

`sudo pip3 install praw`

`sudo pip3 install nltk`

install NLTK dependencies

`sudo python3 -m nltk.downloader -d /usr/local/share/nltk_data all`

Run program

`python3 WikiBot.py`

