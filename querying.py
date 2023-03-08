from calendar import c
from email.mime import application
import math
import re
import time
from unittest import result

from Index import Index
import indexing
import preprocessing


def resolve_queries(query_type, index_filein, queries, results_fileout, expanded_query: str=""):
    """
    Loads index and given query file, processes ranked queries and saves output to a given file location
    :param query_type: either 'boolean' or 'ranked'
    :param index_filein: text file to load index from
    :param queries: list of queries
    :param results_fileout: text file to save results to
    :return: None
    """
    # load the index from the given filepath
    # index is the custom 'Index' object as defined above
    t0 = time.time()
    index = indexing.load_index(index_filein)
    print(f"Loading index took {round(time.time() - t0, 2)}s")

    # resolve each individual query using the loaded index and save results to output file
    with open(results_fileout, "w", encoding='utf-8') as f:
        for q in queries:
            if query_type.lower() == "boolean":
                result = bool_helper(index, q.strip())
                for doc in result:
                    f.write(f"{doc}\n")
                    # print(f"{query_num},{doc}")
            elif query_type.lower() == "ranked":
                result = ranked_query(index, q.strip(), expanded_query=expanded_query)
                for doc, score in result:
                    f.write(f"{doc},{round(score, 4)}\n")
                    # print(f"{query_num},{doc},{round(score, 4)}")
    return


def resolve_query(query_type: str, index_filein: str, query: str, results_fileout: str, expanded_query: str=""):
    """
    Loads index and given query file, processes ranked queries and saves output to a given file location
    :param expanded_query:
    :param query_type: either 'boolean' or 'ranked'
    :param index_filein: text file to load index from
    :param query: list of queries
    :param results_fileout: text file to save results to
    :return: None
    """
    # load the index from the given filepath
    # index is the custom 'Index' object as defined above
    t0 = time.time()
    index = indexing.load_index(index_filein)
    print(f"Loading index took {round(time.time() - t0, 2)}s")

    # resolve each individual query using the loaded index and save results to output file
    with open(results_fileout, "w", encoding='utf-8') as f:
        if query_type.lower() == "boolean":
            result = bool_helper(index, query.strip())
            for doc in result:
                f.write(f"{doc}\n")
                # print(f"{query_num},{doc}")
        elif query_type.lower() == "ranked":
            result = ranked_query(index, query.strip(), expanded_query=expanded_query)
            for doc, score in result:
                f.write(f"{doc},{round(score, 4)}\n")
                # print(f"{query_num},{doc},{round(score, 4)}")
    return


def resolveContentQuery(index_filein: str, query: str, lecture_id: int):
    index = indexing.loadContentIndex(index_filein, lecture_id)
    index.lecture_id = lecture_id
    result = ranked_query(index, query)
    with open("yeet.txt", "w", encoding='utf-8') as f:
        for doc, score in result:
            f.write(f"{doc},{round(score, 4)}\n")
    return result


def ranked_query(index: Index, query: str, expanded_query=""):
    """
    Resolves ranked query using the given index
    :param expanded_query:
    :param index: Index object
    :param query: ranked query to process
    :return: returns a sorted list of tuples (document, score)
    """
    # apply pre-processing to the query
    terms = preprocessing.clean_line(query).split(" ")
    expanded_terms = preprocessing.clean_line(expanded_query).split(" ")
    # get the set of all documents to calculate score for
    docs_union = set()
    for term in terms:
        docs = index.getTermDocAppearances(term)
        docs_union = docs_union.union(docs)

    # calculate the score for each document
    scores = {}
    for doc in docs_union:
        scores[doc] = calculate_score(index, terms, doc, expanded_terms=expanded_terms)

    # sort results and keep only first 150 indices
    out = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    out = out[:150]
    return out


def calculate_score(index: Index, terms: [str], doc: int, expanded_terms: [str]=[]):
    """
    Calculate the score of a document given a list of terms
    :param expanded_terms:
    :param index: Index object
    :param terms: list of terms to search for
    :param doc: document number to score
    :return: returns a score
    """
    N = index.total_num_docs
    score = 0
    all_terms = terms + expanded_terms
    for i in range(len(all_terms)):
        term = all_terms[i]
        # if this term does not appear in the given document then skip it
        if doc not in index.getTermDocAppearances(term):
            continue
        # calculate term frequency
        tf = index.getTermFreq(term, doc)
        # calculate document frequency and inverse document frequency
        df = index.getDocFreq(term)
        idf = math.log10(N / df)
        # finally, calculate the score and add it to the running total
        wtd = (1 + math.log10(tf)) * idf
        if i >= len(terms):
            wtd *= 0.5
        score += wtd
    return score


def preprocess_boolean_query(index, raw_query):
    '''
    takes a raw query string for a boolean query and resolves each phrase.
    takes this:  'probability AND "Discrete mathematics" OR "baysian statistic"
    into this => ['probability', 'AND', __set_of_results__, 'OR', __set_of_results__]

    :param index: Index
    :param raw_query: str query formatted like s"
    '''
    open = False
    start = 0
    end = 0
    curr_phrase = ''
    curr_query = ''
    total = []
    for char in raw_query:

        if char == '"' and not open:
            open = True
            total.append(curr_query)
            curr_query = ''
        else:
            if char == '"' and open:
                open = False
                total.append(phrase_search(index, curr_phrase))
                curr_phrase = ''

        if open and char != '"':
            curr_phrase = curr_phrase + char
        else:
            if char != '"':
                curr_query = curr_query + char
    total.append(curr_query)

    processed_query = []
    for chunk in total:
        if isinstance(chunk, str):
            temp = chunk.strip().split(' ')
            for term in temp:
                if term == '':
                    continue
                processed_query.append(term)
        if isinstance(chunk, set):
            processed_query.append(chunk)

    return processed_query


def resolve_term(index: Index, term: str, not_flag=False):
    """
    Given an index and a term, return the list of documents the term is in
    :param index: Index object
    :param term: can be a single term or a phrase
    :param not_flag: if set to True, return the set of documents that DON'T contain this term
    :return: set of document numbers
    """
    # if the term is a phrase, call another function to resolve it
    if re.search(r'\"[A-Za-z0-9 ]+\"', term):
        return resolve_phrase(index, term, not_flag=not_flag)

    term = preprocessing.clean_line(term)
    # return the list of documents this term is in
    if not_flag:
        return index.all_docs.difference(index.getTermDocAppearances(term))
    return index.getTermDocAppearances(term)


def resolve_phrase(index: Index, term: str, not_flag=False):  # currently only works for
    # exactly 2 terms.
    """
    Returns the set of documents that a phrase is in
    :param index: Index object
    :param term: phrase string
    :param not_flag: if set to True, return the set of documents that DON'T contain this phrase
    :return: set of document numbers
    """
    # get each individual term in the phrase
    terms = term[1:-1].split(" ")
    left = preprocessing.clean_line(terms[0])
    right = preprocessing.clean_line(terms[1])

    # get the set of documents that contain both terms
    left_docs = index.getTermDocAppearances(left)
    right_docs = index.getTermDocAppearances(right)
    intersect = left_docs.intersection(right_docs)
    # for every document, check if the terms appear in the appropriate positions
    out = set()
    for doc in intersect:
        for pos_left in index.getTermPositions(left, doc):
            if pos_left + 1 in index.getTermPositions(right, doc):
                out.add(doc)
                break

    if not_flag:
        return index.all_docs.difference(out)
    return out


def resolve_proximity(index, term):
    """
    Returns the set of documents that match a given proximity query
    :param index: Index object
    :param term: proximity query string
    :return: set of document numbers
    """
    # use regex to extract the max required distance between the terms
    # regex is used since we don't know how many digits long the range is
    range = int(re.findall("#[0-9]+\(", term)[0][1:-1])
    # use regex to extract the individual terms
    terms = re.findall("\([A-Za-z0-9]+,[A-Za-z0-9 ]+\)", term)[0]
    # remove any spaces that might be after the comma
    terms.replace(" ", "")
    # get each individual term
    terms = terms[1:-1].split(",")
    left = preprocessing.clean_line(terms[0])
    right = preprocessing.clean_line(terms[1])

    # get the set of documents that contain both terms
    left_docs = index.getTermDocAppearances(left)
    right_docs = index.getTermDocAppearances(right)
    intersect = left_docs.intersection(right_docs)
    # for every document, check if the terms appear in the appropriate positions
    out = set()
    for doc in intersect:
        for pos_left in index.getTermPositions(left, doc):
            brk = False
            for pos_right in index.getTermPositions(right, doc):
                if abs(pos_left - pos_right) <= range:
                    out.add(doc)
                    brk = True
                    break
            if brk:
                break
    return out


def phrase_search(index: Index, query):
    '''
    helper function for calling recursive function phrase_search
    
    :param index: Index
    :param query: tokenized [str]
    '''
    query = preprocessing.clean_line(query)
    terms = query.split(' ')
    if terms == []:
        return set()

    seed = terms[0]

    appearances = index.getTermDocAppearances(seed)
    if not appearances:
        return set()
    tups = []
    for app in appearances:
        positions = index.getTermPositions(seed, app)
        for pos in positions:
            tups.append((app, pos))

    results = []
    for tup in tups:
        result = phrase_search_recur(index, tup, terms[1:])
        if result != (-1, -1):
            results.append(result)
    return set(results)


def phrase_search_recur(index: Index, tup, rest_of_phrase: [str]):
    if rest_of_phrase == []:
        return tup[0]

    seed = rest_of_phrase[0]
    terms = rest_of_phrase[1:]
    prev_doc = tup[0]
    prev_pos = tup[1]

    appearences = index.getTermDocAppearances(seed)
    if not appearences:
        return (-1, -1)
    else:
        for app in appearences:
            if app == prev_doc:
                positions = index.getTermPositions(seed, app)
                for pos in positions:
                    if pos == prev_pos + 1:
                        return phrase_search_recur(index, (app, pos), terms)
        return (-1, -1)


def and_wrap(index: Index, term_1, term_2):
    if isinstance(term_1, str):
        term_1 = resolve_term(index, term_1)

    if isinstance(term_2, str):
        term_2 = resolve_term(index, term_2)

    return term_1.intersection(term_2)


def or_wrap(index: Index, term_1, term_2):
    if isinstance(term_1, str):
        term_1 = resolve_term(index, term_1)

    if isinstance(term_2, str):
        term_2 = resolve_term(index, term_2)

    return term_1.union(term_2)


def not_wrap(index: Index, term):
    if isinstance(term, str):
        term = resolve_term(index, term)

    return index.all_docs.difference(term)


def bool_helper(index: Index, query):
    '''
    high level function for boolean search 
    - initialises special functions used in bool search and calls the function
    
    :param query: untokenised raw string query
    :param index: Index
    '''

    opp_dict = {1: ('NOT', not_wrap, 1),
                2: ('AND', and_wrap, 2),
                3: ('OR', or_wrap, 2)}
    opp_index = 1

    terms = preprocess_boolean_query(index, query)

    if len(terms) == 1:
        if isinstance(terms, str):
            return index.getTermDocAppearances(terms[0])
        elif isinstance(terms, set):
            return terms[0]

    def make_new_terms(terms, count, function, arity):
        '''
        constructs a new list which on which bool search is
        called recursively. It replaces specified terms with a 
        wrapper function application wrt the given operator. 
        
        :param terms: [str|set] query being worked on 
        :param count: int position of the operator
        :param function: wrapper fucntion variable which is applied to terms
        :param arity: the arity of the given function 
        '''
        new_terms = []
        if arity == 1:
            application = function(index, terms[count + 1])
            for i in range(len(terms)):
                if i == count + 1:
                    continue
                elif i == count:
                    new_terms.append(application)
                else:
                    new_terms.append(terms[i])

        if arity == 2:
            application = function(index, terms[count - 1], terms[count + 1])
            for i in range(len(terms)):
                if i == count - 1 or i == count + 1:
                    continue
                elif i == count:
                    new_terms.append(application)
                else:
                    new_terms.append(terms[i])

        return new_terms

    # todo confirm the type of the query and implement the
    # necessary preprocessing before passing to bool_search

    def bool_search(terms, opp_index):
        '''
        recursively called on a list of terms which are repeatedly simplified through operator applications
        
        :param terms: [str|set] query being processed
        :param opp_index: dictionary storing the order of operations
        '''
        if len(terms) == 1:
            return terms[0]

        while opp_index <= max(opp_dict.keys()):
            opp, opp_func, opp_arity = opp_dict.get(opp_index)
            for count, term in enumerate(terms):
                if term == opp:
                    try:
                        new_terms = make_new_terms(terms, count, opp_func, opp_arity)
                    except IndexError:
                        print('badly formed boolean query query')
                        return {}
                    return bool_search(new_terms, opp_index)
            opp_index += 1

    return bool_search(terms, opp_index)


def boolean_query(index: Index, query: str):
    terms = query
    if re.fullmatch(r'#[0-9]+\([A-Za-z0-9]+,[A-Za-z0-9 ]+\)', terms):
        return sorted(resolve_proximity(index, query))
    or_op = " OR " in terms
    and_op = " AND " in terms

    # case when AND/OR operator is present in query
    if and_op or or_op:
        if and_op:
            terms = terms.split(" AND ")
        else:
            terms = terms.split(" OR ")
        # resolve left
        left_not = bool(re.fullmatch(r'NOT (.*?)', terms[0]))
        if left_not:
            left = resolve_term(index, terms[0][4:], not_flag=or_op)
        else:
            left = resolve_term(index, terms[0])

        # resolve right
        right_not = bool(re.fullmatch(r'NOT (.*?)', terms[1]))
        if right_not:
            right = resolve_term(index, terms[1][4:], not_flag=or_op)
        else:
            right = resolve_term(index, terms[1])

        if or_op:
            return sorted(left.union(right))
        if left_not:
            return sorted(right.difference(left))
        elif right_not:
            return sorted(left.difference(right))
        else:
            return sorted(left.intersection(right))
    else:
        # resolve single term
        not_flag = bool(re.fullmatch(r'NOT (.*?)', terms))
        if not_flag:
            return resolve_term(index, terms[4:], not_flag=True)
        return sorted(resolve_term(index, terms))
