import time
import os

from indexing import create_index
from preprocessing import preprocess_xml
from querying import resolve_queries


def main():
    # define file locations with these variables
    data_filepath = "data/MIT/"
    clean_data_filepath = "clean/MIT/"
    index_filepath = "index/MIT.index.txt"

    t0 = time.time()
    resolve_queries("ranked", index_filepath, ["Obama"], "temp_results2.txt")
    print(f"Total runtime: {round(time.time() - t0, 2)}s")
    exit()

    print("Cleaning data...")
    t0 = time.time()
    preprocess_xml(data_filepath, clean_data_filepath)
    print(f"Took {round(time.time() - t0, 2)}s")
    #exit()


    print("Creating index...")
    t0 = time.time()
    create_index(clean_data_filepath, index_filepath)
    print(f"Took {round(time.time() - t0, 2)}s")
    exit()


    boolean_query_file = "queries.boolean.txt"
    boolean_output_file = "results.boolean.txt"
    print("Running boolean queries...")
    t0 = time.time()
    resolve_queries("boolean", index_filepath, boolean_query_file, boolean_output_file)
    print(f"Took {round(time.time() - t0, 2)}s")
    exit()
    ranked_query_file = "queries.ranked.txt"
    ranked_output_file = "results.ranked.txt"
    print("Running ranked queries...")
    t0 = time.time()
    resolve_queries("ranked", index_filepath, ranked_query_file, ranked_output_file)
    print(f"Took {round(time.time() - t0, 2)}s")

def test_bool():
    data_filepath = "data/MIT/"
    clean_data_filepath = "clean/MIT/"
    index_filepath = "index/MIT.index.txt"

    t0 = time.time()
    resolve_queries("boolean", index_filepath, ['engineering OR machine AND learning OR math AND NOT science'], "temp_bool_results2.txt")
    print(f"Total runtime: {round(time.time() - t0, 2)}s")
    exit()

#test_bool()
main()

