import time
import os

from indexing import create_index_xml
from preprocessing import preprocess_xml
from querying import resolve_queries


def run_queries(index_filepath, queries):
    with open("temp.txt", "w") as f:
        for i in range(len(queries)):
            f.write(f"{i} {queries[i]}")

    t0 = time.time()
    resolve_queries("ranked", index_filepath, "temp.txt", "temp_results.txt")
    print(f"Total runtime: {round(time.time() - t0, 2)}s")

    os.remove("temp.txt")


def main():
    # define file locations with these variables
    data_filepath = "data/lec_1.xml"
    clean_data_filepath = "clean/lec_1.clean.xml"
    index_filepath = "index/lec_1.index.txt"

    run_queries(index_filepath, ["Obama"])
    exit()

    print("Cleaning data...")
    t0 = time.time()
    preprocess_xml(data_filepath, clean_data_filepath)
    print(f"Took {round(time.time() - t0, 2)}s")


    print("Creating index...")
    t0 = time.time()
    create_index_xml(clean_data_filepath, index_filepath)
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



main()
