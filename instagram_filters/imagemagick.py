import subprocess
import shlex

class Convert(object):
    """
    imagemagick convert tool wrapper
    """

    def __init__(self, input_file, output_file):
        """
        :param input_file: input file path
        :param output_file: output file path
        """
        self.input_file=input_file
        self.output_file=output_file

        #tuple of sub commands and parameter dicts
        self._process_steps = []

        self.default_params = {}

    def add_filter_step(self, process_step_cmd, **kwargs):
        """
        Registers a new sub command (filter step) that is chained into the imagemagick command queue
        :param process_step_cmd: sub command string
        :param kwargs: parameters that will be concatenated with the default parameters and applied to the command string
        """
        self._process_steps.append((process_step_cmd,kwargs))

    def clear_filter_steps(self):
        """
        Delete all registered filter steps
        :return:
        """
        self._process_steps = []

    def apply(self):
        """
        Applying the filter and producing the output file
        First all sub commands are combined to one command string together with replacing parameter placeholders
        """
        steps = ''

        # concat steps
        for cmd, params in self._process_steps:
            format = dict(self.default_params.items() + params.items())
            step = cmd.format(**format)
            steps += " {} ".format(step)

        command = "convert {input_filename} {steps} {output_filename}".format(input_filename=r'"%s"' % self.input_file,
                                                                              output_filename=r'"%s"' % self.output_file,
                                                                              steps=steps)
        self._execute_process(command)

    def _execute_process(self, command):
        """
        Execute the imagemagick command
        :param command: full command string
        """

        cmd = shlex.split(command)

        p = subprocess.Popen(cmd,shell=False, stderr=subprocess.STDOUT)
        p.wait()