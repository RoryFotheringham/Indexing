import time
from collections import deque

from Index import Index


class ContentIndex(Index):
    def __init__(self, index_filename, lecture_id=-1, max_cache_size=1000):
        # super().__init__(index_filename, num_docs)
        # [slidenos] = [1, 1, 1, 2, 4, 5]
        # term -> {doc -> [slidenos]}
        self.index_filename = index_filename
        self.index_squared_filename = index_filename.split(".", 1)[0] + ".indexSquared.txt"
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

    def loadTermBin(self, term):
        t0 = time.time()
        found_term = False
        offset = 0
        with open(self.index_squared_filename, 'r') as f:
            aggregate = 0
            for line in f:
                current_term, current_offset = line.split(":")
                aggregate += int(current_offset)
                if current_term == term:
                    found_term = True
                    # offset = int(current_offset)
                    offset = aggregate
                    break
        if not found_term:
            return False

        self.term_doc_sv[term] = {}
        chunk_size = 1024
        with open(self.index_filename, 'rb') as f:
            result = []
            buffer = 0
            shift = 0
            f.seek(offset)
            hard_delimit = False
            stage = 0
            doc = -1
            doc_def = True
            doc_aggregration = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                for byte in chunk:
                    # delimiter byte
                    if byte == 0x00:
                        # if this is a hard delimit, we have read all data for the term, thus return
                        if hard_delimit:
                            print(f"Loading {term} took {round(time.time() - t0, 2)}s")
                            return True

                        # if this line is a term definition, then parse it as so
                        if stage == 0:
                            stage += 1
                        else:
                            # if the line isn't term def, then it is term frequency with term positions
                            # thus parse it
                            if doc_def:
                                doc_def = False
                                doc_aggregration += result[0]
                                doc = doc_aggregration
                                doc_num_slides = result[1]
                                self.total_num_docs = doc_num_slides
                            else:
                                doc_def = True
                                #slide_aggregration = 0
                                #slides = []
                                #for slide in result:
                                #    slide_aggregration += slide
                                #    slides.append(slide_aggregration)
                                self.term_doc_sv[term][doc] = result
                                # print(f"{doc}: {result}")
                        result = []
                        buffer = 0
                        shift = 0

                        hard_delimit = True
                        # print(f"Delim took {round(time.time() - t_delim, 2)}s")
                    else:
                        hard_delimit = False
                        if byte < 128:  # MSB is 0
                            buffer |= byte << shift
                            result.append(buffer)
                            buffer = 0
                            shift = 0
                        else:  # MSB is 1
                            buffer |= (byte & 0x7f) << shift
                            shift += 7
        return found_term

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
