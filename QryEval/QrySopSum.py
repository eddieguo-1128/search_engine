"""
The SUM operator for BM25.
"""

import sys

from QrySop import QrySop
from RetrievalModelBM25 import RetrievalModelBM25


class QrySopSum(QrySop):

    # -------------- Methods (alphabetical) ---------------- #

    def __init__(self):
        QrySop.__init__(self)		# Inherit from QrySop

    def docIteratorHasMatch(self, r):
        """
        Indicates whether the query has a match.

        r: The retrieval model that determines what is a match.
        Returns True if the query matches, otherwise False.
        """
        return self.docIteratorHasMatchMin(r)


    def getScore(self, retrievalModel):
        """
        Get a score for the document that docIteratorHasMatch matched.

        retrievalModel: retrieval model parameters

        Returns the document score.

        throws IOException: Error accessing the Lucene index
        """

        if isinstance(retrievalModel, RetrievalModelBM25):
            return self.__getScoreBM25(retrievalModel)
        else:
            raise Exception('{}.{} does not support {}'.format(
                self.__class__.__name__,
                sys._getframe().f_code.co_name,
                retrievalModel.__class__.__name__))


    def __getScoreBM25(self, r):
        """
        getScore for BM25 model.

        r: The retrieval model that determines how scores are calculated.
        Returns the document score.
        throws IOException: Error accessing the Lucene index
        """

        # Return the sum of its query argument scores.
        scores = []
        docid = self.docIteratorGetMatch()
        for q_i in self._args:
            if (q_i.docIteratorHasMatch(r) and q_i.docIteratorGetMatch() == docid):
                scores.append(q_i.getScore(r))
        return sum(scores)