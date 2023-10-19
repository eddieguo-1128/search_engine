"""
Define and store data for the Indri Model.
"""

from RetrievalModel import RetrievalModel

class RetrievalModelIndri(RetrievalModel):
    """
    Define and store data for the Indri Retrieval Model.
    """


    # -------------- Methods (alphabetical) ---------------- #

    def __init__(self, mu, Lambda):
        RetrievalModel.__init__(self)
        # AND is the default query operator for most language modeling systems		
        self.defaultQrySop = '#AND'

        # Parameters for Indri
        self.mu = mu
        self.Lambda = Lambda