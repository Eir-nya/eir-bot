import os, importlib, sys, inspect, re, asyncio

#Import all modules, but not submodules
os.chdir("modules")

modulesToLoad = [file[:-3] for file in os.listdir() if file.endswith(".py")]
modules = []

for module in modulesToLoad:
	modules.append(importlib.import_module("modules." + module))

#Read all modules and their types (global or local)
globalModules = {}  #List full of classes (instances from modules)
localModules = {}   #List full of modules (python files)

for module in modules:
	name = module.__name__.split("modules.")[1]
	module.name = name
	if len(inspect.getmembers(module, inspect.isclass)) == 0:
		if not hasattr(module, "silent") or module.silent is not True:
			print("WARNING: Module \"" + name + "\" is missing a \"this\" class. Skipping.")
		continue
	if hasattr(module, "isGlobal") and module.isGlobal == True:
		globalModules[name] = module
	else:
		module.isGlobal = False
		localModules[name] = module

#Import from parent folder
os.chdir("../")
sys.path.insert(1, "..")
import lib.discord as discord
