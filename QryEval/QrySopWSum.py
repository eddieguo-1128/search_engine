"""
The Weighted SUM operator for Indri.
"""

import sys

from QrySop import QrySop
from RetrievalModelIndri import RetrievalModelIndri


class QrySopWSum(QrySop):

    # -------------- Methods (alphabetical) ---------------- #

    def __init__(self):
        QrySop.__init__(self)		# Inherit from QrySop
        self.weights = []
    
    def setWeight(self, weight):
        """
        Overridden method to also add a weight when a query argument is added.

        q: The query argument to add.
        weight: The weight associated with the query argument.
        """
        self.weights.append(weight)

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

        if isinstance(retrievalModel, RetrievalModelIndri):
            return self.__getScoreIndri(retrievalModel)
        else:
            raise Exception('{}.{} does not support {}'.format(
                self.__class__.__name__,
                sys._getframe().f_code.co_name,
                retrievalModel.__class__.__name__))


    def __getScoreIndri(self, r):
        """
        getScore for Indri model.

        r: The retrieval model that determines how scores are calculated.
        Returns the document score.
        throws IOException: Error accessing the Lucene index
        """

        # Return the sum of its query argument scores.
        scores = []
        docid = self.docIteratorGetMatch()
        total_weight = sum(self.weights)
        for i, q_i in enumerate(self._args):
            weight = self.weights[i]
            if (q_i.docIteratorHasMatch(r) and q_i.docIteratorGetMatch() == docid):
                scores.append(q_i.getScore(r)*(weight/total_weight))
            else:
                scores.append(q_i.getDefaultScore(r, docid)*(weight/total_weight))
        return sum(scores)
    
    def getDefaultScore(self, r, docid):
        scores = []
        total_weight = sum(self.weights)
        for i, q_i in enumerate(self._args):
            weight = self.weights[i] 
            scores.append(q_i.getDefaultScore(r, docid)*(weight/total_weight))
        return sum(scores)