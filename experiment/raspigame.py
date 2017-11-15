
import pi3d
import pytmx
import json
from collections import OrderedDict
import numpy as np
from raspigame_particle_dev import PexParticles
from raspigame_particle_lite import *
import threading
import math
import time

def addVectors((angle1, length1), (angle2, length2)):
    x = math.sin(angle1) * length1 + math.sin(angle2) * length2
    y = math.cos(angle1) * length1 + math.cos(angle2) * length2

    angle = 0.5 * math.pi - math.atan2(y, x)
    length = math.hypot(x, y)

    return (angle, length)

def rotatePolygon(polygon, theta, sprite_size):
    theta %= 360
    theta = math.radians(theta)

    # calculate the centre of the polygon (assume it's a rectangle, for now).
    ox = polygon[0][0] + (sprite_size[0] / 2)#((polygon[0][1] - polygon[0][0]) / 2)
    oy = polygon[0][1] - (sprite_size[1] / 2)#((polygon[2][1] - polygon[2][0]) / 2)
    #~ ox = polygon[0][0]
    #~ oy = polygon[0][1]
    #~ ox = 116
    #~ oy = 84
    #~ 
    rotatedPolygon = []
    for corner in polygon:
        #~ rotatedPolygon.append((corner[0]*math.cos(theta)-corner[1]*math.sin(theta),
                               #~ corner[0]*math.sin(theta)+corner[1]*math.cos(theta),
                               #~ 0.0)) # z
        rotatedPolygon.append((ox + math.cos(theta) * (corner[0] - ox) - math.sin(theta) * (corner[1] - oy),
                               oy + math.sin(theta) * (corner[0] - ox) + math.cos(theta) * (corner[1] - oy),
                               0.0)) # z
    return rotatedPolygon

def translatePolygon(polygon, x, y):
    translatedPolygon = []
    for corner in polygon:
        translatedPolygon.append((corner[0]+x,
                                  corner[1]+y,
                                  corner[2]))
    return translatedPolygon



        

class World:
    """
    Main class. Updating it must update everything else.

    """
    def __init__(self,background=(1.0, 1.0, 1.0, 1.0), width=1280, height=800, frames_per_second=60, use_pygame=True):

        self.DISPLAY = pi3d.Display.create(background=background,
            w=width, h=height,
            frames_per_second=frames_per_second, tk=False, use_pygame=use_pygame)
        #~ self.DISPLAY.set_background(95, 205, 228, 255)
        
        self.background = background
        self.width = width
        self.height = height
        self.frames_per_second = frames_per_second
        self.use_pygame = use_pygame


        self.world_style = None # Platformer, RPG, etc. Maybe useful.

        self.layers = [] # raspigame.Layer object.

        self.main_shader = pi3d.Shader("uv_light")
        self.camera = pi3d.Camera(is_3d=False,scale=1)

        # the default light
        self.default_light = pi3d.Light()
        self.default_light.position((0, 0, -50))


    def add_layer(self, layer):
        layer._world_added(self)
        self.layers.append(layer)
        

    def run(self):
        for layer in self.layers:
            layer.update()

        player = self.layers[2].objects[0]
        self.layers[0].shape.translate(-player.x,-player.y,0)
        self.layers[0].offset_x += -player.x
        self.layers[0].offset_y += -player.y
        player.move(0,0,True)

#~ background_layer = raspigame.Layer(spritesheet=spritesheet, map_layer=first_map.layer('background'), depth=10)

class Layer:
    """
    Is a buffer containing objects (characters, movables, lands).
    Each layer has a depth, defining the moment where all elements from the
    layer will be rendered.

    For instance, you can have a layer for the background, one (or more) for
    the player(s), one for the enemies, and one for the foreground.

    """
    def __init__(self, spritesheet=None, depth=0, has_movable=False):

        self.world = None # the world is added when we do World.add_layer()
        self.map_layer = None
        self.spritesheet = spritesheet
        self.depth = depth
        self.objects = []
        self.has_movable = has_movable

        self.dirty = False # need to be re_init

        self.offset_x = 0
        self.offset_y = 0

        # pi3d buffer things
        self.verts = []
        self.texcoords = []
        self.inds = []
        self.norms = []
        self.sprites = []
        self.a = 3
        self.b = 0
        self.c = 1
        self.d = 2

        self.shader = pi3d.Shader("uv_light")
        self.camera = pi3d.Camera(is_3d=False,scale=1)
        # the default light
        self.default_light = pi3d.Light()
        self.default_light.position((0, 0, -50))
        #######

        self.shape = pi3d.Shape(self.camera, None, "points", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                1.0, 1.0, 1.0, 0.0, 0.0, 0.0) # this is the "buffer". The name may not be the best (for futur), but it is clear.

        self.shape.buf = [pi3d.Buffer(self.shape, self.verts, self.texcoords, self.inds, self.norms)]
        #~ self.shape.set_draw_details(self.shader, [self.spritesheet.img])



        if self.map_layer: # if we have a map_layer (raspigame.Map.layer), convert it to sprites.
            self.convert_map_to_layer(self.map_layer)

    def _world_added(self, world): # trigged by World.add_layer()
        self.world = world
        self.shape.set_light(self.default_light)
        #~ self.shape.set_draw_details(self.shader, [self.spritesheet.img])

    def set_light(self, light): # pi3d.Light() object
        self.shape.set_light(light)

    def update(self):
        if self.has_movable:
            for obj in self.objects:
                obj.update()

        if self.dirty:
            self.shape.buf[0].re_init(pts=np.array(self.verts, 'f'),texcoords=np.array(self.texcoords, 'f'))
        #~ print(self.verts)
        #~ print(self.texcoords)
        #~ print(self.inds)
        #~ print('DRAW !')
        self.shape.draw()

    def add_object(self, obj): # DEFINE OBJ!
        """
        When we add an object, we must book in his place in the OpenGL buffer
        of the shape, and add his sprite the verts/texcoords of this shape.
        """
        obj.spritesheet_width  = self.spritesheet.size['width']
        obj.spritesheet_height = self.spritesheet.size['height']
        
        obj._layer_added(self)
        

        obj.buffer_index = len(self.objects)
        self.objects.append(obj)

        x = obj.x
        y = obj.y
        
        self.verts.extend(((x, y, 0.0), (x+obj.width, y, 0.0), (x+obj.width, y-obj.height, 0.0), (x, y-obj.height, 0.0)))
        self.texcoords.extend(obj.uv_texture)
        self.norms.extend(((0, 0, -1), (0, 0, -1),  (0, 0, -1), (0, 0, -1)))

        if pi3d.PLATFORM == pi3d.PLATFORM_PI:
            self.inds.append((self.a,self.b,self.c))
            self.inds.append((self.d,self.a,self.c))
        else:
            self.inds.extend((self.a,self.b,self.c))
            self.inds.extend((self.d,self.a,self.c))

        self.a += 4
        self.b += 4
        self.c += 4
        self.d += 4

        
        #~ return len(self.sprites)-1
        

    def add_objects_from_map_layer(self, map_layer):
        pass

    def init_buffer(self):
        """
        First initialisation of the buffer.
        """
        
        self.shape.buf = [pi3d.Buffer(self.shape, self.verts, self.texcoords, self.inds, self.norms)]
        self.shape.set_draw_details(self.shader, [self.spritesheet.img])

    def re_init_buffer(self):
        """
        Manually re_init the buffer.
        """
        #~ print(self.verts)
        #~ print(self.texcoords)
        #~ print(self.inds)
        self.shape.buf[0].re_init(pts=np.array(self.verts, 'f'),texcoords=np.array(self.texcoords, 'f'))





    


class Sprite:
    """
    A sprite reprensents a box on screen with a texture or a group of textures.
    It has a place ("booked") for it in the OpenGL buffer.
    You can change the texture at will, for instance to make an animation.
    A character and a platform have a sprite in them.
    """
    def __init__(self, name, x, y, width, height, rotated=False):

        self.name = name

        self.x = float(x)
        self.y = float(y)
        self.uv_x = self.x
        self.uv_y = self.y
        self.width = float(width)
        self.height = float(height)
        self.rotated = rotated
        self.buffer_index = None
        self.spritesheet_width = 0
        self.spritesheet_height = 0

        self.layer = None
        

        

        # print width , spritesheet_width, ' - ', height , spritesheet_height
        # print uv_width, uv_height
        #~ print x , y

    def _layer_added(self, layer):
        # spritesheet sizes are now setted by the Layer.add_object().
        # calculating uv texture...
        self.layer = layer
        self.uv_x = self.layer.spritesheet.json['frames'][self.name]['frame']['x'] #float(x)
        self.uv_y = self.layer.spritesheet.json['frames'][self.name]['frame']['y'] #1float(y)
        
        spritesheet_width = float(self.spritesheet_width)
        spritesheet_height = float(self.spritesheet_height)
        x = float(self.x)
        y = float(self.y)

        uv_width  = float(self.width) / float(spritesheet_width)
        uv_height = float(self.height) / float(spritesheet_height)

        #~ uv_x = x / uv_width
        #~ uv_y = y / uv_height
        # self.topleft = (spritesheet_width / uv_x if uv_x != 0 else 0, spritesheet_height / uv_y if uv_y != 0 else 0)
        self.topleft = (1 / (spritesheet_width / self.uv_x) if self.uv_x != 0 else 0, 1 / (spritesheet_height / self.uv_y) if self.uv_y != 0 else 0)
        self.topright = (self.topleft[0] + uv_width, self.topleft[1])
        self.bottomright = (self.topright[0],self.topleft[1] + uv_height)
        self.bottomleft = (self.topleft[0], self.bottomright[1])

        self.uv_texture = (self.topleft,self.topright,self.bottomright,self.bottomleft)
        #~ print('uv: ' + str(self.uv_texture))
        #~ print("---\n")

    def book_in_buffer(self, pbuffer): # Pi3d buffer
        pass

    def move(self, dx, dy, move_to=False):
        # uv_texture = self.sprites[self.current_frame].uv_texture
        # buffer.texcoords[self.buffer_index*4:self.buffer_index*4+4] = uv_texture

        if move_to == False:
            x = self.x + dx
            y = self.y + dy
        else:
            x = dx
            y = dy
            
        self.x = x
        self.y = y
        verts = ((x, y, 0.0), (x+self.width, y, 0.0), (x+self.width, y-self.height, 0.0), (x, y-self.height, 0.0))

        self.layer.verts[self.buffer_index*4:self.buffer_index*4+4] = verts

    def rotate(self, angle):
        #~ print('=========')
        verts = self.layer.verts[self.buffer_index*4:self.buffer_index*4+4]
        #~ print(verts)
        #~ print('----')
        #verts = translatePolygon(rotatePolygon(verts, angle),self.delta_x,self.delta_y)
        verts = [[self.x,self.y],
                 [self.x+self.width,self.y],
                 [self.x+self.width,self.y-self.height],
                 [self.x,self.y-self.height]]
        verts = rotatePolygon(verts, angle, (self.width,self.height))
        #~ print(verts)
        self.layer.verts[self.buffer_index*4:self.buffer_index*4+4] = verts
        #~ print('=========')

    #~ def copy(self):
        #~ sprite = Sprite(self.name ,self.uv_x ,self.uv_y, self.width, self.height, self.spritesheet_width,  self.spritesheet_height, self.rotated)
        #~ return sprite
#~ 
#~ 
    #~ def move(self, dx, dy, buffer, move_to=False):
        #~ # uv_texture = self.sprites[self.current_frame].uv_texture
        #~ # buffer.texcoords[self.buffer_index*4:self.buffer_index*4+4] = uv_texture
#~ 
        #~ if move_to == False:
            #~ x = self.x + dx
            #~ y = self.y + dy
        #~ else:
            #~ x = dx
            #~ y = dy
        #~ self.x = x
        #~ self.y = y
        #~ verts = ((x, y, 0.0), (x+self.width, y, 0.0), (x+self.width, y-self.height, 0.0), (x, y-self.height, 0.0))
#~ 
        #~ buffer.verts[self.buffer_index*4:self.buffer_index*4+4] = verts

class Character(Sprite):
    """
    Object representing a player or an opponent. The collision detection
    happens here.
    """
    def __init__(self, name, x, y, width, height, rotated=False):
        Sprite.__init__(self, name, x, y, width, height, rotated=False)

        self.xvel = 0
        self.yvel = 0
        self.xacceleration = 1.005
        self.yacceleration = 1.005
        self.max_xvel = 15
        self.max_yvel = 15

        self.last_x = self.x
        self.last_y = self.y

        self.pex_trail = None#pi3d.PexParticles('particles/sun.pex', camera=self.layer.camera, emission_rate=40)

        self.style = 'platformer'


        # style asteroid
        self.style = 'asteroid'
        self.angle = 0
        self.accel_angle = 0
        self.last_angle = self.angle
        self.acceleration = 0.10
        self.max_xvel = 4
        self.max_yvel = 4
        self.speed = 0
        #~ self.max_speed = 5
        self.delta_x = 0
        self.delta_y = 0


         # style asteroid2
        self.style = 'asteroid2'
        self.angle = 0
        self.move_angle = math.radians(0)
        self.last_angle = self.angle
        self.acceleration = 0.10
        self.max_xvel = 4
        self.max_yvel = 4
        self.speed = 0
        self.max_speed = 10
        #~ self.max_speed = 5
        self.delta_x = 0
        self.delta_y = 0

        self.n = 0

        
    def update(self):
        print('toto')


    def inputs(self, up, down, left, right):
        if self.pex_trail == None:
            #~ self.pex_trail = PexParticles('particles/sun.pex', camera=self.layer.camera, emission_rate=0)
            self.pex_trail = PexParticlesLite('particles/sun.pex', camera=self.layer.camera, emission_rate=0)
            
          
            #~ self.t = threading.Thread(target=self.pex_trail.update) # run in infinite loop
            #~ self.t.daemon = True
            #~ self.t.start()

        


        if self.style == 'platformer':

            move_x = 0
            move_y = 0

            if up and not down:
                move_y = 1
            if down and not up:
                move_y = -1
            if not up and not down:
                move_y = 0

            if left and not right:
                move_x = -1
            if right and not left:
                move_x = 1
            if not left and not right:
                move_x = 0

            # x movement
            self.xvel += move_x * self.xacceleration
            if move_x > 0:
                self.xvel = min(move_x * self.max_xvel, self.xvel)
            elif move_x < 0:
                self.xvel = max(move_x * self.max_xvel, self.xvel)
            elif move_x == 0:
                self.xvel = 0

            # y movement
            self.yvel += move_y * self.yacceleration
            if move_y > 0:
                self.yvel = min(move_y * self.max_yvel, self.yvel)
            elif move_y < 0:
                self.yvel = max(move_y * self.max_yvel, self.yvel)
            elif move_y == 0:
                self.yvel = 0
            
            self.last_x = self.x
            self.last_y = self.y
            self.x += self.xvel
            self.y += self.yvel
        
     
            self.collide()
            self.move(int(self.x), int(self.y), move_to=True)
            self.layer.dirty = True

         

       
        if self.style == 'asteroid':

            self.last_angle = self.angle

            if left:
                self.angle += 5
                self.angle %= 360
            if right:
                self.angle -= 5
                self.angle %= 360

            if up:
                #~ if self.speed < self.max_speed:
                #~ if self.xvel < self.max_xvel:
                    #~ self.speed += 0.09
                self.xvel += math.cos(math.radians(self.angle)) * self.acceleration
                if self.xvel > 0:
                    self.xvel = min(self.max_xvel,self.xvel)
                else:
                    self.xvel = max(-self.max_xvel,self.xvel)
                #~ if self.yvel < self.max_yvel:
                self.yvel += math.sin(math.radians(self.angle)) * self.acceleration
                if self.yvel > 0:
                    self.yvel = min(self.max_yvel,self.yvel)
                else:
                    self.yvel = max(-self.max_yvel,self.yvel)
            else:
                if self.xvel > 0:
                    self.xvel -= 0.005
                    self.xvel = max(self.xvel,0)
                if self.yvel > 0:
                    self.yvel -= 0.005
                    self.yvel = max(self.yvel,0)


            self.x += self.xvel #self.speed * math.cos(math.radians(self.angle))
            self.y += self.yvel #self.speed * math.sin(math.radians(self.angle))

            self.collide()

            # manage delta_x delta_y
            
            self.rotate(self.angle)# - self.last_angle)
            self.layer.dirty = True


               #~ if up:
                #~ (self.accel_angle, self.speed) = addVectors((math.radians(self.accel_angle), self.speed),
                                                        #~ (math.radians(self.angle), 0.05))
                #~ self.xvel += math.cos(math.radians(self.accel_angle)) * self.speed
                #~ self.yvel += math.sin(math.radians(self.accel_angle)) * self.speed
            #~ else:
                #~ self.xvel -= 0.005
                #~ self.yvel -= 0.005
#~ 

            #~ self.x += math.sin(math.radians(self.angle)) * self.speed
            #~ self.y -= math.cos(math.radians(self.angle)) * self.speed

        if self.style == 'asteroid2':

            self.last_angle = self.angle

            if left:
                self.angle -= 5
                self.angle %= 360
            if right:
                self.angle += 5
                self.angle %= 360

            if up:
                (self.move_angle, self.speed) = addVectors((self.move_angle, self.speed),
                                                        (math.radians(self.angle), self.acceleration))
                #~ self.pex_trail.sourcePosition['x'] = self.x + (self.width / 2)
                #~ self.pex_trail.sourcePosition['y'] = self.y - (self.height / 2)
                self.pex_trail.sourcePosition['x'] = (self.x + (self.width / 2) ) + 30 * math.cos(math.radians(180 - self.angle))
                self.pex_trail.sourcePosition['y'] = (self.y - (self.height / 2) ) + 30 * math.sin(math.radians(180 - self.angle ))
                #~ angle = self.angle - 180
                #~ angle %= 360
                self.pex_trail.gravity['x'] = 300 * math.cos(math.radians(180 - self.angle))
                self.pex_trail.gravity['y'] = 300 * math.sin(math.radians(180 - self.angle))
                self.pex_trail.angle = 180 - self.angle
        
                self.pex_trail._emission_rate = 10#120#40

            else:
                self.pex_trail._emission_rate = 0
                if self.speed > 0:
                    self.speed -= 0.01

            #~ print(math.degrees(self.move_angle))


            #~ self.pex_trail.draw()
            self.n += 1
            if self.n % 2 == 0:
                pass
                #~ self.pex_trail.update()
            
            self.speed = min(self.speed, self.max_speed)

            

            self.x += self.speed * math.cos(self.move_angle)
            self.y -= self.speed * math.sin(self.move_angle)
            self.collide_point()
            
            #~ print(self.collisions)        
            self.rotate(360-self.angle)
            self.layer.dirty = True


    def collide_point(self):
        elasticity = 0.5
        for collision in self.collisions:
            
            dx = self.x - (collision.x + self.layer.world.layers[0].offset_x - (collision.size))
            dy = self.y - (collision.y + self.layer.world.layers[0].offset_y + (collision.size))

            #~ print(self.layer.offset_x)

            distance = math.hypot(dy, dx)
            if not collision.collided and distance < self.width / 2 + collision.size / 2:
                #~ raise Exception
                print('collision ' + str(time.time()))
                print('distance ' + str(distance))
                tangent = math.atan2(dx, dy)
                angle   = 0.5 * math.pi + tangent

                angle1 = math.degrees(2*tangent - self.move_angle)
                angle1 %= 360
                angle1 = math.radians(angle1)
                #~ angle2 = 2*tangent - collision.angle
                speed1 = self.speed*elasticity
                speed2 = self.speed*elasticity

                previous_angle = self.move_angle
                print('previous ' + str(math.degrees(tangent)))

                (self.move_angle, self.speed) = (angle1, speed1)

                delta = max(2, (self.width / 2 + collision.size / 2) - int(distance))
                print('previous ' + str(math.degrees(previous_angle)) + ' new ' + str(math.degrees(self.move_angle)))

                prev = math.degrees(previous_angle)
                prev += 180
                prev %= 360
                prev = math.radians(prev)
                #~ self.x += int(math.cos(prev) * delta)
                #~ self.y += int(math.sin(prev) * delta)
                
                #~ self.x += int(math.cos(self.move_angle) * delta)
                #~ self.y += int(math.sin(self.move_angle) * delta)
                collision.collided = True
                #~ self.x = 16 - dx
            if collision.collided and distance > self.width / 2 + collision.size / 2:
                collision.collided = False

                               

    def collide(self):
        '''
        Box collide. The character is limited to the visible screen.
        '''
        if not self.style == 'asteroid':
            halfwidth = self.layer.world.width / 2
            halfheight = self.layer.world.height / 2

            if self.x > halfwidth - self.width:
                self.x = halfwidth - self.width

            if self.x < -halfwidth:
                self.x = -halfwidth

            if self.y > halfheight:
                self.y = halfheight
    #~ 
            if self.y < -(halfheight - self.height):
                self.y = -(halfheight - self.height)

        if self.style == 'asteroid':
            halfwidth = self.layer.world.width / 2
            halfheight = self.layer.world.height / 2

            if self.x > halfwidth - self.width:
                self.x = halfwidth - self.width
                self.xvel = -self.xvel

            if self.x < -halfwidth:
                self.x = -halfwidth
                self.xvel = -self.xvel

            if self.y > halfheight:
                self.y = halfheight
                self.yvel = -self.yvel
    #~ 
            if self.y < -(halfheight - self.height):
                self.y = -(halfheight - self.height)
                self.yvel = -self.yvel

        if self.style == 'asteroid2':
            halfwidth = self.layer.world.width / 2
            halfheight = self.layer.world.height / 2

            if self.x > halfwidth - self.width:
                self.x = halfwidth - self.width
                self.xvel = -self.xvel

            if self.x < -halfwidth:
                self.x = -halfwidth
                self.xvel = -self.xvel

            if self.y > halfheight:
                self.y = halfheight
                self.yvel = -self.yvel
    #~ 
            if self.y < -(halfheight - self.height):
                self.y = -(halfheight - self.height)
                self.yvel = -self.yvel

class Platform(Sprite):
    """
    A platfrom is an element of the landscape, may be called a "sprite",
    but sprite has a different meaning in raspigame.
    A platfrom can also move if necessary.
    """
    def __init__(self, name, x, y, width, height, rotated=False):
        Sprite.__init__(self, name, x, y, width, height, rotated=False)

        self.xvel = 0 # x velocity
        self.yvel = 0

        self.angle = 0
        self.speed = 0
        self.size = 16

        # test
        self.collided = False


class Spritesheet:
    """
    An helper class, representing a spritesheet. It can read a spritesheet
    png/jpg and the attached json to provide you with textures.
    """
    def __init__(self, path, image_path):
        self.path = path
        self.image_path = image_path
        self.json = None
        self.sprites = {}
        self.animatedsprites = {}
        self.size = {}
        # TODO: modify path !
        self.img = pi3d.Texture(self.image_path, mipmap=False, i_format=pi3d.GL_RGBA, filter=pi3d.GL_NEAREST)


        with open(self.path,"r") as file_content:
            self.json = json.load(file_content, object_pairs_hook=OrderedDict)
            self.size['width'] = self.json['meta']['size']['w']
            self.size['height'] = self.json['meta']['size']['h']

            #~ print self.json['frames']['16.png']

            for frame in self.json['frames']:
                pass
                #~ print(frame)
                # print frame

                #~ sprite = Sprite(frame,
                                #~ self.json['frames'][frame]['frame']['x'],
                                #~ self.json['frames'][frame]['frame']['y'],
                                #~ self.json['frames'][frame]['frame']['w'],
                                #~ self.json['frames'][frame]['frame']['h'],
                                #~ self.size['width'],
                                #~ self.size['height'],
                                #~ self.json['frames'][frame]['rotated']
                                #~ )
#~ 
                #~ if frame.startswith('anim '):
                    #~ sprite_name = frame.split(' ')[1]
                    #~ if not sprite_name in self.animatedsprites:
                        #~ asprite = AnimatedSprite()
                        #~ self.animatedsprites[sprite_name] = asprite
                    #~ self.animatedsprites[sprite_name].sprites.append(sprite)
#~ 
#~ 
                #~ else:
                    #~ self.sprites[frame] = sprite

class Map:
    """
    The description of a map. 
    """
    def __init__(self, path, spritesheet):
        self.path = path
        self.spritesheet = spritesheet # raspigame.Spritesheet()
        self.map = pytmx.TiledMap(self.path)
        self.layers = {}
        self.tiles = []

        for layer in self.map.layers:
            if not layer.name in self.layers:
                self.layers[layer.name] = []
            for x, y, image in layer.tiles():
                name = str(image[0]).split('/')[-1]
                tile = Tile(name, x, y)
                self.tiles.append(tile)
                self.layers[layer.name].append(tile)
                #~ sprite = spritesheet.sprites[name].copy()
                #~ sprite.x = x
                #~ sprite.y = y

class Tile:
    '''
    A description of a sprite/tile in a map.
    '''
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
