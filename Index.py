import time
from collections import deque


class Index:
    def __init__(self, index_filename, num_docs=None, doc_freq={}, term_doc_appearances={}, term_positions={}, max_cache_size=1000):
        """
        :param doc_freq: num of docs term appears in
        :param term_doc_appearances: docs that a term appears in
        :param term_positions: positions of appearances of term in each doc
        """
        self.index_filename = index_filename
        self.index_squared_filename = index_filename.split(".", 1)[0] + ".indexSquared.txt"
        self.LRU = deque(maxlen=max_cache_size)
        # save given parameters as class attributes
        self.doc_freq = doc_freq
        self.term_doc_appearances = term_doc_appearances
        self.term_freq = {}
        self.term_positions = term_positions
        # get the set of all documents in the index
        self.all_docs = set().union(*self.term_doc_appearances.values())
        #self.doc_freq = {}
        #self.term_doc_appearances = {}
        #self.term_positions = {}
        if num_docs is None:
            self.readNumDocsBin()
            #self.total_num_docs = 13630
        else:
            # save the total number of documents in index
            self.total_num_docs = num_docs

    def fill_all_docs(self):
        self.all_docs = set(range(1,self.total_num_docs+1))

    def getDocFreq(self, term: str):
        if term not in self.doc_freq:
            if len(self.LRU) >= self.LRU.maxlen:
                self.removeFromCache(1)
            self.loadToCache(term)

        if term in self.doc_freq:
            return self.doc_freq[term]
        else:
            return 0

    def getTermDocAppearances(self, term: str):
        if term not in self.term_doc_appearances:
            if len(self.LRU) >= self.LRU.maxlen:
                self.removeFromCache(1)
            self.loadToCache(term)

        if term in self.term_doc_appearances:
            return self.term_doc_appearances[term]
        else:
            return set()

    def getTermFreq(self, term: str, doc: int):
        term_doc_tuple = (term, doc)
        if term not in self.doc_freq:
            if len(self.LRU) >= self.LRU.maxlen:
                self.removeFromCache(1)
            self.loadToCache(term)

        if term_doc_tuple in self.term_freq:
            return self.term_freq[term_doc_tuple]
        else:
            return 0
        #return len(self.getTermPositions(term, doc))

    def getTermPositions(self, term: str, doc: int):
        term_doc_tuple = (term, doc)
        if term not in self.doc_freq:
            if len(self.LRU) >= self.LRU.maxlen:
                self.removeFromCache(1)
            self.loadToCache(term)

        if term_doc_tuple in self.term_positions:
            return self.term_positions[term_doc_tuple]
        else:
            return []

    def loadToCache(self, term):
        found_term = self.loadTerm(term)
        if found_term:
            self.LRU.append(term)
        return found_term

    def removeFromCache(self, remove_no):
        remove_no = min(remove_no, len(self.LRU))
        for i in range(remove_no):
            oldest_term = self.LRU.popleft()
            for doc in self.term_doc_appearances[oldest_term]:
                del self.term_positions[(oldest_term, doc)]
                del self.term_freq[(oldest_term, doc)]
            del self.doc_freq[oldest_term]
            del self.term_doc_appearances[oldest_term]

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
            print(f"Didn't find {term}... ({round(time.time() - t0, 2)})")
            return False

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
                        elif stage == 1:
                            # print(result)
                            self.doc_freq[term] = result[0]
                            stage += 1
                        else:
                            # if the line isn't term def, then it is term frequency with term positions
                            # thus parse it
                            if doc_def:
                                doc_def = False
                                doc = result[0]
                            else:
                                doc_def = True
                                if term in self.term_doc_appearances:
                                    self.term_doc_appearances[term].add(doc)
                                else:
                                    self.term_doc_appearances[term] = {doc}
                                self.term_positions[(term, doc)] = result
                                self.term_freq[(term, doc)] = len(result)
                                # print(f"{doc}: {result}")
                        result = []
                        buffer = 0
                        shift = 0

                        hard_delimit = True
                        #print(f"Delim took {round(time.time() - t_delim, 2)}s")
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

    def loadTermBinSlow(self, term):
        t0 = time.time()
        chunk_size = 1024
        with open(self.index_filename, 'rb') as f:
            found_term = False
            result = []
            buffer = 0
            shift = 0
            first_line = True
            term_def = True
            already_read_term = False
            hard_delimit = False
            skip = False
            s = ""
            doc = -1
            positions = []
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                for byte in chunk:
                    # delimiter byte
                    if byte == 0x00:
                        s = ""
                        # if this is a hard delimit, flip term_def and continue to next loop
                        if hard_delimit:
                            hard_delimit = False
                            term_def = not term_def
                            continue

                        # if this line is a term definition, then parse it as so
                        if term_def:
                            # if the term has already been found, then return
                            if found_term and not already_read_term:
                                print(f"Loading {term} took {round(time.time() - t0, 2)}s")
                                return True
                            # if this is the first line in the file, it contains num_docs
                            if first_line:
                                first_line = False
                            elif not already_read_term:
                                # get term and doc_freq from line. If the term is our target, then load it
                                current_term = ''.join(map(chr, result))
                                #print(current_term)
                                # print(current_term)
                                if current_term == term:
                                    found_term = True
                                already_read_term = True

                            else:
                                already_read_term = False
                                skip = False
                                if found_term:
                                    self.doc_freq[term] = result[0]
                        elif found_term:
                            # if the line isn't term def, then it is term frequency with term positions
                            # thus parse it if the current term is our target
                            if positions is not None:
                                doc = result[0]
                                positions = None
                            elif positions is None:
                                positions = result
                                if term in self.term_doc_appearances:
                                    self.term_doc_appearances[term].add(doc)
                                else:
                                    self.term_doc_appearances[term] = {doc}
                                self.term_positions[(term, doc)] = positions
                        result = []
                        buffer = 0
                        shift = 0

                        hard_delimit = True
                        #print(f"Delim took {round(time.time() - t_delim, 2)}s")
                    elif term_def and not already_read_term and not skip:
                        hard_delimit = False
                        buffer |= byte << shift
                        result.append(buffer)
                        s += chr(buffer)
                        #print(''.join(map(chr, result)))
                        if not term.startswith(s):
                            skip = True
                        buffer = 0
                        shift = 0
                    else:
                        hard_delimit = False
                        if found_term:
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
        t0 = time.time()
        with open(self.index_filename, "r", encoding='utf-8') as f:
            f.readline()

            found_term = False
            for line in f:
                if line[0] != '\t':
                    if found_term:
                        print(f"Loading {term} took {round(time.time() - t0, 2)}s")
                        return True
                    if line.split(": ")[0] != term:
                        continue
                    found_term = True
                    terms = line.split(": ")
                    self.doc_freq[terms[0]] = int(terms[1])
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

    def readNumDocsBin(self):
        chunk_size = 1024
        with open(self.index_filename, 'rb') as f:
            result = []
            buffer = 0
            shift = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                for byte in chunk:
                    # delimiter byte
                    if byte == 0x00:
                        self.total_num_docs = result[0]
                        return
                    else:
                        if byte < 128:  # MSB is 0
                            buffer |= byte << shift
                            result.append(buffer)
                            buffer = 0
                            shift = 0
                        else:  # MSB is 1
                            buffer |= (byte & 0x7f) << shift
                            shift += 7