import subprocess
from PIL import Image
import shlex

class Convert(object):
    """
    imagemagick convert tool wrapper
    """

    def __init__(self, input_file, output_file):
        self._image = False
        self.input_file=input_file
        self.output_file=output_file

        self._process_steps = []

        self.default_params = dict(
            width=self.image().size[0],
            height=self.image().size[1]
        )

    def close_image(self):
        if self.image:
            self.image.close()

    def image(self):
        if not self._image:
            self._image = Image.open(self.input_file)
        return self._image

    def add_process_step(self, process_step_cmd, **kwargs):
        self._process_steps.append( (process_step_cmd,kwargs))

    def clear_process_steps(self):
        self._process_steps = []

    def apply(self):

        steps = ''

        # concat steps
        for cmd, params in self._process_steps:
            format = dict(self.default_params.items() + params.items())
            step = cmd.format(**format)
            steps += " {} ".format(step)

        command = "convert {input_filename} {steps} {output_filename}".format(input_filename=r'"%s"' % self.input_file,
                                                                              output_filename=r'"%s"' % self.output_file,
                                                                              steps=steps)
        self.execute_process(command)

    def execute_process(self, command):

        cmd = shlex.split(command)

        p = subprocess.Popen(cmd,shell=False, stderr=subprocess.STDOUT)
        p.wait()