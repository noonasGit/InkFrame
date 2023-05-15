# By Jonas Johansson
# For the KoboHUB Dashboard

from requests import get
from requests.exceptions import RequestException
from dataclasses import dataclass
import os


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

    # DEBUG AREA
    #quote_text = ""
    #quote_author = ""
    #quote_data = quote_summary(quote_text, quote_author)
    # DEBUG AREA



    return quote_data    

def addquotetofile(ref_file_path:str, file_path:str, n_quote_text:str, n_quote_author:str):
    author_block = ["Joseph Stalin","Putin","Hitler","Karl Marx"]
    quote_array = []
    ref_array = []
    if os.path.exists(ref_file_path) :
        ref_file = open(ref_file_path, 'r')
        for rline in ref_file:
             ref_array.append(rline)
        #print(str(len(ref_array))+" reference quotes loaded...")
        ref_file.close
    
    if os.path.exists(file_path) :
        my_file = open(file_path, 'a')
        if any(n_quote_text in word for word in  ref_array):
            if not n_quote_author in author_block :
                print("Quote alredy in file")
            else:
                print("Author "+n_quote_author+" blocked")
        else:
            print("New quote added to file : "+file_path)
            my_file.write("\n"+n_quote_text)
            my_file.write("- "+n_quote_author)
            my_file.close
    else:
        print("Error")
