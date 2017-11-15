
#!/usr/bin/python
import pi3d
import pygame
from pygame import *
import numpy as np
import time

if pi3d.PLATFORM == pi3d.PLATFORM_PI:
  import os
  os.environ['SDL_VIDEODRIVER'] = 'dummy'
  import pygame
  pygame.init()
  pygame.display.set_mode((1,1))

DISPLAY = pi3d.Display.create(background=(1.0, 1.0, 1.0, 1.0),
                              w=800, h=480,
                                frames_per_second=60, tk=False, use_pygame=True)#, samples=4)

DISPLAY.set_background(255,0,0,255)
shader = pi3d.Shader("uv_light")
CAMERA = pi3d.Camera(is_3d=False)

sprite = pi3d.ImageSprite("textures/sheet.png", shader, w=100.0, h=100.0, z=5.0)

while DISPLAY.loop_running():
  
  for e in pygame.event.get():
    # if e.type == QUIT: raise SystemExit, "QUIT"
    if e.type == KEYDOWN and e.key == K_ESCAPE:
      DISPLAY.destroy()
      # raise SystemExit, "QUIT"


  
  #~ sprite.draw()
