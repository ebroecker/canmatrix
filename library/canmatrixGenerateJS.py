#!/usr/bin/env python
from canmatrix import *

signalShortens = {};
signalShortensIndex = 0;


def generateCode_js(db, botschaften, generatorConfig):
	constants = ""
	macros = ""	
	framedecodeMethods = ""
	framedecodeSwitch = ""
	globalMessagesRaw = ""
	i=0;
	botschafenFeld = "decodeFrameName : function(id) { return this.database[id]; },"
	if(generatorConfig['nice']): 
		botschafenFeld += '\n'
	botschafenFeld += "decode : function(id, d) { if(typeof(this[id]) == \"function\") return this[id](d); else return 0; },"
	if(generatorConfig['nice']): 
		botschafenFeld += '\n'

	constants = "database : {"
	if(generatorConfig['nice']): 
		constants += '\n'
	for botschaftName in botschaften:
		if type(botschaftName).__name__ == 'int':
			botschaft = db.frameById(botschaftName)
		elif type(botschaftName).__name__ == 'instance':
			botschaft = botschaftName		
		else:
			botschaft = db.frameByName(botschaftName)
		i = i + 1

		constants +=  '"' + str(botschaft._Id) + '":"' + botschaft._name + '"'
		if i < len(botschaften):
			constants += ',' 		

		if(generatorConfig['nice']): 
			constants += '\n'

		[code_temp, macro_temp, globalMessagesRaw_temp] = generateSignalMacros_js(botschaft, generatorConfig);
	
		macros += macro_temp
		framedecodeMethods += code_temp
		if i < len(botschaften):
			framedecodeMethods += ',\n' 
	constants += "},\n"
	return  botschafenFeld, constants, macros, globalMessagesRaw, framedecodeMethods, framedecodeSwitch



def generateSignalMacros_js(botschaft, generatorConfig):
	macros = ""
	globalMessagesRaw = ""
	global signalShortensIndex
	framedecodeMethods = '"' + str(botschaft._Id)+ "\" : function(f)\n{ t=this;return {"
	if(generatorConfig['nice']): 
		framedecodeMethods += '\n'

	i = 0;
	for signal in botschaft._signals:
		if signal._name not in signalShortens:
			signalShortens[signal._name] = str(signalShortensIndex)
			signalShortensIndex = signalShortensIndex + 1

		if(generatorConfig['nice']): 		
			framedecodeMethods +=  "\"" + signal._name + '":[t._' + signal._name + "(f),\n"
			framedecodeMethods +=  't._' + signal._name + "(f)"
			if signal._factor != 1:
				framedecodeMethods += "*" + str(signal._factor)
			if signal._offset != 0:
				if float(signal._offset) < 0:
					framedecodeMethods += str(signal._offset)
				else:
					framedecodeMethods += "+" + str(signal._offset)
			framedecodeMethods += "]\n"

		else: 
			framedecodeMethods +=  "\"" + signal._name + '":[t._' + signalShortens[signal._name] + "(f),"
			framedecodeMethods += 't._' + signalShortens[signal._name] + "(f)"
			if signal._factor != 1:			
				framedecodeMethods += "*" + str(signal._factor)
			if signal._offset != 0:
				framedecodeMethods += "+" + str(signal._offset) 
			framedecodeMethods += "]\n"

#			framedecodeMethods +=  "\"" + signal._name + '_S":t._' + signalShortens[signal._name] + "(f)*" + str(signal._factor) + "+" + str(signal._offset) 
 		i += 1
		if i < len(botschaft._signals):
			framedecodeMethods += ","
		if generatorConfig['nice']:
			framedecodeMethods += "\n"

		if signal._valuetype == '-':
			macros  += "/* only unsigned signals supported: " + signal._name
			continue	
		if signal._byteorder == 1:
			if ((signal._startbit % 8) + signal._signalsize) > 8:
				macros += "/* " + signal._name + " getMacro generation not jet supportet */\n"				
			else:
				startbyte = signal._startbit / 8
				startbit = signal._startbit % 8								
				mask = (2 << (signal._signalsize-1)) - 1
								
				if(generatorConfig['nice']): 		
					macros += "_" + signal._name + ":function(d){return ("			
				else:
					macros += "_" + signalShortens[signal._name] + ":function(d){return ("			
				if startbit == 0:
					macros += "d[" + str(startbyte) + "]"   
				else:
					macros += "(d[" + str(startbyte) + "]>>>" + str(startbit) + ")" 
				if mask != 0xff:
					macros += "&" + hex(mask) 
				macros += ")>>>0;},"
				if(generatorConfig['nice']): 
					macros += '\n'

		else: # Motorola 
#TODO flasche Bits bei nicht-vollständigen Bytes...
			startbyte = (signal._startbit / 8)
			startbit = 7 - ( signal._startbit % 8)			

			if startbit + signal._signalsize > 8:
				if (startbit + signal._signalsize) % 8 != 0:
					macros +=  " /* Startbyte ist kein ganzes Byte, Generator-Implementierung nicht vollstaendig v */"
					print "Error Generierungs-Script hier unvollstaendig: " + botschaft._name + " " + signal._name
				else:
					if(generatorConfig['nice']): 		
						macros += "_" + signal._name + " : function(d) { return ("
					else:
						macros += "_" + signalShortens[signal._name] + " : function(d) { return ("
				sizeInByte = signal._signalsize / 8 + ((signal._signalsize % 8) > 0)

				for index in range(0, sizeInByte):
					if (index < sizeInByte-1) or ((signal._signalsize % 8) == 0):
						cfindex = 7-(index+startbyte)						
						cfindex = (sizeInByte-index)+startbyte-1					
						if index > 0:
							macros += "d[" + str(cfindex) + "]<<" + str(index*8)
						else:
							macros += "d[" + str(cfindex) + "]"
						if index < sizeInByte-1:
							macros += " | "
					else:
						cfindex = 7-(index+startbyte)						
						cfindex = (sizeInByte-index)+startbyte-1	
						mask = (2 << ((signal._signalsize % 8)-1)) - 1 
						macros += "(d[" + str(cfindex) + "]<<" + str(index*8) +")&" + hex(mask)
				macros += ")>>>0;},"
				if(generatorConfig['nice']): 
					macros += '\n'

			else:
				macros += "/* " + signal._name + " getMacro (2) generation not jet supportet */\n"				
				print "Error Generierungs-Script hier unvollstaendig: " + botschaft._name + " " + signal._name
	framedecodeMethods += "};}"
	return framedecodeMethods, macros, globalMessagesRaw 
#Ende generateSignalMacrosSel
