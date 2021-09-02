isGlobal = True

class this:
	def __init__(self):
		pass
	
	async def Create(self):
		pass
	
	#TODO comment out
	async def shutdown(self, sourceMessage):
		"""Debug command. Only usable by the creator of the bot.
Shuts down the bot."""
		if sourceMessage.author.id == 138733266285887488:
			await main.client.change_presence(status=main.discord.Status.invisible)
			await main.client.close()
			print(main.client.user.name + " signed out!")
		else:
			raise main.PermissionException

	async def help(self, sourceMessage, commandName=None):
		"""Displays all commands, or displays info for one command."""
		# prefix = self.CheckPrefix(sourceMessage)
		# prefix = main.localModules["settings"].GetSetting("prefix", sourceMessage.guild)
		prefix = await main.servers[sourceMessage.guild in main.servers and sourceMessage.guild or "DM"].modules["settings"].GetSetting("prefix")
		
		#Temporary function that turns a command into a string, complete with prefix and usage
		def textifyCommand(command):
			string = prefix + command.usage
			return string
		
		messageContent = "```"
		
		#List all commands, no descriptions
		if commandName == None:
			for command in main.commands:
				messageContent += "\n" + textifyCommand(main.commands[command])
			
			#Key
			messageContent += "\n\nKey:\n  [required argument]\n  (optional argument = value if not provided)\n  (...) - as many arguments as you want"
			messageContent += "\n```"
			messageContent += "\nType `" + prefix + "help <commandName>` for info on a specific command."
		#List one command with description
		elif commandName in main.commands:
			messageContent += "\n" + textifyCommand(main.commands[commandName])
			messageContent += "\n\n" + main.commands[commandName].description.replace("[prefix]", prefix)
			messageContent += "\n```"
		#Invalid command name
		else:
			raise main.InvalidCommandException #TODO: should I just make it display the regular "help" output, showing all commands, instead?
			
		await sourceMessage.channel.send(content=messageContent)

	#Template for embeds, to be used across all modules
	def CreateEmbed(self, title, footerText="", description=None, colour=0xFAAAAB):
		embed = main.discord.Embed(title=title, description=description, colour=colour)
		embed.set_footer(text=footerText, icon_url=main.client.user.avatar_url)
		return embed
