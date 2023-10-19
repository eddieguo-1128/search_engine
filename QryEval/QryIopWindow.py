"""The WINDOW operator for all retrieval models."""

from InvList import InvList
from QryIop import QryIop

class QryIopWindow(QryIop):
    """The WINDOW operator for all retrieval models."""

    # -------------- Methods (alphabetical) ---------------- #

    def __init__(self,window):
        """Create an empty WINDOW query node."""
        QryIop.__init__(self)		# Inherit from QryIop
        self.window = window

    def evaluate(self):
        self.invertedList = InvList(self._field)

        if len(self._args) == 0:
            return

        while self.docIteratorHasMatchAll(None):
            docid = self._args[0].docIteratorGetMatch()
            positions = []

            while True:
                min_pos = float('inf')
                max_pos = float('-inf')
                min_arg_idx = 0
                max_arg_idx = 0

                done = False
                for i, q in enumerate(self._args):
                    if not q.locIteratorHasMatch():
                        done = True
                        break

                    pos = q.locIteratorGetMatch()
                    if pos < min_pos:
                        min_pos = pos
                        min_arg_idx = i
                    if pos > max_pos:
                        max_pos = pos
                        max_arg_idx = i
                
                if done:
                    break

                if max_pos >= min_pos and max_pos - min_pos < self.window:
                    positions.append(self._args[max_arg_idx].locIteratorGetMatch())
                    for q in self._args:
                        q.locIteratorAdvance()
                else:
                    self._args[min_arg_idx].locIteratorAdvance()

            if positions:
                positions.sort()
                self.invertedList.appendPosting(docid, positions)
            
            for q in self._args:
                q.docIteratorAdvancePast(docid)
