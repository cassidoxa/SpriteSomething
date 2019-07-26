import importlib
import itertools
import json
from source.spritelib import SpriteParent
from source import common
from . import rom_import, rom_export, rdc_export

class Sprite(SpriteParent):
	def __init__(self, filename, manifest_dict, my_subpath):
		super().__init__(filename, manifest_dict, my_subpath)

		self.overview_scale_factor = 1    #Samus's sheet is BIG, so don't zoom in on the overview

		self.overhead = False   #Samus is sideview, so only left/right direction buttons should show

		#TODO: Make file select and ship be animations in the big list, or tie to the ship background
		# self.plugins += [
		# 	("File Select Preview",None,None),
		# 	("Ship Preview",None,None)
		# ]

	def import_from_ROM(self, rom):
		#The history of the Samus import code is a story I will tell to my children
		self.images = rom_import.rom_import(self, rom)
		self.master_palette = list(self.images["palette_block"].getdata())

	def inject_into_ROM(self, rom):
		#The history of the Samus export code is a story I will tell to my grandchildren
		return rom_export.rom_export(self, rom)

	def get_rdc_export_blocks(self):
		SAMUS_EXPORT_BLOCK_TYPE = 4
		return [(SAMUS_EXPORT_BLOCK_TYPE,rdc_export.get_raw_rdc_samus_block(self))]

	def get_colors_from_master(self, color_set):
		#for internal class use.  For general use, call get_timed_palette()
		color_set_switcher = {
			"power": [0,15],
			"base": [0,15],
			"varia": [15,30],
			"gravity": [30,45],
			"death": [45,60],
			"flash": [60,75],
			"fileselect": [75,90],
			"door": [3],
			"xray": [91,94],
			"ship": [101,104]
		}
		master_palette_indexes = color_set_switcher.get(color_set.lower().replace(' ',"").replace('-',"").replace('_',""))
		if len(master_palette_indexes) == 1:
			return self.master_palette[master_palette_indexes[0]]
		elif len(master_palette_indexes) == 2:
			return self.master_palette[master_palette_indexes[0]:master_palette_indexes[1]]
		else:
			raise AssertionError(f"Unrecognized color set request: {color_set}")

	def get_timed_palette(self, overall_type="power", variant_type="standard"):
		timed_palette = []
		base_palette = self.get_colors_from_master(overall_type)

		if overall_type.lower() == "ship" or variant_type.lower() == "ship":
			ship_color_body, ship_color_window, ship_glow_color = self.get_colors_from_master("ship")

			if variant_type.lower() == "outro" or variant_type.lower() == "intro":
				#11 customizable colors
				ship_palette = []
				ship_palette.append(tuple(channel+72 for channel in ship_color_body))
				ship_palette.append(tuple(25/21*channel for channel in ship_color_body))
				ship_palette.append(tuple(10/21*channel for channel in ship_color_body))
				ship_palette.append(tuple( 0/21*channel for channel in ship_color_body))
				ship_palette.append(tuple(channel+5 for channel in ship_color_body))
				ship_palette.append(tuple(22/21*channel for channel in ship_color_body))
				ship_palette.append(tuple(18/21*channel for channel in ship_color_body))
				ship_palette.append(tuple(13/21*channel for channel in ship_color_body))
				ship_palette.append(ship_color_window)
				ship_palette.append(tuple(0.7*channel for channel in ship_color_window))
				ship_palette.append(tuple(0.4*channel for channel in ship_color_window))
				#and then 4 colors that are part of the underrigging which aren't coded to customize
				ship_palette.extend([(48,48,72),(16,16,40),(0,0,0),(0,0,0)])
				if variant_type.lower() == "intro":
					timed_palette = [(0, ship_palette)]
				else:   #outro
					timed_palette = [(0x18, common.palette_pull_towards_color(ship_palette,(0xFF,0xFF,0xFF),(float(15-i)/15.0))) for i in range(15)]
					timed_palette.append((0, ship_palette))

			else:     #standard ship colors with underglow
				#11 customizable colors
				ship_palette = []
				ship_palette.append(ship_color_body)
				ship_palette.append(tuple(16/21*channel for channel in ship_color_body))
				ship_palette.append(tuple( 3/21*channel for channel in ship_color_body))
				ship_palette.append(tuple( 1/21*channel for channel in ship_color_body))
				ship_palette.append(tuple(17/21*channel for channel in ship_color_body))
				ship_palette.append(tuple(13/21*channel for channel in ship_color_body))
				ship_palette.append(tuple( 9/21*channel for channel in ship_color_body))
				ship_palette.append(tuple( 4/21*channel for channel in ship_color_body))
				ship_palette.append(ship_color_window)
				ship_palette.append(tuple(0.7*channel for channel in ship_color_window))
				ship_palette.append(tuple(0.4*channel for channel in ship_color_window))
				#and then 3 colors that are part of the underrigging which aren't coded to customize
				ship_palette.extend([(48,48,72),(16,16,40),(0,0,0)])
				#then 1 more color for the underglow
				timed_palette = [(5, ship_palette + common.palette_pull_towards_color([ship_glow_color], (0,0,0), abs(float(7-i)/7.0))) for i in range(14)]

		elif variant_type.lower() == "standard":
			timed_palette = [(0, self.get_colors_from_master(overall_type))]

		elif variant_type.lower() == "loader":
			for _ in range(0x27):   #in the ROM, this is encoded as 0x24 + 0x03
				timed_palette.append((3,base_palette))
				timed_palette.append((3,common.palette_shift(base_palette,(0,80,120))))
			for _ in range(3):
				timed_palette.append((3,base_palette))
				timed_palette.append((3,common.palette_shift(base_palette,(0,40,120))))
			for _ in range(2):
				timed_palette.append((3,base_palette))
				timed_palette.append((3,common.palette_shift(base_palette,(0,0,80))))
			timed_palette.append((0,base_palette))

		elif variant_type.lower() == "heat":
			timed_palette.append((16,common.palette_shift(base_palette,(0,0,0))))
			timed_palette.append((4,common.palette_shift(base_palette,(8,0,0))))
			timed_palette.append((4,common.palette_shift(base_palette,(8,0,0))))
			timed_palette.append((5,common.palette_shift(base_palette,(16,0,0))))
			timed_palette.append((6,common.palette_shift(base_palette,(16,0,0))))
			timed_palette.append((7,common.palette_shift(base_palette,(24,0,0))))
			timed_palette.append((8,common.palette_shift(base_palette,(24,0,0))))
			timed_palette.append((8,common.palette_shift(base_palette,(40,0,0))))
			timed_palette.append((8,common.palette_shift(base_palette,(40,0,0))))
			timed_palette.append((8,common.palette_shift(base_palette,(24,0,0))))
			timed_palette.append((7,common.palette_shift(base_palette,(24,0,0))))
			timed_palette.append((6,common.palette_shift(base_palette,(16,0,0))))
			timed_palette.append((5,common.palette_shift(base_palette,(16,0,0))))
			timed_palette.append((4,common.palette_shift(base_palette,(8,0,0))))
			timed_palette.append((4,common.palette_shift(base_palette,(8,0,0))))
			timed_palette.append((3,common.palette_shift(base_palette,(8,0,0))))

		elif variant_type.lower() == "charge":
			timed_palette = [(1, common.palette_pull_towards_color(base_palette,(0xFF,0xFF,0xFF),float(i)/8.0)) for i in range(8)]

		elif variant_type.lower().replace("_"," ") == "speed boost":
			timed_palette.append((4,common.palette_shift(base_palette,(0,0,0))))
			timed_palette.append((4,common.palette_shift(base_palette,(0,0,80))))
			timed_palette.append((4,common.palette_shift(base_palette,(0,40,160))))
			timed_palette.append((0,common.palette_shift(base_palette,(20,100,240))))  #(0,120,160)

		elif variant_type.lower().replace("_"," ") == "speed squat":
			#i = 0 1 2 3 2 1 0 2 3 2 1 0 1 2...
			timed_palette.extend([(1,common.palette_pull_towards_color(base_palette,(0xFF,0xFF,0xFF),float(i)/4.0)) for i in range(4)])
			timed_palette.extend([(1,common.palette_pull_towards_color(base_palette,(0xFF,0xFF,0xFF),float(i)/4.0)) for i in [2,1]])

		elif variant_type.lower().replace("_","").replace(" ","") == "shinespark":
			timed_palette.append((1,common.palette_shift(base_palette,(0,0,0))))
			timed_palette.append((1,common.palette_shift(base_palette,(64,64,32))))
			timed_palette.append((1,common.palette_shift(base_palette,(104,104,0))))
			timed_palette.append((1,common.palette_shift(base_palette,(176,176,64))))

		elif variant_type.lower().replace("_"," ") == "screw attack":
			timed_palette.append((1,common.palette_shift(base_palette,(0,0,0))))
			timed_palette.append((1,common.palette_shift(base_palette,(0,64,0))))
			timed_palette.append((1,common.palette_shift(base_palette,(0,128,0))))
			timed_palette.append((1,common.palette_shift(base_palette,(0,192,40))))
			timed_palette.append((1,common.palette_shift(base_palette,(0,128,0))))
			timed_palette.append((1,common.palette_shift(base_palette,(0,64,0))))

		elif variant_type.lower().replace("_"," ") == "hyper":
			grayscale_palette = common.grayscale(self.get_colors_from_master("gravity"))
			faded_palette = common.palette_pull_towards_color(grayscale_palette,(0,0,0),2.0/3.0)
			timed_palette.append((2,common.palette_shift(faded_palette,(0xE0,0x20,0x20))))
			timed_palette.append((2,common.palette_shift(faded_palette,(0xE0,0x68,0x10))))
			timed_palette.append((2,common.palette_shift(faded_palette,(0xE0,0xE0,0x00))))
			timed_palette.append((2,common.palette_shift(faded_palette,(0x58,0xE0,0x00))))
			timed_palette.append((2,common.palette_shift(faded_palette,(0x00,0xE0,0x00))))
			timed_palette.append((2,common.palette_shift(faded_palette,(0x08,0x85,0x40))))
			timed_palette.append((2,common.palette_shift(faded_palette,(0x08,0x60,0x80))))
			timed_palette.append((2,common.palette_shift(faded_palette,(0x50,0x30,0x90))))
			timed_palette.append((2,common.palette_shift(faded_palette,(0x90,0x00,0x90))))
			timed_palette.append((2,common.palette_shift(faded_palette,(0xA8,0x10,0x58))))

		elif variant_type.lower().replace("_"," ") == "death suit":
			timed_palette.append((21, common.palette_pull_towards_color(base_palette,(0xFF,0xFF,0xFF),float(0.0)/8.0)))
			timed_palette.append((6, common.palette_pull_towards_color(base_palette,(0xFF,0xFF,0xFF),float(1.0)/8.0)))
			timed_palette.append((3, common.palette_pull_towards_color(base_palette,(0xFF,0xFF,0xFF),float(2.0)/8.0)))
			timed_palette.append((4, common.palette_pull_towards_color(base_palette,(0xFF,0xFF,0xFF),float(3.0)/8.0)))
			timed_palette.append((5, common.palette_pull_towards_color(base_palette,(0xFF,0xFF,0xFF),float(4.0)/8.0)))
			timed_palette.append((5, common.palette_pull_towards_color(base_palette,(0xFF,0xFF,0xFF),float(5.0)/8.0)))
			timed_palette.append((6, common.palette_pull_towards_color(base_palette,(0xFF,0xFF,0xFF),float(6.0)/8.0)))
			timed_palette.append((6, common.palette_pull_towards_color(base_palette,(0xFF,0xFF,0xFF),float(7.0)/8.0)))
			timed_palette.append((80, common.palette_pull_towards_color(base_palette,(0xFF,0xFF,0xFF),float(8.0)/8.0)))

		elif variant_type.lower() == "death":
			death_palette = self.get_colors_from_master("death")
			timed_palette.append((21, common.palette_pull_towards_color(death_palette,(0xFF,0xFF,0xFF),float(0.0)/8.0)))
			timed_palette.append((6, common.palette_pull_towards_color(death_palette,(0xFF,0xFF,0xFF),float(1.0)/8.0)))
			timed_palette.append((3, common.palette_pull_towards_color(death_palette,(0xFF,0xFF,0xFF),float(2.0)/8.0)))
			timed_palette.append((4, common.palette_pull_towards_color(death_palette,(0xFF,0xFF,0xFF),float(3.0)/8.0)))
			timed_palette.append((5, common.palette_pull_towards_color(death_palette,(0xFF,0xFF,0xFF),float(4.0)/8.0)))
			timed_palette.append((5, common.palette_pull_towards_color(death_palette,(0xFF,0xFF,0xFF),float(5.0)/8.0)))
			timed_palette.append((6, common.palette_pull_towards_color(death_palette,(0xFF,0xFF,0xFF),float(6.0)/8.0)))
			timed_palette.append((6, common.palette_pull_towards_color(death_palette,(0xFF,0xFF,0xFF),float(7.0)/8.0)))
			timed_palette.append((80, common.palette_pull_towards_color(death_palette,(0xFF,0xFF,0xFF),float(8.0)/8.0)))

		elif variant_type.lower() == "flash":
			flash_master_palette = self.get_colors_from_master("flash")
			flash_bright_portion = flash_master_palette[:9]
			flash_rotating_portion = flash_master_palette[9:]
			timed_palette.append((2,common.palette_shift(flash_bright_portion,(0,0,0))    + flash_rotating_portion[6:] + flash_rotating_portion[:6]))
			timed_palette.append((2,common.palette_shift(flash_bright_portion,(24,24,24))    + flash_rotating_portion[5:] + flash_rotating_portion[:5]))
			timed_palette.append((2,common.palette_shift(flash_bright_portion,(56,56,56))    + flash_rotating_portion[4:] + flash_rotating_portion[:4]))
			timed_palette.append((2,common.palette_shift(flash_bright_portion,(88,88,88)) + flash_rotating_portion[3:] + flash_rotating_portion[:3]))
			timed_palette.append((2,common.palette_shift(flash_bright_portion,(56,56,56))    + flash_rotating_portion[2:] + flash_rotating_portion[:2]))
			timed_palette.append((2,common.palette_shift(flash_bright_portion,(24,24,24))    + flash_rotating_portion[1:] + flash_rotating_portion[:1]))

		elif variant_type.lower() == "sepia":
			timed_palette = [(0, common.sepia(self.get_colors_from_master("power")))]

		elif variant_type.lower().replace("_"," ") == "sepia hurt":
			sepia_palette = common.sepia(self.get_colors_from_master("power"))
			timed_palette = [(0, common.palette_pull_towards_color(sepia_palette,(0xFF,0xFF,0xFF),0.6))]

		elif variant_type.lower() == "door":
			TRANSITION_TIME = 30
			visor_color = self.get_colors_from_master("power")[3]
			for i in range(13):
				[new_visor_color] = common.palette_pull_towards_color([visor_color],base_palette[3],float(i)/13.0)
				dimmed_base_palette = common.palette_pull_towards_color(base_palette,(0,0,0),float(13-i)/13.0)
				dimmed_base_palette[3] = new_visor_color
				timed_palette.append((3,dimmed_base_palette))
			timed_palette.append((TRANSITION_TIME,base_palette))
			for i in range(13):
				[new_visor_color] = common.palette_pull_towards_color([visor_color],base_palette[3],float(12-i)/13.0)
				dimmed_base_palette = common.palette_pull_towards_color(base_palette,(0,0,0),float(1+i)/13.0)
				dimmed_base_palette[3] = new_visor_color
				timed_palette.append((3,dimmed_base_palette))
			timed_palette.append((TRANSITION_TIME,[(0,0,0) for _ in range(15)]))

		elif variant_type.lower().replace("-", "").replace("_","") == "xray":
			visor_colors = self.get_colors_from_master("xray")
			timed_palette = [(6, base_palette[:3]+[color]+base_palette[4:]) for color in visor_colors]

		elif variant_type.lower().replace("_", " ") == "file select":
			timed_palette = [(0, self.get_colors_from_master("file select"))]

		else:
			raise AssertionError(f"unrecognized palette request: {overall_type}, {variant_type}")

		#now scrub the palette to get rid of floats and numbers that are too large/small
		return [(time,[(max(0,min(255,int(color_plane))) for color_plane in color) for color in palette]) for (time,palette) in timed_palette]

	def get_current_pose_list(self):
		direction_dict = self.animations[self.current_animation]
		if hasatttr(self,"spiffy_buttons_exist") and self.spiffy_buttons_exist:     #this will also indicate if the direction buttons exist
			facing = self.facing_var.get().lower() if hasattr(self,"facing_var") else ""	#grabbed from the direction buttons, which are named "facing"
			aiming = self.aiming_var.get().lower() if hasattr(self,"aiming_var") else ""	#grabbed from the aiming buttons, which are named "aiming"

			#now start searching for this facing and aiming in the JSON dict
			#start going down the list of alternative aiming if a pose does not have the original
			ALTERNATIVES = {
				"up": "diag_up",
				"diag_up": "shoot",
				"shoot": "neutral",
				"down": "diag_down",
				"diag_down": "shoot"
			}
			while(self.concatenate_facing_and_aiming(facing,aiming) not in direction_dict):
				if aiming in ALTERNATIVES:
					aiming = ALTERNATIVES[aiming]
				else:
					return super().get_current_pose_list()  #don't worry about aiming

			return direction_dict[self.concatenate_facing_and_aiming(facing,aiming)]

		#do whatever the parent would do
		return super().get_current_pose_list()

	def concatenate_facing_and_aiming(self, facing, aiming):
		return "_aim_".join([facing,aiming])

	def get_palette(self, palettes, default_range, frame_number):
		#TODO: get dynamic palettes working again
		self.frame_getter = lambda: 0   #TODO: this is temporary to get the code to compile
		#get the actual list of associated palettes
		palette_timing_list = self.get_timed_palette_converter(palettes)
		#figure out the timing
		palette_timing_progression = list(itertools.accumulate([duration for (duration,_) in palette_timing_list]))

		#if the last palette has "zero" duration, indicating to freeze on that palette, and we are past that point
		if palette_timing_list[-1][0] == 0 and frame_number >= palette_timing_progression[-1]:
			palette_number = -1    #use the last palette
		else:
			mod_frames = self.frame_getter() % palette_timing_progression[-1]
			palette_number = palette_timing_progression.index(min([x for x in palette_timing_progression if x >= mod_frames]))

		#now actually get that specific palette
		_,palette = palette_timing_list[palette_number]

		return palette

	def get_timed_palette_converter(self, palette_list):
		#used to interface the new palette string format with the older get_timed_palette function.
		# could be refactored into the main code later, if coding time was not a valuable resource

		overall_type, variant_type = "power", "standard"   #defaults unless we are told otherwise
		for palette_string in palette_list:
			if palette_string.endswith("_suit"):
				overall_type = palette_string.replace("_suit","")
			if palette_string.endswith("_variant"):
				variant_type = palette_string.replace("_variant","")
		
		return self.get_timed_palette(overall_type=overall_type, variant_type=variant_type)
