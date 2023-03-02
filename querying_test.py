from querying import phrase_search, preprocess_boolean_query
from indexing import create_index
from preprocessing import preprocess_xml
from querying import resolve_queries
import indexing
import time




data_filepath = "data/MIT/"
clean_data_filepath = "clean/MIT/"
index_filepath = "index/MIT.index.txt"


#preprocess_xml(data_filepath, clean_data_filepath)


# #create_index(clean_data_filepath, index_filepath)

# index = indexing.load_index(index_filepath)

# example_q = 'bayesian OR "logical reasoning" AND NOT kapow'

# processed = preprocess_boolean_query(index, example_q)

# #result = phrase_search(index, 'machine learning')

# print(processed)

def test_bool():
    data_filepath = "data/MIT/"
    clean_data_filepath = "clean/MIT/"
    index_filepath = "index/MIT.index.txt"

    t0 = time.time()
    resolve_queries("boolean", index_filepath, ['engineering OR "machine learning" OR math AND NOT "bayesian statistical mining"'], "temp_bool_results2.txt")
    print(f"Total runtime: {round(time.time() - t0, 2)}s")
    exit()

test_bool()