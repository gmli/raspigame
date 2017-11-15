#!/usr/bin/python
import sys
import os
sys.path.insert(1,os.path.join(sys.path[0], '../..'))
import raspigame
import pygame # for music, and perhaps for event handling (keyboard, gamepad)
import pi3d

game = raspigame.World(background=(255,255,0,255), width=1280, height=800, frames_per_second=60)

spritesheet = raspigame.Spritesheet('textures/sheet.json')
background_layer = raspigame.Layer(spritesheet=spritesheet, depth=10, has_movable=False)
game.add_layer(background_layer) # background sprites, farest depth
test_obj = raspigame.Platform('32.png', 100, 100, 32, 32, False)
background_layer.add_object(test_obj)
background_layer.init_buffer()


inputs = pi3d.InputEvents()
while game.DISPLAY.loop_running() and not inputs.key_state("KEY_ESC"):
    inputs.do_input_events()
    game.run()
    
