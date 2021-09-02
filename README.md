# eir-bot

![Eir-bot](https://github.com/Eir-nya/eir-bot/blob/main/eir-bot.png)

This is an archive of my personal discord bot, used in my private server. I wrote it from scratch using discord.py, and I'm somewhat proud of it, even if I didn't put that many uses into it.

One thing it does is automatically generate output for the `!help` command when commands are registered and added to the source. It does this by reading their docstring.

Another thing it does is use a simple modules system - demonstrated by my existing modules, as well as the test ones in the "old" subfolder.

It also uses sqlite3 to store settings information per-server, in a locally-generated sql file (one per server). Admins in servers with the bot can change its prefix for that server, as well as the default settings for the minesweeper game.  
Worth noting is that the bot works with DMs, and treats DMs as a whole as one server with the default settings only.

&nbsp;

This bot is still active in my server at the time of writing, albeit not used. The reason I'm archiving it now is because of the recent news of the shutting down of discord.py, as well as discord's heavy API changes for bots in the future.
