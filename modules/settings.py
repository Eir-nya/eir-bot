import os, sqlite3

isGlobal = False

default_settings = {
	"prefix" : ["!", "text"],
	"minesweeper default mines" : [10, "integer"],
	"minesweeper default width" : [8, "integer"],
	"minesweeper default height" : [8, "integer"],
}

class this:
	def __init__(self, server):
		self.server = server
		
		#Load default settings
		self.settings = {}
		for key in default_settings.keys():
			self.settings[key] = default_settings[key][0]
	
	async def Create(self):
		#Check if server already has a settings database file, create one if necessary
		if self.server.guild != None:
			fileExists = os.path.exists("settings/" + str(self.server.guild.id) + ".sqlite")
			try:
				self.conn = sqlite3.connect("settings/" + str(self.server.guild.id) + ".sqlite")
			except Exception as e:
				print("An error occured while initializing the settings database for server \"" + (self.server.guild and self.server.guild.name or "DM") + "\":")
				print(e)
				print("Closing bot...")
				await main.client.close()
			
			#Check if database file already exists
			if not fileExists:
				#Create initialization string
				toDoString = "CREATE TABLE IF NOT EXISTS settings ("
				
				counter = 0
				for key in default_settings:
					counter += 1
					toDoString += "\n\"" + key + "\" " + default_settings[key][1] + (counter < len(default_settings.keys()) and "," or "")
				toDoString += "\n);"
				
				#Apply changes and save file
				self.conn.cursor().execute(toDoString)
				self.conn.commit()
				
				#Insert default values
				toDoString = "INSERT INTO settings(\"" + ("\",\"".join(default_settings.keys())) + "\") VALUES ("
				counter = 0
				for key in default_settings:
					counter += 1
					toDoString += "\"" + str(default_settings[key][0]) + "\"" + (counter < len(default_settings.keys()) and "," or "")
				toDoString += ")"
				
				#Apply changes and save file
				self.conn.cursor().execute(toDoString)
				self.conn.commit()
			#Otherwise, load the settings from the database
			else:
				self.LoadSettings()
	
	#Loads settings from a database file and converts it to the same settings table used by the other modules
	def LoadSettings(self):
		cursor = self.conn.cursor().execute("SELECT * FROM settings")
		row = cursor.fetchone()
		columns = next(zip(*cursor.description))
		
		self.settings = {}
		
		for i in range(len(columns)):
			self.settings[columns[i]] = row[i]
	
	#Command to change the bot's setting for the current server, and save it to the matching database file.
	async def changesetting(self, sourceMessage, name, value):
		"""Requires admin priveleges.
Changes one of the bot's settings for this server, and saves it.
If a setting name has spaces in it, you will have to surround that setting with \"quotes\" when using this command."""
		if not sourceMessage.channel.permissions_for(sourceMessage.author).administrator:
			raise main.PermissionException
		elif self.server.guild == None:
			raise CustomResponseException("Unable to change settings for DMs.")
		
		cursor = self.conn.cursor().execute("SELECT * FROM settings")
		row = cursor.fetchone()
		columns = next(zip(*cursor.description))
		
		#Check if the named setting is in the columns tuple
		if not name in columns or not name in default_settings:
			raise CustomResponseException("Setting \"" + str(name) + "\" could not be found.")
		
		#Interpret the given value to a type (it's "text" by default)
		type = default_settings[name][1]
		data = value
		
		try:
			if type == "integer":
				data = int(value)
			elif type == "bool" or type == "boolean":
				data = data.lower()
				if data == "true" or data == "false":
					data = data == "true"
				else:
					raise Exception()
		except:
			raise CustomResponseException("Error while parsing value \"" + str(value) + "\".")
		
		#Store the new value to the row
		rowlist = list(row)
		rowlist[columns.index(name)] = data
		row = tuple(rowlist)
		
		#Store the new row to the table
		self.conn.cursor().execute("DELETE FROM settings")
		toDoString = "INSERT INTO settings(\"" + ("\",\"".join(columns)) + "\") VALUES ("
		counter = 0
		for key in columns:
			counter += 1
			toDoString += "\"" + str(row[columns.index(key)]) + "\"" + (counter < len(columns) and "," or "")
		toDoString += ")"
		
		self.conn.cursor().execute(toDoString)
		self.conn.commit()
		self.LoadSettings()
		
		await sourceMessage.channel.send(content="Success! Setting `" + name + "` changed to `" + value + "`.")
	
	#Command to print the bot's settings for the current server.
	async def listsettings(self, sourceMessage):
		"""Requires admin priveleges.
Print's the bot's settings for the current server."""
		if not sourceMessage.channel.permissions_for(sourceMessage.author).administrator:
			raise main.PermissionException
		
		cursor = self.conn.cursor().execute("SELECT * FROM settings")
		row = cursor.fetchone()
		columns = next(zip(*cursor.description))
		
		toPrintString = ""
		for i in range(len(columns)):
			toPrintString += columns[i] + " (" + default_settings[columns[i]][1] + ") = " + str(row[i]) + (i < len(columns) - 1 and "\n" or "")
		
		prefix = self.settings["prefix"]
		embed = main.globalModules["util"].CreateEmbed(main.globalModules["util"], title="Settings for " + (self.server.guild == None and "DMs" or self.server.guild.name), description="```\n" + toPrintString + "\n```", colour=main.discord.Colour.darker_grey(), footerText="Usage: `" + prefix + main.commands["changesetting"].usage + "`")
		await sourceMessage.channel.send(embed=embed)
	
	#Utility function to return a server's value for a setting, if applicable, or the default setting otherwise
	async def GetSetting(self, setting):
		#return self.server.modules["settings"].settings[setting]
		return self.settings[setting]

#TODO: do we need this one down here?
#Utility function to return a server's value for a setting, if applicable, or the default setting otherwise
# def GetSettingOrDefault(setting, guild=None):
	# if guild == None:
		# guild = "DM"
	# return main.servers[guild].modules["settings"].settings[setting]
