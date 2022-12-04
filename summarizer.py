# using self trained model for summary prediction

from transformers import pipeline

hub_model_id = "darshkk/t5-small-finetuned-xsum"
summarizer = pipeline("summarization", model=hub_model_id)

text = "Iran has abolished the country’s morality police, AFP reported quoting the prosecutor general. This comes as protests have raged across Iran prompting confrontations between demonstrators and security forces for more than two months of protests triggered by the arrest of Mahsa Amini for allegedly violating the country's strict female dress code."
summary = summarizer(text)
print(summary)
