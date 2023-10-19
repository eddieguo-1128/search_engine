"""
The AND operator for all retrieval models.
"""

import sys
import math

from QrySop import QrySop
from RetrievalModelUnrankedBoolean import RetrievalModelUnrankedBoolean
from RetrievalModelRankedBoolean import RetrievalModelRankedBoolean
from RetrievalModelIndri import RetrievalModelIndri


class QrySopAnd(QrySop):
    """
    The AND operator for all retrieval models.
    """

    # -------------- Methods (alphabetical) ---------------- #


    def __init__(self):
        QrySop.__init__(self)		# Inherit from QrySop


    def docIteratorHasMatch(self, r):
        """
        Indicates whether the query has a match.

        r: The retrieval model that determines what is a match.
        Returns True if the query matches, otherwise False.
        """
        # For Indri, matches if any arguments match
        if isinstance(r, RetrievalModelIndri):
            return self.docIteratorHasMatchMin(r)
        return self.docIteratorHasMatchAll(r)


    def getScore(self, retrievalModel):
        """
        Get a score for the document that docIteratorHasMatch matched.

        retrievalModel: retrieval model parameters

        Returns the document score.

        throws IOException: Error accessing the Lucene index
        """

        if isinstance(retrievalModel, RetrievalModelUnrankedBoolean) or isinstance(retrievalModel, RetrievalModelRankedBoolean):
            return self.__getScoreBoolean(retrievalModel)
        if isinstance(retrievalModel, RetrievalModelIndri):
            return self.__getScoreIndri(retrievalModel)
        else:
            raise Exception('{}.{} does not support {}'.format(
                self.__class__.__name__,
                sys._getframe().f_code.co_name,
                retrievalModel.__class__.__name__))


    def __getScoreBoolean(self, r):
        """
        getScore for Boolean retrieval models.

        r: The retrieval model that determines how scores are calculated.
        Returns the document score.
        throws IOException: Error accessing the Lucene index
        """

        # Return the minimum of its query argument scores.  The
        # document matches, but we don't know which query arguments
        # match, so check each query argument.
        scores = []
        docid = self.docIteratorGetMatch()

        for q_i in self._args:
            if (q_i.docIteratorHasMatch(r) and
                q_i.docIteratorGetMatch() == docid):
                scores.append(q_i.getScore(r))

        return min(scores)
    
    def __getScoreIndri(self, r):
        """
        getScore for Indri retrieval model.

        r: The retrieval model that determines how scores are calculated.
        Returns the document score.
        throws IOException: Error accessing the Lucene index
        """ 
        scores = []
        docid = self.docIteratorGetMatch()

        for q_i in self._args:
            if (q_i.docIteratorHasMatch(r) and q_i.docIteratorGetMatch() == docid):  # if qi has a match for document d
                scores.append(q_i.getScore(r))  # call qi.getScore
            else:
                scores.append(q_i.getDefaultScore(r, docid))  # else, call qi.getDefaultScore
        
        scores = math.prod(scores)
        return math.pow(scores, 1/len(self._args))
    
    def getDefaultScore(self, r, docid):
        if isinstance(r, RetrievalModelIndri):
            scores = []
            for q_i in self._args:
                scores.append(q_i.getDefaultScore(r, docid))  # call the ith query argument's getDefaultScore method  
            scores = math.prod(scores)
            return math.pow(scores, 1/len(self._args))