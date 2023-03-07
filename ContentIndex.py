from collections import deque

from Index import Index


class ContentIndex(Index):
    def __init__(self, index_filename, lecture_id=-1, max_cache_size=1000):
        # super().__init__(index_filename, num_docs)
        # [slidenos] = [1, 1, 1, 2, 4, 5]
        # term -> {doc -> [slidenos]}
        self.index_filename = index_filename
        self.LRU = deque(maxlen=max_cache_size)
        self.term_doc_sv = {}
        self.lecture_id = -1
        self.total_num_docs = -1

    def getDocFreq(self, term: str):
        if term not in self.term_doc_sv:
            if len(self.LRU) >= self.LRU.maxlen:
                self.removeFromCache(1)
            self.loadToCache(term)

        if term in self.term_doc_sv and self.lecture_id in self.term_doc_sv[term]:
            return len(set(self.term_doc_sv[term][self.lecture_id]))
        else:
            return 0

    def getTermDocAppearances(self, term: str):
        if term not in self.term_doc_sv:
            if len(self.LRU) >= self.LRU.maxlen:
                self.removeFromCache(1)
            self.loadToCache(term)

        if term in self.term_doc_sv and self.lecture_id in self.term_doc_sv[term]:
            return set(self.term_doc_sv[term][self.lecture_id])
        else:
            return set()

    def getTermFreq(self, term: str, doc: int):
        if term not in self.term_doc_sv:
            if len(self.LRU) >= self.LRU.maxlen:
                self.removeFromCache(1)
            self.loadToCache(term)

        if term in self.term_doc_sv and self.lecture_id in self.term_doc_sv[term]:
            slide_appearances = self.term_doc_sv[term][self.lecture_id]
            return slide_appearances.count(doc)
        else:
            return 0

    def loadToCache(self, term):
        found_term = self.loadTerm(term)
        if found_term:
            self.LRU.append(term)
        return found_term

    def removeFromCache(self, remove_no):
        remove_no = min(remove_no, len(self.LRU))
        for i in range(remove_no):
            oldest_term = self.LRU.popleft()
            del self.term_doc_sv[oldest_term]

    def loadTerm(self, term):
        if self.index_filename.rsplit(".", 1)[-1] == "txt":
            return self.loadTermText(term)
        elif self.index_filename.rsplit(".", 1)[-1] == "bin":
            return self.loadTermBin(term)

    def loadTermText(self, term):
        with open(self.index_filename, "r", encoding='utf-8') as f:
            found_term = False
            for line in f:
                if line[0] != '\t':
                    if found_term:
                        return True
                    key = line.strip()
                    if key != term:
                        continue
                    found_term = True
                    self.term_doc_sv[term] = {}
                else:
                    if not found_term:
                        continue
                    doc_str, doc_num_slides_str, slides_str = line.split(": ")
                    self.total_num_docs = int(doc_num_slides_str)
                    slides = [int(s) for s in slides_str.split(',')]
                    self.term_doc_sv[term][int(doc_str)] = slides
        return found_term

    def loadTermBin(self, term):
        return True