"""
Define and store data for the Ranked Boolean Retrieval Model.
"""

from RetrievalModel import RetrievalModel

class RetrievalModelRankedBoolean(RetrievalModel):
    """
    Define and store data for the Unranked Boolean Retrieval Model.
    """


    # -------------- Methods (alphabetical) ---------------- #

    def __init__(self, parameters):
        RetrievalModel.__init__(self)		# Inherit from RetrievalModel
        self.defaultQrySop = '#AND'