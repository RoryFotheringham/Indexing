class Index:
    def __init__(self, term_freq, term_doc_appearances, term_positions):
        """
        :param term_freq: num of docs term appears in
        :param term_doc_appearances: docs that a term appears in
        :param term_positions: positions of appearances of term in each doc
        """
        # save given parameters as class attributes
        self.term_freq = term_freq
        self.term_doc_appearances = term_doc_appearances
        self.term_positions = term_positions
        # get the set of all documents in the index
        self.all_docs = set().union(*self.term_doc_appearances.values())
        # save the total number of documents in index
        self.total_num_docs = len(self.all_docs)
