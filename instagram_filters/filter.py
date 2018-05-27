# inspired from http://net.tutsplus.com/tutorials/php/create-instagram-filters-with-php/

from PIL import Image

import imagemagick

class Filter(imagemagick.Convert):
    """
    Common image filter class
    """

    def __init__(self, filename, output_filename=None, width=None, height=None):
        """
        :param filename: input file path
        :param output_filename:  output file path, if None, input file will be replaced
        :param width: optional width of the image, might speed up filter process
        :param height: optional height of the image, might speed up filter process
        """
        if not output_filename:
            output_filename = filename
        super(Filter, self).__init__(input_file=filename,output_file=output_filename)

        self._image = False

        if not width or not height:
            image = self.image()
            self.default_params['width'] = image.size[0]
            self.default_params['height'] = image.size[1]
        else:
            self.default_params['width'] = width
            self.default_params['height'] = height

        self._post_decorations = []
        self._pre_decorations = []

    def close_image(self):
        if self._image:
            self._image.close()

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

    def add_post_decoration(self, decoration):
        self._post_decorations.append(decoration)

    def add_pre_decoration(self, decoration):
        self._pre_decorations.append(decoration)

    def apply(self):
        for decorator in self._pre_decorations:
            decorator.apply(filter=self)
        self._filter_callback()
        for decorator in self._post_decorations:
            decorator.apply(filter=self)
        super(Filter, self).apply()
