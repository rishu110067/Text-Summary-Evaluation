from torchmetrics import TranslationEditRate

predicted_summary = 'How big is London'
gold_summary = 'London has 9,787,426 inhabitants at the 2011 census'

ter = TranslationEditRate()
ter_score = (float)(ter(predicted_summary, gold_summary))
print(ter_score)