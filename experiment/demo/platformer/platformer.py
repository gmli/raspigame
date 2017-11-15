#!/usr/bin/python
import sys
import os
sys.path.insert(1,os.path.join(sys.path[0], '../..'))
import raspigame
import pygame # for music, and perhaps for event handling (keyboard, gamepad)
import pi3d
import time


game = raspigame.World(background=(0,0,0,0), width=1280, height=800, frames_per_second=60)
game.DISPLAY.set_background(0,0,0,1)
#~ game.set_style('platformer')

spritesheet = raspigame.Spritesheet('textures/sheet.json', 'textures/sheet.png')
first_map = raspigame.Map('maps/test.tmx', spritesheet)


background_layer = raspigame.Layer(spritesheet=spritesheet, depth=10, has_movable=False)
foreground_layer = raspigame.Layer(spritesheet=spritesheet, depth=0, has_movable=False)
objects_layer = raspigame.Layer(spritesheet=spritesheet, depth=5, has_movable=False)

game.add_layer(background_layer) # background sprites, farest depth
game.add_layer(foreground_layer) # foreground sprites, nearest depth
game.add_layer(objects_layer)    # objects (player) sprites, medium depth


#~ player = raspigame.Player('player1', style="platformer")
#~ objects_layer.add_object(player)
player = raspigame.Character('64.png', 100, 100, 64, 64, False)
player.style = 'asteroid2'
objects_layer.add_object(player)


for tile in first_map.layers['background']:
    t = raspigame.Platform(tile.name,tile.x*32-640,-tile.y*32+400,32,32,False)
    foreground_layer.add_object(t)

collisions = []
print('Tiles : {}').format(len(first_map.tiles))
#~ print(first_map.layers)
for tile in first_map.layers['foreground']:
    t = raspigame.Platform(tile.name,tile.x*32-640,-tile.y*32+400,32,32,False)
    #~ print('{} {} {}').format(tile.name,tile.x,tile.y)
    background_layer.add_object(t)
    collisions.append(t)


player.collisions = collisions

objects_layer.init_buffer()
objects_layer.re_init_buffer()

background_layer.init_buffer()
background_layer.re_init_buffer()

# See if we could change that with a function in the main code.
#~ background_layer.add_objects_from_map_layer(first_map.layer('background'))
#~ foreground_layer.add_objects_from_map_layer(first_map.layer('foreground'))


inputs = pi3d.InputEvents()

#~ sprite = pi3d.ImageSprite("textures/sheet.png", game.main_shader, w=100.0, h=100.0, z=5.0)

######################################### TESTS ########################################
HWIDTH, HHEIGHT = 1280 / 2.0, 800 / 2.0

QWIDTH = HWIDTH/2 # quarter width

CAMERA = game.camera

font_colour = (255, 255, 255, 255)

class EgClass(object):
  valA = 0.0
  fps = 0.0
  ms = 0.0
  name = "Asteroid demo"
  angle = 0.0

eg_object = EgClass() # create an instance of the example class


text_pos = QWIDTH
working_directory = os.path.dirname(os.path.realpath(__file__))
font_path = os.path.abspath(os.path.join(working_directory, 'fonts', 'NotoSans-Regular.ttf'))
pointFont = pi3d.Font(font_path, font_colour, codepoints=list(range(32,128)))
text = pi3d.PointText(pointFont, CAMERA, max_chars=200, point_size=64)

newtxt = pi3d.TextBlock(510, 380, 0.1, 0.0, 10, data_obj=eg_object, attr="fps",
          text_format="fps:{:4.1f}", size=0.35, spacing="C", space=0.6,
          colour=(0.0, 1.0, 1.0, 1.0))
text.add_text_block(newtxt)
newtxt = pi3d.TextBlock(510, 360, 0.1, 0.0, 10, data_obj=eg_object, attr="ms",
          text_format=" ms:{:4.2f}", size=0.35, spacing="C", space=0.6,
          colour=(0.0, 1.0, 1.0, 1.0))
text.add_text_block(newtxt)

newtxt = pi3d.TextBlock(-635, 380, 0.1, 0.0, 25, data_obj=eg_object, attr="name",
          text_format="{:s}", size=0.25, spacing="F", space=0.08,
          colour=(1.0, 1.0, 1.0, 0.5))
text.add_text_block(newtxt)

frame_count = 0
end_time = time.time() + 1.0
########################################################################################
while game.DISPLAY.loop_running() and not inputs.key_state("KEY_ESC"):
    t1 = time.time()
    inputs.do_input_events()
    if inputs.key_state("KEY_UP"): 
        UP = True
    else:
        UP = False
    if inputs.key_state("KEY_DOWN"): 
        DOWN = True
    else:
        DOWN = False
    if inputs.key_state("KEY_LEFT"): 
        LEFT = True
    else:
        LEFT = False
    if inputs.key_state("KEY_RIGHT"): 
        RIGHT = True
    else:
        RIGHT = False

    

    player.inputs(UP, DOWN, LEFT, RIGHT)

    game.run()
    #~ game.DISPLAY.set_background(95, 205, 228, 255)
    #~ sprite.draw()
    #~ background_layer.re_init_buffer()


    ######################################### TESTS ########################################
    t2 = time.time()
    ms = t2 - t1
    now = time.time()
    frame_count += 1
    if now > end_time:
        end_time = now + 1.0
        eg_object.fps = frame_count
        eg_object.ms = 1000*ms
        frame_count = 0

    text.regen()
    text.draw()
    ########################################################################################

    if inputs.key_state("KEY_F1"):
        pi3d.util.Screenshot.screenshot('screenshot.png')


# while game.DISPLAY.loop_running():

    # for e in pygame.event.get():

    #     if e.type == KEYDOWN and e.key == K_ESCAPE:
    #         DISPLAY.destroy()



    # game.run()
