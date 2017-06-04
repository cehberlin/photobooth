# inspired from http://net.tutsplus.com/tutorials/php/create-instagram-filters-with-php/

from PIL import Image

import imagemagick

class Filter(imagemagick.Convert):
    """
    Common image filter class
    """

    def __init__(self, filename, output_filename=None):
        if not output_filename:
            output_filename = filename
        super(Filter, self).__init__(input_file=filename,output_file=output_filename)

        self._image = False

        image = self.image()
        self.default_params['width'] = image.size[0]
        self.default_params['height'] = image.size[1]

    def close_image(self):
        if self.image:
            self.image.close()

    def image(self):
        if not self._image:
            self._image = Image.open(self.input_file)
        return self._image

    def colortone(self, color, level, type = 0):

        arg0 = level
        arg1 = 100 - level
        if type == 0:
            negate = '-negate'
        else:
            negate = ''

        self.add_filter_step(process_step_cmd="\( -clone 0 -fill '{color}' -colorize 100% \)", color=color)
        self.add_filter_step(process_step_cmd="\( -clone 0 -colorspace gray {negate} \)", negate = negate)
        self.add_filter_step(process_step_cmd="-compose blend -define compose:args={arg0},{arg1}", arg0 = arg0, arg1 = arg1)
        self.add_filter_step(process_step_cmd="-composite")

    def _filter_callback(self):
        """
        Overwrite this method in child class and add required filter steps
        :return:
        """
        pass

    def apply(self):
        self._filter_callback()
        super(Filter, self).apply()
