import nltk

try:
    nltk.download("punkt")
except Exception as e:
    try:
        nltk.download("punkt_tab")
    except Exception as e:
        print(e)

nltk.download("stopwords")
