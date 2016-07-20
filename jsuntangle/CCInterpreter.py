#import logging
#log = logging.getLogger("Thug")

class CCInterpreter(object):
	"""
		Microsoft Internet Explorer Conditional Comments tiny interpreter
	"""
	def __init__(self, jsversion = 5.8):
		self.jsversion = jsversion

	def run(self, script):
		script = script.replace('@cc_on!@', '*/!/*')

		if '/*@cc_on' in script:
			script = script.replace('/*@cc_on', '')
			script = script.replace('@_jscript_version', "%0.1f" % self.jsversion)
			script = script.replace('/*@if', 'if')
			script = script.replace('@if', 'if')
			script = script.replace('@elif', 'else if')
			script = script.replace('@else', 'else')
			script = script.replace('/*@end', '')
			script = script.replace('@end', '')
			script = script.replace('@_win64', 'false')
			script = script.replace('@_win32', 'true')
			script = script.replace('@_win16', 'false')
			script = script.replace('@*/', '')
			script = script.replace('/*@', '')

		return script
