from flask import Flask, render_template
from google.cloud import storage
from gensim.summarization.textcleaner import split_sentences

import os
import datetime
from google.cloud.exceptions import NotFound, Conflict

def group_sentences(sentence_list, size):
    for i in range(0, len(sentence_list), size):
        yield sentence_list[i:i+size]

def create_paragraphs(article_text,paragraph_size):
    sentence_list = split_sentences(article_text)
    sentences_groups_list = group_sentences(sentence_list,4)
    new_article = ""
    for group in sentences_groups_list:
        paragraph = " ".join(group)
        new_article = f"{new_article}{paragraph}<BR/><BR/>"

    return new_article

def list_blobs(bucket_name, prefix):
    """Lists all the blobs in the bucket."""
    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix)

    return blobs

def get_articles(bucket_name, prefix):
    blobs = list_blobs(bucket_name, prefix)
    articles = []

    for blob in blobs:
        blob_datetime_str = f"{blob.name.split('_')[1]}_{blob.name.split('_')[2].split('.')[0]}"
        dt_obj = datetime.datetime.strptime(blob_datetime_str,'%Y%m%d_%H%M%S')
        article_datetime_str = datetime.datetime.strftime(dt_obj,"News at %H:%M on %A, %d %B %Y")

        article_text = blob.download_as_string().decode('utf-8')
        article_text_trim = article_text[0:article_text.rfind('.')+1]

        article_text_with_paragraphs = create_paragraphs(article_text_trim,6)
        article_doc = f"<b>{article_datetime_str}</b><BR/><BR/>{article_text_with_paragraphs}"
        articles.append(article_doc)

    articles = articles[::-1]

    return articles

app = Flask(__name__, static_url_path='/static')

@app.route('/')
def home():
    articles = get_articles(ml_articles_bucket, 'news')
    article = "<BR/><BR/>".join(articles)
    return render_template('home.html', article=article)

@app.route('/about')
def about():
    return render_template('about.html')

@app.errorhandler(500)
def server_error(e):
    print('An internal error occurred')
    return 'An internal error occurred.', 500

storage_client = storage.Client()

ml_articles_bucket = os.getenv('ML_ARTICLES_BUCKET')


print("Ready to serve.")
