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


def convert_doc_to_vector(doc,tfidf,cv):
    feature_names = cv.get_feature_names_out()
    top_n = 10
    tf_idf_vector = tfidf.transform(cv.transform([doc]))
    
    sorted_items = sort_coo(tf_idf_vector.tocoo())
    
    keywords = extract_topn_from_vector(feature_names, sorted_items, top_n)
    
    return keywords