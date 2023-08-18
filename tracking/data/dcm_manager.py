# import numpy as np
# import pydicom


class DcmManager():
    def __init__(self) -> None:
        self.ds = None
        self.image = None

    def reset_dcm(self):
        self.image = None
