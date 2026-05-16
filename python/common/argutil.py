import argparse


##
# Command line help formatting to improve readability.
#
# author: mjhwa@yahoo.com
##
class CustomHelpFormatter(argparse.HelpFormatter):
  # Adds a newline after every help text line
  def _split_lines(self, text, width):
    return super()._split_lines(text, width) + ['']

  # Join options (e.g., -f, --file) and append metavar once
  def _format_action_invocation(self, action):
    if not action.option_strings or action.nargs == 0:
      return super()._format_action_invocation(action)
    
    default = self._get_default_metavar_for_optional(action)
    args_string = self._format_args(action, default)
    return ', '.join(action.option_strings) + ' ' + args_string