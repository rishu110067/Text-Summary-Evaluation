# just for reference

from sentence_transformers import SentenceTransformer, util

st_model = SentenceTransformer('all-MiniLM-L6-v2')

predicted_summary = 'How big is London'
actual_summary = 'London has 9,787,426 inhabitants at the 2011 census'

pred_embedding = st_model.encode([predicted_summary])
gt_embedding = st_model.encode([actual_summary])

sim = util.cos_sim(pred_embedding, gt_embedding)
print(sim)