import praw
import config
import time
import os
import requests
import wikipedia
import nltk
import urllib
import urllib.request
import heapq
from bs4 import BeautifulSoup

sentence_re = r'''(?x)      # set flag to allow verbose regexps
        (?:[A-Z]\.)+        # abbreviations, e.g. U.S.A.
      | \w+(?:-\w+)*        # words with optional internal hyphens
      | \$?\d+(?:\.\d+)?%?  # currency and percentages, e.g. $12.40, 82%
      | \.\.\.              # ellipsis
      | [][.,;"'?():_`-]    # these are separate tokens; includes ], [
    '''
lemmatizer = nltk.WordNetLemmatizer()
from nltk.stem.porter import *
stemmer = PorterStemmer()

#Taken from Su Nam Kim Paper...
grammar = r"""
    NBAR:
        {<NN.*|JJ>*<NN.*>}  # Nouns and Adjectives, terminated with Nouns
        
    NP:
        {<NBAR>}
        {<NBAR><IN><NBAR>}  # Above, connected with in/of/etc...
"""
chunker = nltk.RegexpParser(grammar)


def bot_login():
	print ("Logging in")
	reddit = praw.Reddit(username = config.username,
				password = config.password,
				client_id = config.client_id,
				client_secret = config.client_secret,
				user_agent = "WikiBot1.0")
	print ("Logged in")
	return reddit

from nltk.corpus import stopwords
stopwords = stopwords.words('english')


def leaves(tree):
    """Finds NP (nounphrase) leaf nodes of a chunk tree."""
    for subtree in tree.subtrees(filter = lambda t: t.label()=='NP'):
        yield subtree.leaves()

def normalise(word):
    """Normalises words to lowercase and stems and lemmatizes it."""
    word = word.lower()
    #word = stemmer.stem(word)
    word = lemmatizer.lemmatize(word)
    return word

def acceptable_word(word):
    """Checks conditions for acceptable word: length, stopword."""
    accepted = bool(2 <= len(word) <= 40
        and word.lower() not in stopwords)
    return accepted


def get_terms(tree):
    for leaf in leaves(tree):
        term = [ normalise(w) for w,t in leaf if acceptable_word(w) ]
        yield term

def get_page(url):
    html = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(html, 'html.parser')
    text = ""
    # Kill all script and style elements
    for script in soup.find_all('p'):
        text += script.get_text()
    #Break into lines
    lines = []

    for line in text.splitlines():
        if(len(line) > 10):
            lines.append(line)
   # lines = (line.strip() for line in text.splitlines())

    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    return text

def get_sum(paragraph):


    #Start cleaning the text word by word to prepare for summary
    article = paragraph

    #clean brackets
    article = re.sub(r'\[[0-9]*\]', ' ', article)
    article = re.sub(r'\s+', ' ', article)

    #format article
    formatted_article = re.sub('[^a-zA-Z]', ' ', article)
    formatted_article = re.sub(r'\s+', ' ', formatted_article)

    #Finished preprocessing

    #Start tokenizing article
    sentence_list = nltk.sent_tokenize(article)

    stopwords = nltk.corpus.stopwords.words('english')
    word_frequencies = {}  
    for word in nltk.word_tokenize(formatted_article):  
        if word not in stopwords:
            if word not in word_frequencies.keys():
                word_frequencies[word] = 1
            else:
                word_frequencies[word] += 1
    
    maximum_frequncy = max(word_frequencies.values())

    for word in word_frequencies.keys():  
        word_frequencies[word] = (word_frequencies[word]/maximum_frequncy)

    sentence_scores = {}  
    for sent in sentence_list:  
        for word in nltk.word_tokenize(sent.lower()):
            if word in word_frequencies.keys():
                if len(sent.split(' ')) < 30:
                    if sent not in sentence_scores.keys():
                        sentence_scores[sent] = word_frequencies[word]
                    else:
                        sentence_scores[sent] += word_frequencies[word]

    summary_sentences = heapq.nlargest(10, sentence_scores, key=sentence_scores.get)

    return ' '.join(summary_sentences)


def get_wiki_sum(summary):
    toks = nltk.regexp_tokenize(summary, sentence_re)
    postoks = nltk.tag.pos_tag(toks)

    # print (postoks)

    tree = chunker.parse(postoks)

    terms = get_terms(tree)

    for term in terms:
        if(len(term) > 0):
            
            s = ""
            for word in term:
                s += word + " "

            try:

                pg = wikipedia.page(s)
                wiki_summary = pg.summary
                print("Searching for: " + s + "Found page: " + pg.title)
                print(wiki_summary)
            except wikipedia.exceptions.DisambiguationError as e:
                print("Disambiguation")
            except wikipedia.exceptions.PageError as x:
                print("Page Error")
            except wikipedia.exceptions.WikipediaException as z:
                print("WEIRD ERROR")

reddit = bot_login()
subreddit = reddit.subreddit('news')

url = "http://www.espn.com/tennis/story/_/id/25128160/roger-federer-turned-invitation-play-exhibition-saudi-arabia"

paragraph = get_page(url)
print(paragraph)
summary = get_sum(paragraph)
get_wiki_sum(summary)
