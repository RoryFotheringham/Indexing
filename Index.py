from collections import deque


class Index:
    def __init__(self, index_filename, num_docs, term_freq={}, term_doc_appearances={}, term_positions={}, max_cache_size=1000):
        """
        :param term_freq: num of docs term appears in
        :param term_doc_appearances: docs that a term appears in
        :param term_positions: positions of appearances of term in each doc
        """
        self.index_filename = index_filename
        self.LRU = deque(maxlen=max_cache_size)
        # save given parameters as class attributes
        self.term_freq = term_freq
        self.term_doc_appearances = term_doc_appearances
        self.term_positions = term_positions
        # get the set of all documents in the index
        self.all_docs = set().union(*self.term_doc_appearances.values())
        #self.term_freq = {}
        #self.term_doc_appearances = {}
        #self.term_positions = {}
        # save the total number of documents in index
        self.total_num_docs = num_docs

    def getTermFreq(self, term: str):
        if term not in self.term_freq:
            if len(self.LRU) >= self.LRU.maxlen:
                self.removeFromCache(1)
            self.loadToCache(term)

        if term in self.term_freq:
            return self.term_freq[term]
        else:
            return None

    def getTermDocAppearances(self, term: str):
        if term not in self.term_doc_appearances:
            if len(self.LRU) >= self.LRU.maxlen:
                self.removeFromCache(1)
            self.loadToCache(term)

        if term in self.term_doc_appearances:
            return self.term_doc_appearances[term]
        else:
            return None

    def getTermPositions(self, term_doc_tuple: tuple):
        if term_doc_tuple not in self.term_positions:
            if len(self.LRU) >= self.LRU.maxlen:
                self.removeFromCache(1)
            self.loadToCache(term_doc_tuple)

        if term_doc_tuple in self.term_positions:
            return self.term_positions[term_doc_tuple]
        else:
            return None

    def loadToCache(self, term):
        found_term = self.loadTerm(term)
        if found_term:
            self.LRU.append(term)
        return found_term

    def removeFromCache(self, remove_no):
        remove_no = min(remove_no, len(self.LRU))
        for i in range(remove_no):
            oldest_term = self.LRU.popleft()
            del self.term_freq[oldest_term]
            del self.term_doc_appearances[oldest_term]
            del self.term_positions[oldest_term]

    def loadTerm(self, term):
        with open(self.index_filename, "r", encoding='utf-8') as f:
            f.readline()

            found_term = False
            for line in f:
                if line[0] != '\t':
                    if found_term:
                        return True
                    if line.split(": ")[0] != term:
                        continue
                    found_term = True
                    terms = line.split(": ")
                    self.term_freq[terms[0]] = int(terms[1])
                    key = terms[0]
                    # print("-----------")
                    # print("header:", repr(terms[0]), repr(int(terms[1])))
                # print(repr(line))
                else:
                    if not found_term:
                        continue
                    terms = line.split(": ")
                    doc = int(terms[0])
                    if key in self.term_doc_appearances:
                        self.term_doc_appearances[key].add(doc)
                    else:
                        self.term_doc_appearances[key] = {doc}

                    positions = [int(s) for s in terms[1].split(',')]
                    self.term_positions[(key, doc)] = set(positions)
                    # print("footer:", repr(int(terms[0])), repr(positions))
        return found_term
