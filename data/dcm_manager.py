# import numpy as np
from pydicom import dcmread
from pydicom.pixel_data_handlers.util import apply_modality_lut, apply_voi_lut
import math


class DcmManager():
    def __init__(self) -> None:
        self.ds = None
        self.image = None

    def reset_dcm(self):
        self.image = None

    def get_image(self):
        return self.image

    def get_windwoing_value(self):
        """
        Returns:
            tuple(wl_value, ww_value)
        """
        try:
            wl_value = self.ds.WindowCenter
            ww_value = self.ds.WindowWidth
        except AttributeError:
            wl_value = 255
            ww_value = 255
        return wl_value, ww_value

    def open_dcm_file(self, fname):
        self.ds = dcmread(fname[0])
        pixel = self.ds.pixel_array
        self.total_frame = 1
        if len(pixel.shape) == 3:
            self.image = pixel[0]
        else:
            self.image = pixel
        self.init_digit_length()

    def init_digit_length(self):
        def digit_length(num):
            return int(math.log10(num)) + 1 if num > 0 else 0

        self.xd = digit_length(self.image.shape[0]) - 1
        self.yd = digit_length(self.image.shape[1]) - 1

    def dcm_windowing_change(self, start, end):
        """
        windwow center는 x값에 대해 변경되므로 마우스 좌우로 변경됩니다.  
        windwow width는 y값에 대해 변경되므로 마우스 상하로 변경됩니다.
        windowing 값은 정수값입니다.
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        xd = self.xd
        yd = self.yd
        try:
            self.ds.WindowCenter = int(
                self.ds.WindowCenter + (10**xd) * dx / self.image.shape[0])
            self.ds.WindowWidth = int(
                self.ds.WindowWidth - (10**yd) * dy / self.image.shape[1])
            modality_lut_image = apply_modality_lut(self.image, self.ds)
            voi_lut_image = apply_voi_lut(modality_lut_image, self.ds)

        except AttributeError:
            self.ds.WindowCenter = 255
            self.ds.WindowWidth = 255
            voi_lut_image = None

        return voi_lut_image
