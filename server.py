import webbrowser, sys, requests, validators, re, sqlite3, nltk
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from collections import Counter
from nltk import word_tokenize, ngrams, pos_tag, ne_chunk
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

final_results = []

def count_top(arr_of_words):
	frequency = Counter(arr_of_words)
	for token, count in frequency.most_common(1):
		return token

def get_bigrams(arr_of_words):
	return list(ngrams(arr_of_words, 2))

def get_trigrams(arr_of_words):
	return list(ngrams(arr_of_words, 3))
	
def eliminiate_garb_words(arr_of_words):
	stemmer = PorterStemmer()
	english_stopwords = stopwords.words('english') # array containing english stopwords
	final_array = []
	for token in arr_of_words:
		stemmed_token = stemmer.stem(token)
		if stemmed_token in english_stopwords or len(stemmed_token)<2:
			continue
		final_array.append(stemmed_token)
	return final_array

def do_search(search_words):
	q = search_words.split(" ")
	headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
	front_door = "http://www.google.com/search?"

	class Result(object):
		def __init__(self):
			self.url = ""
			self.title = ""
			self.content = ""
			
	class FinalResult(object):
		def __init__(self):
			self.url = ""
			self.title = ""
			self.most_common_word = ""
			self.most_common_bigram = ""
			self.most_common_trigram = ""
			self.number_of_nouns = ""
			self.number_of_person = ""
			
	initial_results = []
	
	search_string = ("+").join(q)
	url = front_door+"q="+search_string
	print(url)
	
	r = requests.get(url, headers=headers)
	try:
		r.raise_for_status()
	except Exception as e:
		print("There was a problem performing search on Google: " + e)

	soup = BeautifulSoup(r.content, "lxml")
	all_links = soup.select('.r a')
	r.close()

	for link in all_links:
		link=link['href']
		if (validators.url(link)):
			text_only = ""
			title_only = ""
			result_req = requests.get(link)
			result_soup = BeautifulSoup(result_req.content, "lxml")
			result_text = result_soup.select('p')
			result_title = result_soup.select('h1')
			result_req.close()
			for result in result_text:
				text_only += result.get_text()
			for title in result_title:
				title_only += title.get_text()
			a_result = Result()
			a_result.url = link
			a_result.title = title_only
			a_result.content = text_only
			initial_results.append(a_result)

	for text in initial_results:
		a_final_result = FinalResult()
		tokens = text.content.split(" ");
		
		title = text.title
		url = text.url
		
		part_of_speech_tags = pos_tag(word_tokenize(text.content))
		tag_frequency = Counter(tag for word,tag in part_of_speech_tags)
		
		clean_tokens = eliminiate_garb_words(tokens)
		bigram_tokens = get_bigrams(clean_tokens)
		trigram_tokens = get_trigrams(clean_tokens)
		
		most_common_word = count_top(clean_tokens)
		most_common_bigram = count_top(bigram_tokens)
		most_common_trigram = count_top(trigram_tokens)

		number_of_nouns = tag_frequency["NN"] #same concept for the other tags
		 
		number_of_person = 0

		### for named entity recognition
		for subtree in ne_chunk(part_of_speech_tags).subtrees(): 
			if subtree.label() == "PERSON":
				number_of_person += 1
				
		a_final_result.url = url
		a_final_result.title = title
		a_final_result.most_common_word = most_common_word
		a_final_result.most_common_bigram = most_common_bigram
		a_final_result.most_common_trigram = most_common_trigram
		a_final_result.number_of_nouns = number_of_nouns
		a_final_result.number_of_person = number_of_person

		final_results.append(a_final_result)
	
	return
	
@app.route('/')
def index():
	final_results = []
	return render_template('index.html')
	
@app.route('/perform_search', methods=['GET'])
def perform_search():
	del final_results[:]
	q = request.args.get('q', '')
	do_search(q)
	return render_template('index.html', results = final_results)