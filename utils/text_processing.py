from bs4 import BeautifulSoup
import glob
from datetime import datetime 
import pandas as pd
import calendar
import requests

import re

import nltk


import nltk
import os
import string
import numpy as np
import copy 
import pickle
import re
import math

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.feature_extraction.text import TfidfTransformer




from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer
from collections import Counter
from num2words import num2words

def save_page(url, file_name):
    
    OUTPUT_FOLDER = 'data/0_isw_data_collection/1_raw_isw_data'
    page = requests.get(url)
    
    url_name = url.split("/")[-1].replace("-","_")
    
    with open(f"{OUTPUT_FOLDER}/{file_name}___{url_name}.html",'wb+') as f:
        f.write(page.content)


def get_article_from_yesterday(d,m,year):
    
    

    month_number = m 
    month_name = calendar.month_name[month_number]
    OUTPUT_FOLDER = 'data/0_isw_data_collection/1_raw_isw_data'

    BASE_URL = "https://understandingwar.org/backgrounder/russian-offensive-campaign-assessment"
    
    file_name = f"{d}_{m}_{year}"
    url = f"{BASE_URL}-{month_name}-{d}-{year}"
    url_name = url.split("/")[-1].replace("-","_")
    
    
    save_page(url,file_name)
    
    return f"{OUTPUT_FOLDER}/{file_name}___{url_name}.html"
    
    
def read_html(file):
    
    all_data=[]
    d = {}
    file_name = file.split("/")[-1].split("___")
    date = datetime.strptime(file_name[0],"%d_%m_%Y")
    url = file_name[1].split(".")[0]
    
    with open(file,"r", encoding='utf8') as cfile:
        parsed_html = BeautifulSoup(cfile.read(),features="lxml")
        
        title = parsed_html.head.find("title").text
        link = parsed_html.head.find("link",attrs={"rel":"canonical"},href=True)
        if parsed_html.head.find("link",attrs={"rel":"canonical"},href=True) is not None:
            link = parsed_html.head.find("link",attrs={"rel":"canonical"},href=True).attrs["href"]
        if parsed_html.body.find('h1', {'class': 'title', 'id': 'page-title'}) is not None:
            text_title = parsed_html.body.find('h1', {'class': 'title', 'id': 'page-title'}).text
        text_main = parsed_html.body.find('div',attrs={"class":"field field-name-body field-type-text-with-summary field-label-hidden"})
    #    print( parsed_html.body.find('h1', {'class': 'title', 'id': 'page-title'}).text)
        
        d = {
            'date': date,
            'short_url': url,
            'title': title,
            'text_title': text_title,
            'full_url': link,
            'main_html': text_main
        }
         
        all_data.append(d)
        
    data = pd.DataFrame(all_data)    
    return data
    
def remove_names_and_dates(page_html_text):

    parsed_html = BeautifulSoup(page_html_text,features="lxml")
    p_lines = parsed_html.findAll('p')
    
    min_sentense_word_count = 13
    p_index = 0
    
    for p_line in p_lines:
      
        
        strong_lines = p_line.findAll('strong')
        if not strong_lines:
            continue 
            
        for s in strong_lines:
            
            if (len((s.text.split(" "))) >= min_sentense_word_count) :
                break
            else:
                p_index += 1
                
                continue
            break
            
        for i in range(0,p_index):
            page_html_text = page_html_text.replace(str(p_lines[i]),"")
            
    return page_html_text
  

    
def remove_one_letter_word(data):
    words = word_tokenize(str(data))
    
    new_text = ""
    for w in words:
        if (len(w) > 1):
            new_text = new_text + " " + w
            
    return new_text

def convert_lower_case(data):
    return np.char.lower(data)

def remove_stop_words(data):
    stop_words = set(stopwords.words('english'))
    stop_stop_words = {"no","not"}
    
    stop_words = stop_words - stop_stop_words
    
    words = word_tokenize(str(data))
    
    new_text = ""
    for w in words:
        if w not in stop_words and len(w) > 1:
            new_text = new_text + " " + w
            
    return new_text


def remove_punctuations(data):
    symbols = " !()-[]{};:'\,<>./?@#$%^&*_~ '"""  
    
    for i in range(len(symbols)):
        data = np.char.replace(data,symbols[i]," ")
        data = np.char.replace(data,"  "," ")
    
    data = np.char.replace(data,",", " ")
    
    return data


def stemming(data):
    stemmer = PorterStemmer()
    
    tokens = word_tokenize(str(data))
    new_text = ""
    for w in tokens:
        new_text = new_text + " " + stemmer.stem(w)
        
    return new_text

def lemmatizing(data):
    lemmatizer = WordNetLemmatizer()
    
    tokens = word_tokenize(str(data))
    new_text = ""
    for w in tokens:
        new_text = new_text + " " + lemmatizer.lemmatize(w)
               
    return new_text


def convert_numbers(data):
    
    tokens = word_tokenize(str(data))
    new_text = ""
    for w in tokens:
        if w.isdigit():
            if int(w) < 1000000000:
                w = num2words(w)
            else:
                w = " "
        new_text = new_text + " " + w
            
    new_text = np.char.replace(new_text,"-"," ")
        
    return new_text


def remove_url_from_string(data):
    words = word_tokenize(str(data))
    new_text = ""

    
    for w in words:
        w = re.sub(r'https?:\/\/.*[\r\n]*',"",str(w),flags=re.MULTILINE)
        w = re.sub(r'http?:\/\/.*[\r\n]*',"",str(w),flags=re.MULTILINE)
        
        new_text = new_text + " " + w
        
    return new_text


def preprocess(data, word_root_algo='lemm'):
    
    data = remove_one_letter_word(data)
    data = convert_lower_case(data)
    data = remove_stop_words(data)
    data = stemming(data)
    data = remove_punctuations(data)
    data = convert_numbers(data)
    data = remove_url_from_string(data)
    
    if word_root_algo =='lemm':
        data = lemmatizing(data)
    else: 
        data = stemming(data)
        
    
    data = remove_punctuations(data)
    data = remove_stop_words(data)
    
    return data


def sort_coo(coo_matrix):
    
    tuples = zip(coo_matrix.col, coo_matrix.data)
    
    return sorted(tuples,key=lambda x: (x[1], x[0]), reverse=True)

def extract_topn_from_vector(feature_names, sorted_items, topn=10):
    
    sorted_items = sorted_items[:topn]
    
    score_vals = []
    feature_vals = []
    
    for idx, score in sorted_items:
        
        score_vals.append(round(score,3))
        feature_vals.append(feature_names[idx])
        
    results = {}
    
    for idx in range(len(feature_vals)):
        results[feature_vals[idx]] = score_vals[idx]
    
    return results


def convert_doc_to_vector(doc,feature_names,tf_idf_vector):
   
    top_n = 10
  
    
    sorted_items = sort_coo(tf_idf_vector.tocoo())
    
    keywords = extract_topn_from_vector(feature_names, sorted_items, top_n)
    
    return keywords
    
                                                                                   
    
    
    

    