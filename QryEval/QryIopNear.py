"""The NEAR operator for all retrieval models."""

from InvList import InvList
from QryIop import QryIop

class QryIopNear(QryIop):
    """The NEAR operator for all retrieval models."""

    # -------------- Methods (alphabetical) ---------------- #

    def __init__(self,distance):
        """Create an empty NEAR query node."""
        QryIop.__init__(self)		# Inherit from QryIop
        self.distance = distance

    def evaluate(self):
        """"
        Evaluate the query operator; the result is an internal inverted
        list that may be accessed via the internal iterators.

        throws IOException: Error accessing the Lucene index.
        """

        # Create an empty inverted list.
        self.invertedList = InvList(self._field)

        # Should not occur if the query optimizer did its job
        if len(self._args) == 0:	
            return		
        
        # Advance all doc iterators until they point to the same document
        while self.docIteratorHasMatchAll(None):
        
            # Initialize i = 0, locations with a empty list
            i = 0
            locations = []
            break_outer_loop = False

            # Begin Loop
            while i < len(self._args)-1:
                
                # Ending criteria: any of the loc iterators is exhausted
                for q in self._args:
                    if not q.locIteratorHasMatch():
                        break_outer_loop = True
                        break
                
                if break_outer_loop:
                    break

                # Initialize q[i], q[i+1]
                q_i,q_i_plus_1 = self._args[i],self._args[i+1]
                q_i_loc,q_i_plus_1_loc = q_i.locIteratorGetMatch(),q_i_plus_1.locIteratorGetMatch()
                docid = q_i.docIteratorGetMatch()

                # Advance q[i+1].loc to q[i].loc
                while q_i_plus_1_loc < q_i_loc:
                    q_i_plus_1.locIteratorAdvance()
                    if q_i_plus_1.locIteratorHasMatch():
                        q_i_plus_1_loc = q_i_plus_1.locIteratorGetMatch()
                    else:
                        break_outer_loop = True
                        break

                if break_outer_loop:
                    break
                
                # distance constraint satisfied
                if q_i_loc + self.distance >= q_i_plus_1_loc:

                    # i + 1 is not the last argument
                    if i + 1 != len(self._args)-1:
                        i += 1

                    # i + 1 is the last argument
                    else:
                        locations.append(q_i_plus_1_loc)
                        for q in self._args:
                            q.locIteratorAdvance()
                        i = 0

                # distance constraint not satisfied
                else:
                    q_i.locIteratorAdvance()
                    i = max(0,i-1)
            
            # Sort and save right most locations
            if len(locations) > 0:
                locations = sorted(set(locations))
                self.invertedList.appendPosting(docid,locations)
            
            # Advance all doc iterators
            for q in self._args:
                q.docIteratorAdvancePast(docid)



                
                    
                     



            
