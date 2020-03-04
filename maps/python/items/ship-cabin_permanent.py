# Script for the Ship's Cabin functionality
#
# Written by James W. Bennett in 2020, based on Nicolas Weeger's "banquet.py" script from 2007
# Released as GPL
# Original concept/reason for writing was Titus', for their "HeroWorld" server
#
# This script teleports the player to a ship's cabin.
# When they exit the cabin, they should appear wherever the ship is, rather than where it was.
#
# TODO: Player can't exit the map if the map with the ship on it gets unloaded.  Maybe store the current map whenever the ship is applied, and use that as a fallback?  The fallback map could be stored as a key on the exit door.
#

import Crossfire
import random
import os.path
import CFDataBase
from shutil import copyfile

# This is where the pointer to the ship is stored.
cabindict = Crossfire.GetPrivateDictionary()

# l is the item being activated, probably the ship cabin's door
l = Crossfire.WhoAmI()
# act is the player
act = Crossfire.WhoIsActivator()

def return_to_bed():
	#If the script breaks for some reason, return the player to their spawn point.
	flags = 0
	if (act.BedMap.find(Crossfire.PlayerDirectory()) != -1):
		# Unique map
		flags = 2
	dest = Crossfire.ReadyMap(act.BedMap, flags)
	if (dest == None):
		act.Message('The %s seems broken.'%l.Name)
		return

	act.Teleport(dest, act.BedX, act.BedY)

def do_back():
	# Teleports the player from the cabin to the current location of the ship.
	
	# Grabs the stored pointer to the ship cabin.  We need this to get the location, so we can teleport the player to the ship.
	shiploc = cabindict.get(act.Name)
	
	#act.Message('CabinDict: ' + str(cabindict[act.Name]))
	#act.Message('Ship x, y: ' + str(shiploc.X) + ', ' + str(shiploc.Y))
	
	# Grabs the ship information from the ship cabin's pointer.  The cabin's "Env" should be the ship's pointer.  "sm" is the map that the ship is in.
	x = shiploc.Env.X
	y = shiploc.Env.Y
	sm = shiploc.Env.Map.Path

	if x == '' or y == '' or sm == '':
		# If something's not getting grabbed, teleport the player back to their spawn point instead.
		act.Message('You feel a distorsion of reality!')
		return_to_bed()
		return
	
	# Tells the server to load the map (before teleporting the playing there)
	dest = Crossfire.ReadyMap(sm)
	
	if (dest == None):
		# Weeger thinks this can happen if we teleport from a random map.  Probably not an issue for us, but let's leave it in just in case.
		act.Message('The %s rattles. It can\'t take you back to your starting point.'%l.Name)
		return_to_bed()
		return

	act.Message('You exit the ship\'s cabin.')
	act.Teleport(dest, int(x), int(y))

def do_cabin():
	#This both creates the cabin and teleports the player to it.
	
	cabindict[act.Name] = Crossfire.WhoAmI()# Stores a pointer to the ship's door's location, and associates it with the activating player.
	
	if l.ReadKey('ship_serial') is not '':
		shipserial = str(l.ReadKey('ship_serial'))
		dest = Crossfire.ReadyMap('/ship-cabins/cabin-' + shipserial)
		act.Message('You enter the ship\'s cabin.')
		act.Teleport(dest, 0, 0)
	else:
		datadir = Crossfire.DataDirectory()
		mapdir = Crossfire.MapDirectory()
		# This stores an incrementing number that uniquely identifies the cabin map.  We will later write this number, as a key, to the cabin door.
		if not os.path.exists(str(datadir) + '/' + str(mapdir) + '/ship-cabins/ship-serial.txt'):# Create the file if it doesn't exist, and set the counter to 0.
			with open(str(datadir) + '/' + str(mapdir) + '/ship-cabins/ship-serial.txt', 'w') as shipfile:
				shipfile.write('0')
		with open(str(datadir) + '/' + str(mapdir) + '/ship-cabins/ship-serial.txt', 'r+') as shipfile:# Grab the current serial, then increment it because we have a new ship's cabin
			shipserial = shipfile.read()
			act.Message('Old shipserial: ' + str(shipserial))
			shipserial = int(shipserial)
			shipserial += 1
			shipserial = str(shipserial)
			act.Message('New shipserial: ' + str(shipserial))
		with open(str(datadir) + '/' + str(mapdir) + '/ship-cabins/ship-serial.txt', 'w') as shipfile:# Overwrite the old file with the new serial
			shipfile.write(str(shipserial))
		
		template = (str(datadir) + '/' + str(mapdir) + '/ship-cabins/cabin-template')# Template for the cabin map.  We could have this randomly picked from a list of template maps, but right now we just have the one template.
		cabinfile = (str(datadir) + '/' + str(mapdir) + '/ship-cabins/cabin-' + shipserial)# Names our copy of the template map as ending in the serial number, like "cabin-7"
		if not os.path.exists(cabinfile):# If the map doesn't exist (it shouldn't), we create it.
			copyfile(template, cabinfile)
			dest = Crossfire.ReadyMap('/ship-cabins/cabin-' + shipserial)
			# Invisible exit, it decouples the player and the ship.  Should be at x,y = 0,0, and the player should enter the map at those coords.  HP and SP are x,y of where the inex will teleport the player afterward.
			inex = Crossfire.CreateObjectByName('invis_exit')
			inex.Slaying = dest.Path
			inex.HP = 8
			inex.SP = 4
			inex.Teleport(dest, 0, 0)
			# The cabin's exit door.
			cabexdoor = Crossfire.CreateObjectByName('tree5')# Avoiding making it an actual exit, because the "unique" flag does special things to exits (and we don't want that)
			cabexdoor.Unique = 1
			cabexdoor.Face = 'oakdoor_1.111'
			cabexdoor.Name = 'oak door'
			cabexdoor.Teleport(dest, 8, 4)
			cabexdoor.WriteKey('cabin_exit', '1', 1)
			cabexeva = Crossfire.CreateObjectByName('event_apply')# The script that we attach to the door, to return the player to the current boat location
			cabexeva.Title = 'Python'
			cabexeva.Slaying = '/python/items/ship-cabin_permanent.py'# Point this to the name of the file you are currently reading this comment in, unless you're doing something janky.
			cabexeva.InsertInto(cabexdoor)# Attaching the script to the door
			l.WriteKey('ship_serial', str(shipserial), 1)
		# Teleport
			act.Message('You enter the ship\'s cabin.')
			act.Teleport(dest, 0, 0)
		else:
			act.Message('ERROR: The cabin map file already exists, but the door didn\'t have a connector to it.  The contents of the /ship-cabins/ directory may need fixing.')
	
if l.ReadKey('cabin_exit') is '1':
	do_back()
else:
	do_cabin()

Crossfire.SetReturnValue(1)
