# By Jonas Johansson
# For the KoboHUB Dashboard

from requests import get
from requests.exceptions import RequestException
from dataclasses import dataclass
import os
import random
import time

@dataclass
class quote_summary:
    quote_text: str
    quote_author :str

def quoteoftheday():
    quote_data = ""
    try:
        response = get('http://api.quotable.io/random')
        if response.ok:
            quote_body = response.json()
            #quote_body = json.loads(rawresponse)
            #print(rawresponse)
            #print(quote_body['quoteText'])
            #print(quote_body['quoteAuthor'])
            quote_text = quote_body['content']
            quote_author = quote_body['author']
            quote_data = quote_summary(quote_text, quote_author)
    except RequestException as e:
        print("Error getting quote")
        quote_text = ""
        quote_author = ""
        quote_data = quote_summary(quote_text, quote_author)

    return quote_data    

def quotefromfile(file_path:str):
    if os.path.exists(file_path) :
        quote_array = []
        with open(file_path) as my_file:
            for line in my_file:
                quote_array.append(line)
        print(str(len(quote_array))+" quotes loaded...")
        ql = len(quote_array)
        qr_n = random.randint(0,(ql-1))
        quote_text = quote_array[qr_n].split("-")[0]
        quote_author = quote_array[qr_n].split("- ")[1]
    else :
        quote_text = "No quote found"
        quote_author = "CNtablet"
    quote_data = quote_summary(quote_text, quote_author)
    return quote_data


def addquotetofile(ref_file_path:str, file_path:str, n_quote_text:str, n_quote_author:str):
    author_block = ["Joseph Stalin","Putin","Hitler","Karl Marx"]
    quote_array = []
    ref_array = []
    if os.path.exists(ref_file_path) :
        ref_file = open(ref_file_path, 'r')
        for rline in ref_file:
             ref_array.append(rline)
        #print(str(len(ref_array))+" reference quotes loaded from "+ref_file_path)
        ref_file.close
    
    if os.path.exists(file_path) :
        my_file = open(file_path, 'a')
        if any(n_quote_text in word for word in ref_array):
            if not n_quote_author in author_block :
                print("Quote alredy in file "+ref_file_path)
            else:
                print("Author "+n_quote_author+" blocked")
        else:
            print("New quote added to file "+file_path)
            my_file.write("\n"+n_quote_text)
            my_file.write("- "+n_quote_author)
            my_file.close
    else:
        print("Error")

def checkfordupes(file_path:str):
    ref_array = []
    dupes = []
    if os.path.exists(file_path) :
        with open(file_path) as my_file:
            for line in my_file:
                ref_array.append(line)
    cq = 0
    qt = len(ref_array)
    print("Loaded "+str(qt)+" rows")

    while cq < qt: 
        qs = 0   
        while qs < qt :
            #print("is "+ref_array[qs]+" equal to "+ref_array[cq])
            #input("press a key")
            if ref_array[qs] == ref_array[cq]:
                if qs != cq:
                    #print("Found match at line "+str((qs+1)))
                    #print(ref_array[qs])
                    #print(ref_array[cq])
                    dupes.append((qs+1))
            qs +=1
            #print("Checking record "+str(qs)+" against record "+str(cq))
            #input("Next")
        #print("At record "+str(cq)+" of "+str(qt))
        #input("press a key")
        cq +=1
    print(dupes)


