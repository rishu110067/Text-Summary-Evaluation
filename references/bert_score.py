from sentence_transformers import SentenceTransformer, util

st_model = SentenceTransformer('all-MiniLM-L6-v2')

predicted_summary = 'How big is London'
gold_summary = 'London has 9,787,426 inhabitants at the 2011 census'

pred_embedding = st_model.encode([predicted_summary])
gt_embedding = st_model.encode([gold_summary])

sim = util.cos_sim(pred_embedding, gt_embedding)
print(sim)