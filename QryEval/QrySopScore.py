"""
The SCORE operator for all retrieval models.
"""

# Copyright (c) 2023, Carnegie Mellon University.  All Rights Reserved.

import math
import sys

from Idx import Idx
from QrySop import QrySop
from RetrievalModelUnrankedBoolean import RetrievalModelUnrankedBoolean
from RetrievalModelRankedBoolean import RetrievalModelRankedBoolean
from RetrievalModelBM25 import RetrievalModelBM25
from RetrievalModelIndri import RetrievalModelIndri


class QrySopScore(QrySop):
    """
    """

    # -------------- Methods (alphabetical) ---------------- #


    def __init__(self):
        QrySop.__init__(self)		# Inherit from QrySop
        self.cache_bm25 = {'N':None,'avg_doclen':None}    # N and avg_doclen are constant, so we can cache them
        self.cache_indri = {'lengthC':None,'ctf':{}}    # lengthC is a constant
        self.cache_default = {'lengthC':None}

    def docIteratorHasMatch(self, r):
        """
        Indicates whether the query has a match.
        r: The retrieval model that determines what is a match.

        Returns True if the query matches, otherwise False.
        """
        return(self.docIteratorHasMatchFirst(r))


    def getScore(self, r):
        """
        Get a score for the document that docIteratorHasMatch matched.
        
        r: The retrieval model that determines how scores are calculated.
        Returns the document score.
        throws IOException: Error accessing the Lucene index.
        """
        if isinstance(r, RetrievalModelUnrankedBoolean):
            return self.__getScoreUnrankedBoolean(r)
        elif isinstance(r, RetrievalModelRankedBoolean):
            return self.__getScoreRankedBoolean(r)
        elif isinstance(r, RetrievalModelBM25):
            return self.__getScoreBM25(r,self.cache_bm25)
        elif isinstance(r, RetrievalModelIndri):
            return self.__getScoreIndri(r,self.cache_indri)
        else:
            raise Exception(
                '{} does not support the #SCORE operator.'.format(
                    r.__class__.__name__))


    def __getScoreUnrankedBoolean(self, r):
        """
        getScore for the Unranked retrieval model.

        r: The retrieval model that determines how scores are calculated.
        Returns the document score.
        throws IOException: Error accessing the Lucene index.
        """
        if not self.docIteratorHasMatchCache():
            return 0.0
        else:
            return 1.0
     
    def __getScoreRankedBoolean(self, r):
        """
        getScore for the Ranked retrieval model.

        r: The retrieval model that determines how scores are calculated.
        Returns the document score.
        throws IOException: Error accessing the Lucene index.
        """
        if not self.docIteratorHasMatchCache():
            return 0.0
        else:
            return self._args[0].docIteratorGetMatchPosting().tf
    
    def __getScoreBM25(self, r, cache):
        """
        getScore for BM25 model.
        """
        if not self.docIteratorHasMatchCache():
            return 0.0
        # Return the sum of its query argument scores. Three parts: RSJ weight, tf weight, user weight

        # Model Parameters
        k_1 = r.k_1
        b = r.b
        k_3 = r.k_3

        q = self._args[0]
        
        # Part 1: Modified RSJ weight
        # N is a constant, so we use cache
        if not cache['N']:
            cache['N'] = Idx.getNumDocs()
        N, df = cache['N'], q.getDf()
        rsj_weight = math.log((N+1)/(df+0.5))

        # Part 2: TF weight
        tf = q.docIteratorGetMatchPosting().tf
        doclen = Idx.getFieldLength(q._field, q.docIteratorGetMatch())
        # avg_doclen is a constant, so we use cache
        if not cache['avg_doclen']:
            cache['avg_doclen'] = Idx.getSumOfFieldLengths(q._field) / Idx.getDocCount(q._field)
        avg_doclen = cache['avg_doclen']
        tf_weight = tf / (tf + k_1 * ((1 - b) + b * (doclen / avg_doclen)))

        # Part 3: User Weight
        qtf = 1
        user_weight = (k_3 + 1) * qtf / (k_3 + qtf)

        return rsj_weight * tf_weight * user_weight
    
    def __getScoreIndri(self, r, cache):
        """
        getScore for Indri model.
        """
        if not self.docIteratorHasMatchCache():
            return 0.0
        
        # Model Parameters
        mu = r.mu
        Lambda = r.Lambda

        q = self._args[0]

        # Two-stage smoothing to compute term weights
        if not cache['lengthC']:
            cache['lengthC'] = Idx.getSumOfFieldLengths(q._field)
        if not cache['ctf'].get(q):
            cache['ctf'][q] = q.getCtf()
        ctf, lengthC = cache['ctf'][q], cache['lengthC'] 
        pMLE = ctf / lengthC

        tf = q.docIteratorGetMatchPosting().tf
        docid = q.docIteratorGetMatch()
        lengthd = Idx.getFieldLength(q._field, docid)
        if lengthd == 0 and mu == 0:
            return 0
        else:
            return (1-Lambda)*((tf+mu*pMLE)/(lengthd+mu))+Lambda*pMLE
    
    # Calculates a score for a term
    def getDefaultScore(self, r, docid):
        if isinstance(r, RetrievalModelIndri):
            # Model Parameters
            mu = r.mu
            Lambda = r.Lambda
            
            q = self._args[0]
            ctf = q.getCtf()
            # Extra smoothing for terms that have ctf=0
            if ctf == 0:
                ctf = 0.5
            if not self.cache_default['lengthC']:
                self.cache_default['lengthC'] = Idx.getSumOfFieldLengths(q._field)
            pMLE = ctf / self.cache_default['lengthC']
            length = Idx.getFieldLength(q._field, docid)
            if length == 0 and mu == 0:
                return 0
            else:
                return (1-Lambda)*((0+mu*pMLE)/(length+mu))+Lambda*pMLE

    def initialize(self, r):
        """
        Initialize the query operator (and its arguments), including any
        internal iterators.  If the query operator is of type QryIop, it
        is fully evaluated, and the results are stored in an internal
        inverted list that may be accessed via the internal iterator.

        r: A retrieval model that guides initialization.
        throws IOException: Error accessing the Lucene index.
        """
        q = self._args[ 0 ]
        q.initialize(r)
