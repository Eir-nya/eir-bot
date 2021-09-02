import modules.submodules.magicword as magicword

class this:
	def __init__(self, main, server):
		print("To server \"" + server.guild.name + "\": the magic word is: " + magicword.magicword + "!")
