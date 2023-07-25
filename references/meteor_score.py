import nltk
nltk.download('omw-1.4')
nltk.download('punkt')
nltk.download('wordnet')

from nltk.translate import meteor
from nltk import word_tokenize

predicted_summary = 'How big is London'
gold_summary = 'London has 9,787,426 inhabitants at the 2011 census'

meteor_score = meteor([word_tokenize(gold_summary)], word_tokenize(predicted_summary))
print(meteor_score)