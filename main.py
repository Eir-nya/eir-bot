#Import all modules to a list
from import_all import modules, globalModules, localModules, discord, inspect, re, asyncio

#Make a reference to the current script
self = inspect.getmodule(inspect.currentframe())

for globalModule in globalModules.values():
	globalModule.main = self

for localModule in localModules.values():
	localModule.main = self

#Define server class
servers = {}	#List of server class instances, one for each server the bot is in
class Server:
	def __init__(self, server=None):
		#Store the actual server object
		self.guild = server
	
	async def Create(self):
		#Create local modules for every server
		self.modules = {}
		self.modules["settings"] = localModules["settings"].this(self)  #Always load the settings module first
		await self.modules["settings"].Create()
		for localModule in localModules.values():
			if localModule != localModules["settings"]:
				self.modules[localModule.name] = localModule.this(self)
				await self.modules[localModule.name].Create()
	
	def on_message(self, client, message):
		for localModule in self.modules:
			if hasattr(localModule, "on_message"):
				localModule.on_message(client, message)

#Command structure for the command system
class Command:
	def __init__(self, parentModule, command):
		self.isGlobal = parentModule.isGlobal
		self.parentModule = parentModule
		self.name = command.__name__
		
		#Inspect the command in question to get its arguments
		self.description = command.__doc__
		sig = inspect.signature(command)
		params = {param : sig.parameters[param] for param in sig.parameters} #Remove `self` and `sourceMessage`
		params.pop("self", None)
		params.pop("sourceMessage", None)
		
		#Generate "usage" example for "help" command
		#[required arg] (optional arg | default value) (*args...)
		self.usage = self.name
		if len(params) > 0:
			for param in params.values():
				self.usage += " "
				#Should apply to all arguments except *args
				if param.kind == inspect.Parameter.POSITIONAL_ONLY or param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
					#No default argument
					if param.default == inspect._empty:
						self.usage += "[" + param.name + "]"
					#Optional argument
					else:
						self.usage += "(" + param.name + (param.default != None and " = " + str(param.default) or "") + ")"
				#*args only
				elif param.kind == inspect.Parameter.VAR_POSITIONAL:
					self.usage += "(...)"
		
		#Get the minimum number of required arguments
		self.minArgs = len(params)
		for param in params:
			param = params[param]
			#Remove *args from the argument list if it's there, as well as optional commands
			if param.kind == inspect.Parameter.VAR_POSITIONAL or param.default != inspect._empty:
				self.minArgs -= 1
		
		#Get the maximum number of possible arguments
		self.maxArgs = len(params)
		for param in params:
			param = params[param]
			#Remove *args from the argument list if it's there
			if param.kind == inspect.Parameter.VAR_POSITIONAL:
				self.maxArgs = -1
				break
	
	async def run(self, sourceMessage, *args):
		#Argument count handling
		if self.maxArgs > -1 and len(args) > self.maxArgs:
			args = args[:self.maxArgs]
		elif self.minArgs > 0 and len(args) < self.minArgs:
			raise TooFewArgumentsException
		
		#Command is from a global module
		if self.isGlobal:
			await getattr(globalModules[self.parentModule.name], self.name)(self.parentModule, sourceMessage, *args)
		#Command is from a local module
		else:
			await getattr(servers[(sourceMessage.guild or "DM")].modules[self.parentModule.name], self.name)(sourceMessage, *args)

#Generate list of commands
commands = {}   #List of commands to be recognized by the command system in on_message

for globalModule in globalModules.values():
	for function in inspect.getmembers(globalModule.this, inspect.isfunction):
		#Methods beginning with "on_" (for discord.py events) or has any capitals, plus "__init" and "Create", don't get processed into commands
		if function[0] != "__init__" and not function[0].startswith("on_") and function[0].islower():
			commands[function[0]] = Command(globalModule, function[1])

#Same as above, but for local modules
for localModule in localModules.values():
	for function in inspect.getmembers(localModule.this, inspect.isfunction):
		if function[0] != "__init__" and not function[0].startswith("on_") and function[0].islower():
			commands[function[0]] = Command(localModule, function[1])

#Error types for command system
class InvalidCommandException(Exception):
	pass

class TooFewArgumentsException(Exception):
	pass

class PermissionException(Exception):
	pass

class CustomResponseException(Exception):
	pass

#Discord bot setup
ready = False
class Client(discord.Client):
	async def on_ready(client):
		print(client.user.name + " signed in!")
		
		#Initialize global modules first (not instanced per server)
		for globalModule in globalModules:
			this = globalModules[globalModule].this
			globalModules[globalModule] = this
			await this.Create(this)
		
		#Special server class for DMs
		servers["DM"] = Server()
		await servers["DM"].Create()
		#Create a server class for every server
		for guild in client.guilds:
			servers[guild] = Server(guild)
			await servers[guild].Create()
		
		global ready
		ready = True

	async def on_message(client, message):
		global ready
		if message.author == client or not ready:
			return;
		
		await client.wait_until_ready()
		
		#Command system
		# prefix = globalModules["util"].CheckPrefix(message)
		# prefix = localModules["settings"].GetSetting("prefix", message.guild)
		prefix = await servers[message.guild in servers and message.guild or "DM"].modules["settings"].GetSetting("prefix")
		content = message.content.lower()
		
		if content.startswith(prefix):
			try:
				args = parse(message.content)
				
				#Check if message starts with a command in the commands list
				commandName = args[0][len(prefix):]
				if commandName in commands:
					args.remove(args[0])
					
					#We will always pass the source message as the first argument, for both global and local arguments
					await commands[commandName].run(message, *args)
				#Invalid command
				else:
					raise InvalidCommandException
			except InvalidCommandException:
				#Add a reaction to the user's message, and give them 30 seconds to edit to a proper command
				await message.add_reaction("\U00002753")	#?
				def sameMessageCheck(payload):
					return payload.message_id == message.id
				
				try:
					payload = await client.wait_for("raw_message_edit", timeout=30.0, check=sameMessageCheck)
					if payload:
						if not content.startswith(prefix):
							return
						
						#Check if new contents are a valid command
						#Sorry for code duplication...(copied from above)
						args = parse(message.content)
						
						#Check if message starts with a command in the commands list
						commandName = args[0][len(prefix):]
						if commandName in commands:
							args.remove(args[0])
							
							#We will always pass the source message as the first argument, for both global and local arguments
							await commands[commandName].run(message, *args)
				except asyncio.TimeoutError:
					pass
				finally:
					await message.remove_reaction("\U00002753", client.user)
			except TooFewArgumentsException:
				await message.add_reaction("\U0000274C")	#X
			except PermissionException:
				await message.add_reaction("\U0001F6AB")	#No entry sign
			except CustomResponseException as CRE:
				await message.channel.send(str(CRE))
		#The following code is for generalized on_message calls, as in NOT the command system
		else:
			for globalModule in globalModules:  #The items in globalModules are now classes
				if hasattr(globalModules[globalModule], "on_message"):
					globalModule.on_message(client, message)
			
			#Messaged from a server
			if message.guild and message.guild in servers:
				servers[message.guild].on_message(client, message)
			#Messaged from dms
			else:
				servers["DM"].on_message(client, message)
		
#Parses a message for arguments
def parse(input):
	output = []
	if len(input.split(" ")) > 1:
		output = [input[0:input.find(" ")]]
		findall = re.findall('"([^"]+)"|\'([^\']+)\'|([^\s]+)', input.split(input.split(" ")[0])[1])
		for item in findall:
			output.append("".join(item))
	elif len(input.split(" ")) == 1:
		output = [input]
	return output

client = Client()
client.run(open("token.txt", "r").read())
