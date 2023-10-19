"""
Define and store data for the BM25 Model.
"""

from RetrievalModel import RetrievalModel

class RetrievalModelBM25(RetrievalModel):
    """
    Define and store data for the BM25 Retrieval Model.
    """


    # -------------- Methods (alphabetical) ---------------- #

    def __init__(self, k_1, b, k_3):
        RetrievalModel.__init__(self)
        # SUM query operator is the default query operator for unstructured (bag of word) queries in BM25.		
        self.defaultQrySop = '#SUM'

        # Model Parameters
        self.k_1 = k_1
        self.b = b
        self.k_3 = k_3