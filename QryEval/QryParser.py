"""
QryParser is an embarrassingly simplistic query parser.
"""

# Copyright (c) 2023, Carnegie Mellon University.  All Rights Reserved.

import sys
import PyLu

from Idx import Idx
from QryIopSyn import QryIopSyn
from QryIopNear import QryIopNear
from QryIopTerm import QryIopTerm
from QrySopOr import QrySopOr
from QrySopAnd import QrySopAnd
from QrySopScore import QrySopScore
from QrySopSum import QrySopSum
from QryIopWindow import QryIopWindow
from QrySopWSum import QrySopWSum
from QrySopWAnd import QrySopWAnd


class QryParser:
    """
    QryParser is an embarrassingly simplistic query parser.  It has
    two primary methods:  getQuery and tokenizeString.  getQuery
    converts a query string into an optimized Qry tree.  tokenizeString
    converts a flat (unstructured) query string into a string array; it
    is used for creating learning-to-rank feature vectors.

    Add new operators to the query parser by modifying the following
    methods:

        createOperator: Use a string (e.g., #and) to create a node
        (e.g., QrySopAnd).

        parseString:  If the operator supports term weights
        (e.g., #wsum (0.5 apple 1 pie)), you must modify this method.
        For these operators, two substrings (weight and term) are
        popped from the query string at each step, instead of one.

    Add new document fields to the parser by modifying createTerms.
    """

    # -------------- Constants and variables --------------- #

    __ANALYZER = PyLu.LEnglishAnalyzerConfigurable()
    __initialized = False

    # -------------- Methods (alphabetical) ---------------- #

    @staticmethod
    def __init():
        """Initialize the Lucene analyzer."""
        if not QryParser.__initialized:
            QryParser.__ANALYZER.setLowercase(PyLu.JTrue)
            QryParser.__ANALYZER.setStopwordRemoval(PyLu.JTrue) 
            QryParser.__ANALYZER.setStemmer(PyLu.LEnglishAnalyzerConfigurableStemmerType.KSTEM)
            QryParser.__initialized = True


    @staticmethod
    def __createOperator(operatorName):
        """Create and return the specified query operator."""

        operator = None
        operatorNameLowerCase = operatorName.lower()

        # STUDENTS:
        # Add new query operators below.

        # Create the query operator.
        if operatorNameLowerCase == '#or':
            operator = QrySopOr()
        elif operatorNameLowerCase == '#and':
            operator = QrySopAnd()
        elif operatorNameLowerCase == '#syn':
            operator = QryIopSyn()
        elif operatorNameLowerCase[:5] == '#near':
            distance = operatorNameLowerCase[6:]
            operator = QryIopNear(int(distance))
        elif operatorNameLowerCase[:7] == '#window':
            distance = operatorNameLowerCase[8:]
            operator = QryIopWindow(int(distance))
        elif operatorNameLowerCase == '#sum':
            operator = QrySopSum()
        elif operatorNameLowerCase == '#wsum':
            operator = QrySopWSum()
        elif operatorNameLowerCase == '#wand':
            operator = QrySopWAnd()
        else:
            QryParser.__syntaxError('Unknown query operator ' + operatorName)

        operator.setDisplayName(operatorName.upper())

        return operator

  
    @staticmethod
    def __createTerms(token):
        """
        Create one or more terms from a token.  The token may contain
        dashes or other punctuation b(e.g., near-death) and/or a field
        name (e.g., apple.title).

        token: The token consumed from the query string.

        Returns a list of one or more tokens.

        Throws IOException: Error accessing the Lucene index.
        """

        # Split the token into a term and a field.
        if '.' in token:
            term, field = token.split('.', 1)
            field = field.lower()
        else:
            term = token
            field = 'body'

        # Confirm that the field is a known field.
        if not (field == 'body' or
                field == 'title' or
                field == 'url' or 
                field == 'keywords' or
                field == 'inlink'):
            QryParser.__syntaxError('Unknown field ' + token)

        # Lexical processing, stopwords, stemming.  A loop is used
        # just in case a term (e.g., "near-death") gets tokenized into
        # multiple terms (e.g., "near" and "death").

        t = QryParser.tokenizeString(term)
        terms = [ None ] * len(t)
        
        for j in range(0, len(t)):
            terms[j] = QryIopTerm(t[j], field)
    
        return(terms)


    @staticmethod
    def getQuery(queryString):
        """
        Parse a query string into a query tree.

        queryString: The query string, in an Indri-style query language.

        Returns:  The query tree for the parsed query.

        throws IOException: Error accessing the Lucene index.
        throws IllegalArgumentException: Query syntax error.
        """

        QryParser.__init()
        q = QryParser.parseString(queryString)	# An exact parse
        q = QryParser.optimizeQuery(q)		# An optimized parse
        return(q)


    @staticmethod
    def __indexOfBalancingParen(s):
        """
        Get the index of the right parenenthesis that balances the
        left-most parenthesis.  Return -1 if it doesn't exist.

        s: A string containing a query.
        """

        depth = 0

        for i in range(0, len(s)):
            if s[ i ] == '(':
                depth += 1
            elif s[ i ] == ')':
                if depth == 0:
                    QryParser.__syntaxError(
                        'Unbalanced or missing parentheses')
                depth -= 1
                if depth == 0:
                    return i

        return(-1)


    @staticmethod
    def optimizeQuery(q):
        """
        Optimize the query by removing degenerate nodes produced during
        query parsing, for example '#NEAR/1 (of the)' which turns into
        '#NEAR/1 ()' after stopwords are removed; and unnecessary nodes
        or subtrees, such as #AND (#AND (a)), which can be replaced by
        'a'.
        """

        # Term operators don't benefit from optimization.
        if isinstance(q, QryIopTerm):
            return q

        # Optimization is a depth-first task, so recurse on query
        # arguments.  This is done in reverse to simplify deleting
        # query arguments that become None.
        for i in range(len(q._args) - 1, -1, -1):
            q_i_before = q._args[ i ]
            q_i_after = QryParser.optimizeQuery(q_i_before)

            if q_i_after == None:
                q.delArg(i)			# optimization deleted the arg
            else:
                if q_i_before != q_i_after:
                    q._args[ i ] = q_i_after	# optimization changed the arg

        # If the operator now has no arguments, it is deleted.
        if len(q._args) == 0:
            return None

        # Only SCORE operators can have a single argument.  Other
        # query operators that have just one argument are deleted.
        if len(q._args)  == 1 and not isinstance(q, QrySopScore):
            q = q._args[ 0 ]

        return(q)

    @staticmethod
    def parseString(queryString):
        """
        Parse a query string into a query tree.

        queryString: The query string, in an Indri-style query language.

        Returns The query tree for the parsed query.

        throws IOException: Error accessing the Lucene index.
        throws IllegalArgumentException: Query syntax error.
        """

        # This simple parser is sensitive to parenthensis placement,
        # so check for basic errors first.

        queryString = queryString.strip()	# The last char should be ')'

        if (queryString.count('(') == 0 or
            queryString.count('(') != queryString.count(')') or
            QryParser.__indexOfBalancingParen(queryString) !=
            (len(queryString) - 1)):
            QryParser.__syntaxError(
                'Missing, unbalanced, or misplaced parentheses ')

        # The query language is prefix-oriented, so the query string can
        # be processed left to right.  At each step, a substring is
        # popped from the head (left) of the string, and is converted to
        # a Qry object that is added to the query tree.  Subqueries are
        # handled via recursion.

        # Find the left-most query operator and start the query tree.
        substrings = queryString.split('(', 1)
        queryTree = QryParser.__createOperator(substrings[0].strip())

        # Start consuming queryString by removing the query operator and
        # its terminating ')'.  queryString is always the part of the
        # query that hasn't been processed yet.
        queryString = substrings[ 1 ]
        queryString = queryString[ 0 :
                                   queryString.rindex(')') ].strip()
        
        # Each pass below handles one argument to the query operator.
        # Note: An argument can be a token that produces multiple terms
        # (e.g., "near-death") or a subquery (e.g., "#and (a b c)").
        # Recurse on subqueries.
        while len(queryString) > 0:

	    # STUDENTS:
            # In HW2, you will need to modify this to handle query
            # operators that have weights, e.g., #SUM(0.5 a 1.5 b)
            
            weight = 0
            if isinstance(queryTree, QrySopWSum) or isinstance(queryTree, QrySopWAnd):
                weight, queryString = QryParser.__popWeight (queryString)
            
            qargs = []

            if queryString[ 0 ] == '#':		# Subquery
                subquery, queryString = QryParser.__popSubquery (queryString)
                qargs = [ QryParser.parseString (subquery) ]

            else:				# Term 
                term, queryString = QryParser.__popTerm (queryString)
                qargs = QryParser.__createTerms(term)
    
            queryString = queryString.strip()

            # Add the argument(s) to the query tree.
            for q in qargs:
                if isinstance(queryTree, QrySopWSum) or isinstance(queryTree, QrySopWAnd):
                    queryTree.setWeight(weight)
                queryTree.appendArg(q)

        return queryTree

    
    @staticmethod 
    def __popSubquery(argString):
        """
        Remove a subQuery from an argument string.  Return the subquery
        and the modified argument string.
        
        argString: A partial query argument string, e.g., "#and(a b) c d".
        
        Returns a tuple of the subquery string and the modified argString
        (e.g., (#and(a b)" and "c d).
        """
	
        i = QryParser.__indexOfBalancingParen(argString)
	  
        if i < 0:			# Query syntax error. The parser
            return(argString, '')	# handles it. Here, just don't fail.
    
        return(argString[ 0 : i+1 ], argString[ i+1 : ])

    
    @staticmethod
    def __popTerm(argString):
        """
        Remove a term from an argument string.  Return the term and
        the modified argument string.

        argString: A partial query argument string, e.g., "a b c d".

        Returns a tuple of the term string and the modified argString
        (e.g., "a" and "b c d".
        """
	
        substrings = argString.split(maxsplit=1)

        if len(substrings) < 2:	# Is this the last argument?
            argString = ''
        else:
            argString = substrings[1]

        return((substrings[ 0 ], argString))

    
    @staticmethod
    def __popWeight(argString):
        """
        Remove a weight from an argument string.  Return the weight and
        the modified argument string.

        argString: A partial query argument string, e.g., '3.0 fu 2.0 bar'.
        Returns the weight and the modified argString
        (e.g., 3.0 and 'fu 2.0 bar'.
        """

        substrings = argString.split(maxsplit=1)

        if len(substrings) < 2:
            syntaxError('Missing weight or query argument')

        return(float(substrings[ 0 ]), substrings[ 1 ])

    
    @staticmethod
    def __syntaxError(errorString):
        """
        Throw an error specialized for query parsing syntax errors.

        errorString: The error string.

        throws Exception: The query contained a syntax error
        """

        raise Exception('Query syntax error: ' + errorString)


    @staticmethod
    def tokenizeString(query):
        """                      
        Given part of a query string, returns an array of terms with
        stopwords removed and the terms stemmed using the Krovetz
        stemmer.  Use this method to process raw query terms.

        query: String containing query. 

        Returns a list of query tokens

        throws IOException: Error accessing the Lucene index.
        """

        QryParser.__init()

        tokenStream = QryParser.__ANALYZER.tokenStream(PyLu.JString('dummyField'),
                                                        PyLu.JString(query))
        charTermAttribute = tokenStream.addAttribute(PyLu.LCharTermAttribute)
        tokenStream.reset()

        tokens = []

        while tokenStream.incrementToken():
            term = charTermAttribute.toString()
            tokens.append(str(term))

        tokenStream.close()

        return(tokens)

        
