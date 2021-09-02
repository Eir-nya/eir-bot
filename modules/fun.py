import random

isGlobal = False

rpsSymbs = ["\U0000270A", "\U0000270B", "\U0000270C"] #Rock, paper, and scissors
rpsResultsSymbs = ["🏆", "🚫", "⚖"] #Win, lose, and tie #TODO: convert to \U
eightBallResponses = [
	"A thousand times \"yes\".",
	"Positive.",
	"You can be sure of it.",
	"Believe it to be so.",
	"Absolutely.",
	"Outlook is good.",
	"I guarantee it.",
	"No doubt about it.",
	
	"A thousand times \"no\".",
	"Negative.",
	"Don't count on it.",
	"When pigs fly.",
	"Not a chance.",
	"Not at all.",
	
	"Ehh, fifty-fifty.",
	"Unsure.",
	"I'm thinking a solid \"maybe\".",
	"I'm not sure.",
	"I'm drawing a blank here.",
]
minesweeperSymbols = {
	"mine" : ":bomb:",
	"free" : "⬜",#":white_large_square:",
	1	  : ":one:",
	2	  : ":two:",
	3	  : ":three:",
	4	  : ":four:",
	5	  : ":five:",
	6	  : ":six:",
	7	  : ":seven:",
	8	  : ":eight:",
}

class this:
	def __init__(self, server):
		self.server = server
	
	async def Create(self):
		#Set up the minesweeper command with its default values equal to the values from the settings module
		defaultMines = await self.server.modules["settings"].GetSetting("minesweeper default mines")
		defaultWidth = await self.server.modules["settings"].GetSetting("minesweeper default width")
		defaultHeight = await self.server.modules["settings"].GetSetting("minesweeper default height")
		
		#Replacement function
		async def minesweeper(sourceMessage, mines=defaultMines, width=defaultWidth, height=defaultHeight):
			#Argument type handling
			try:
				mines = int(mines)
				width = int(width)
				height = int(height)
			except:
				raise main.InvalidCommandException
			
			#Move arguments into range
			if mines < 1:
				mines = defaultMines
			if width < 1:
				width = defaultWidth
			if height < 1:
				height = defaultHeight
			await self.Minesweeper(sourceMessage, mines, width, height)
		minesweeper.__doc__ = self.Minesweeper.__doc__
		setattr(self, "minesweeper", minesweeper)
		main.commands["minesweeper"] = main.Command(main.localModules[name], self.minesweeper)
	
	async def rps(self, sourceMessage, quiet=False):
		"""Play rock-paper-scissors with the bot.
Use `[prefix]rps quiet` and the bot won't send a new message."""
		
		if str(quiet).lower() == "quiet":
			quiet = True
		
		#Send the message in question
		if quiet:
			msg = sourceMessage
		else:
			msg = await sourceMessage.channel.send(content="Rock-Paper-Scissors...")
		for symb in rpsSymbs:
			await msg.add_reaction(symb)
		
		def reactCheck(reaction, user):
			return user == sourceMessage.author and str(reaction.emoji) in rpsSymbs
		
		#Store the user's reaction
		try:
			userchoice = await main.client.wait_for('reaction_add', timeout=30.0, check=reactCheck)
			userchoice = userchoice[0]
		except asyncio.TimeoutError:
			if quiet:
				for symb in rpsSymbs:
					await msg.remove_reaction(symb, main.client.user)
			else:
				await msg.delete()
			return
		
		#Pick a random symbol
		botchoice = rpsSymbs[random.randint(0, len(rpsSymbs)-1)]
		
		for symb in rpsSymbs:
			await msg.remove_reaction(symb, main.client.user)
			try:
				await msg.remove_reaction(userchoice, sourceMessage.author)
				await msg.clear_reactions()
			except:
				pass
		
		#Results
		if quiet:
			results = RPSResults(userchoice, botchoice)
			
			#Win
			if results.startswith("You win!"):
				await msg.add_reaction(rpsResultsSymbs[0])
			#Lose
			elif results.startswith("You lose!"):
				await msg.add_reaction(rpsResultsSymbs[1])
			#Tie
			else:
				await msg.add_reaction(rpsResultsSymbs[2])
		else:
			await msg.edit(content=RPSResults(userchoice, botchoice))
	
	#NOTE: I can't type "8ball" as the name of the function, so I have to add it with setattr (below)
	async def EightBall(self, sourceMessage, *args):
		"""Ask the magic 8-ball your questions!
Assumes you ask with a yes/no prompt."""
		response = eightBallResponses[random.randint(0, len(eightBallResponses) - 1)]
		
		if len(args) == 0:
			response = "Please provide a query for the ball!"
		
		#await sourceMessage.channel.send(content=":8ball:: " + response)
		# util = main.globalModules["util"]
		# embed = util.CreateEmbed(title="Magic 8-ball", description=":8ball:: " + response, colour=0x080808, footerText="Usage: `" + util.CheckPrefix(sourceMessage) + main.commands["8ball"].usage + "`")
		prefix = await self.server.modules["settings"].GetSetting("prefix")
		embed = main.globalModules["util"].CreateEmbed(main.globalModules["util"], title="Magic 8-ball", description=":8ball:: " + response, colour=main.discord.Colour.darker_grey(), footerText="Usage: `" + prefix + main.commands["8ball"].usage + "`")
		await sourceMessage.channel.send(embed=embed)
	
	#NOTE: The arguments here will actually change according to values in the settings, so this command actually gets added up above, in __init__
	async def Minesweeper(self, sourceMessage, mines=0, width=0, height=0):
		"""Play a discord spoiler tag-based game of minesweeper.
You can customize the number of mines and size of the board."""
		board = MakeBoard(min(mines, width * height), width, height)
		
		#Convert to discord message
		gameText = ""
		for row in board:
			for space in row:
				gameText += "||" + space + "|| "
			gameText += "\n"
		
		#Send the message in question
		prefix = await self.server.modules["settings"].GetSetting("prefix")
		embed = main.globalModules["util"].CreateEmbed(main.globalModules["util"], title="Minesweeper", colour=main.discord.Colour.dark_grey(), description=gameText, footerText="Usage: `" + prefix + main.commands["minesweeper"].usage + "`")
		embed.add_field(name="Game info", value="Mines: " + str(mines) + "\nSize: " + str(width) + " wide, " + str(height) + " tall (" + str(width * height) + " total)")
		
		try:
			await sourceMessage.channel.send(embed=embed)
		except main.discord.HTTPException as e:
			await sourceMessage.channel.send(content="Message could not be sent! The game board is too big, and it hit discord's character limit.")
		except Exception as e:
			await sourceMessage.channel.send(content="Error: " + str(e))

setattr(this, "8ball", this.EightBall)
getattr(this, "8ball").__name__ = "8ball"

#Function to check who won at RPS, and return a "you lose"/"you win" string
def RPSResults(userchoice, botchoice):
	if userchoice.emoji == botchoice:
		return "It's a tie! (" + botchoice + ")"
	else:
		#User picked Rock
		if userchoice.emoji == rpsSymbs[0]:
			#You lose! (Paper covers Rock)
			if botchoice == rpsSymbs[1]:
				return "You lose! (" + botchoice + " covers " + userchoice.emoji + ")"
			#You win! (Rock beats Scissors)
			elif botchoice == rpsSymbs[2]:
				return "You win! (" + userchoice.emoji + " beats " + botchoice + ")"
		#User picked Paper
		elif userchoice.emoji == rpsSymbs[1]:
			#You lose! (Scissors cuts Paper)
			if botchoice == rpsSymbs[2]:
				return "You lose! (" + botchoice + " cuts " + userchoice.emoji + ")"
			#You win! (Paper covers Rock)
			elif botchoice == rpsSymbs[1]:
				return "You win! (" + userchoice.emoji + " covers " + botchoice + ")"
		#User picked Scissors
		elif userchoice.emoji == rpsSymbs[2]:
			#You lose! (Rock beats Scissors)
			if botchoice == rpsSymbs[0]:
				return "You lose! (" + botchoice + " beats " + userchoice.emoji + ")"
			#You win! (Scissors cuts Paper)
			elif botchoice == rpsSymbs[1]:
				return "You win! (" + userchoice.emoji + " cuts " + botchoice + ")"

#Function to create a board for minesweeper
def MakeBoard(mines, width, height):
	board = []
	
	for y in range(0, height):
		board.append([])
		for x in range(0, width):
			board[y].append(minesweeperSymbols["free"])
	
	#Place mines
	for i in range(0, mines):
		#Emergency break counter, to prevent infinite loops
		breakCounter = 0
		
		while True:
			x = random.randint(0, width - 1)
			y = random.randint(0, height - 1)
			
			#Space is valid, place a mine
			if board[y][x] == minesweeperSymbols["free"]:
				board[y][x] = minesweeperSymbols["mine"]
				break
			else:
				breakCounter += 1
				if breakCounter == mines * 3:
					break
				else:
					continue
	
	#Place numbers
	for y in range(0, len(board)):
		for x in range(0, len(board[y])):
			if board[y][x] == minesweeperSymbols["mine"]:
				continue
			
			#Count surrounding mines (top to bottom, left to right)
			nearbyMines = 0
			for y2 in range(max(y - 1, 0), min(y + 2, height)):
				for x2 in range(max(x - 1, 0), min(x + 2, width)):
					if board[y2][x2] == minesweeperSymbols["mine"]:
						nearbyMines += 1
			
			if nearbyMines > 0:
				board[y][x] = minesweeperSymbols[nearbyMines]
	
	return board
