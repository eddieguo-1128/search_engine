"""
An Indri DocVector-style interface for the Lucene termvector.
"""

# Copyright (c) 2023, Carnegie Mellon University.  All Rights Reserved.

import sys

from Idx import Idx
import PyLu


class TermVector:
    """
    Provide an Indri DocVector-style interface for the Lucene termvector.
    There are three main data structurs:

      stems:      The field's vocabulary.  The 0'th entry is an empty
                  string that indicates a stopword.
      stemsFreq:  The frequency (tf) of each entry in stems.
      positions:  The index of the stem that occurred at this position. 
    """

    # -------------- Constants and variables --------------- #

    # -------------- Methods (alphabetical) ---------------- #

    def __init__(self, docid, fieldName):
        """
        Constructor.

        docid: An internal document id (an integer).
        fieldName: The name of a document field.
        """

        # Object initialization
        self.docId = docid		# The TermVector is for this document
        self.fieldName = fieldName	# The TermVector is for this field
        self.__luceneTerms = None
        self.__positions = []		# Indices of stems that each position
        self.__stems = []		# Doc vocabulary. 0 indicates stopword.
        self.__stemsFreq = []		# The tf of each entry in stems.

        # Fetch the term vector, if one exists.
        JfieldName = PyLu.JString(fieldName)
        self.__luceneTerms = Idx.indexReader.getTermVector(docid, JfieldName)

        # If Lucene doesn't have a term vector, the vector is empty.
        if self.__luceneTerms == None:
            return

        # Allocate space for stems & positions. The 0'th stem
        # indicates a stopword.
        stemsLength = self.__luceneTerms.size()
        self.__stems = [ None ] * (stemsLength + 1)
        self.__stemsFreq = [ None ] * (stemsLength + 1)
        self.__positions = [0] * Idx.getFieldLength(fieldName, docid)

        # Iterate through the terms, filling in the stem, frequency,
        # and position information. The 0'th stem indicates a
        # stopword, so the loop starts at i=1.
        ithTerm = self.__luceneTerms.iterator()
        i = 0

        while ithTerm.next() != None:
            i += 1

            ithPositions = ithTerm.postings (None,
                                             PyLu.LPostingsEnum.POSITIONS)
            ithPositions.nextDoc()	# Initialize iPositions
            self.__stems[i] = ithTerm.term().utf8ToString()
            self.__stemsFreq[i] = ithPositions.freq()

            for j in range(0, self.__stemsFreq[i]):
                self.__positions[ithPositions.nextPosition()] = i


    def __str__(self):
        """Render the term vector as a string. Old InspectIndex format."""

        s = '  Field: {}\n'.format(self.fieldName)
        s += '    Stored length: {}\n'.format(len(self.__positions))

        if len(self.__positions) > 0:
            s += '    Vocabulary size: {} terms\n'.format(len(self.__stems) - 1)
            s += '      {:>10} {:<19} {:>2} positions\n'.format(' ', 'term', 'tf')

        # Ignore stem 0 (stopwords)
        for stem_i in range(1, len(self.__stems)):
            s += '      {:>10} {:<19} {:>2} '.format(
                stem_i-1, self.__stems[ stem_i ], self.__stemsFreq[ stem_i ])
            for position_j in range(0, len(self.__positions)):
                if self.__positions[position_j] == stem_i:
                    s += '{} '.format(position_j)
            s += '\n'
        
        return s


    def __str__new(self):
        """Render the term vector as a string."""

        s = 'TermVector:\n'
        s += '  docid: {}\n  field: {}\n  length: {}\n'.format(
            self.docId, self.fieldName, len(self.__positions))
        s += '  stems: {}\n'.format(str(self.__stems))
        s += '  stemsFreq: {}\n'.format(str(self.__stemsFreq))
        s += '  positions: {}\n'.format(str(self.__positions))
        
        return s


    def indexOfStem(self, stem):
        """
        Get the index of stem in the stems vector, or -1 if the stems
        vector does not contain the stem.  

        stem: The stem to search for.
        """

        if self.__stems == [] or self.__stems == [None]:
            return(-1)

        for s in range(1, len(self.__stems)):
            if stem == self.__stems[s]:
                return s

        return(-1)


    def positionsLength(self):
        """
        Get the number of positions in this field (the length of the
        field). If positions are not stored, return 0.
        Note: Idx.getFieldLength report a longer length if the field
        ends with stopwords.
        """
        return(len(self.__positions))


#   /**
#    *  Return the index of the stem that occurred at position i in the
#    *  document.  If positions are not stored, it returns -1.
#    *  @param i A position in the document.
#    *  @return Index of the stem.
#    */
#   public int stemAt(int i) {
#     if (i < positions.length)
#       return positions[i];
#     else
#       return -1;
#   }


    def stemFreq(self, i):
        """
        Get the frequency (tf) of the n'th stem in the current doc,
        or -1 if the index is invalid. The frequency for stopwords
        (i=0) is not stored (0 is returned).

        i: Index of the stem
        """
        if i < len(self.__stemsFreq):
            return(self.__stemsFreq[i])
        else:
            return(-1)


#   /**
#    *  Get the string for the i'th stem, or null if the index is invalid.
#    *  @param i Index of the stem.
#    *  @return The stem string.
#    */
#   public String stemString(int i) {
#     if (i < stems.length)
#       return stems[i];
#     else
#       return null;
#   }
# 
#   /**
#    *  The number of unique stems in this field.
#    *  @return The number of unique stems in this field.
#    */
#   public int stemsLength() {
#     if (this.fieldLength == 0)	# Revise to get rid of fieldLength
#       return 0;
# 
#     return this.stems.length;
#   }
#   
#   /**
#    * Returns ctf of the i'th stem.
#    * @param i Index of the stem.
#    * @return ctf of the stem.
#    * @throws IOException  Error accessing the Lucene index
#    */
#   public long totalStemFreq(int i) throws IOException {
#     return Idx.INDEXREADER.totalTermFreq(terms[i]);
#   }
#   
#   /**
#    * Returns the df of the i'th stem.
#    * @param i Index of the stem.
#    * @return cft of the stem.
#    * @throws IOException Error accessing the Lucene index
#    */
#   public int stemDf(int i) throws IOException {
#     return Idx.INDEXREADER.docFreq(terms[i]);
#   }
#   
# }
