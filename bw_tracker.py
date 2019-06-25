import bpy
import json
import requests
import random
import time
import bmesh
import math
import numpy as np
import geometry_utils
import mathutils
import os
from threading import *


#os.chdir("C:\\Users\\user\\Desktop\\")
print (os.getcwd())

#from hci_control import *

def bl_dist(vect1, vect2):    
    return np.linalg.norm(np.array(vect1) - np.array(vect2))
    #math.sqrt((vect1[0] - vect2[0]) ** 2 + (vect1[1] - vect2[1]) ** 2 + (vect1[2] - vect2[2]) ** 2)
class ModalTimerOp(bpy.types.Operator):    
        #metatags for Blender internal machinery
        bl_idname = "wm.modal_timer_operator"
        bl_label = "Modal Timer Op"
        
        #internal timer
        _timer = None

        tracker = None
        
        #execution step (fires at every timer tick)
        def modal(self, context, event):
            if event.type == "ESC":
                return self.cancel(context)
            
            if event.type == "TIMER":            
                block_ids, block_locations = ModalTimerOp.tracker.get_block_data()
                print (block_ids)
                #print (len(block_dict.keys()))
                if len(block_dict.keys()) == 0:
                    self.flag = True
                ModalTimerOp.tracker.update_scene(block_ids, block_locations)
                if self.flag:
                    tracker.apply_material()
                    self.flag = False                            
            return {"PASS_THROUGH"}
        
        #Setup code (fires at the start)
        def execute(self, context):
            self._timer = context.window_manager.event_timer_add(1.0, context.window)
            context.window_manager.modal_handler_add(self)
            self.flag = False
            return {"RUNNING_MODAL"}
        
        #Timer termination and cleanup
        def cancel(self, context):
            context.window_manager.event_timer_remove(self._timer)
            return {"CANCELLED"}


class Tracker(object):
    
    def __init__(self):
        #Sizes of BW objects in meters
        self.block_edge = 0.155
        self.table_edge = 1.53

        self.kinectLeft = (-0.75, 0.27, 0.6)
        self.kinectRight = (0.75, 0.27, 0.6)

        bpy.utils.register_class(ModalTimerOp)
        ModalTimerOp.tracker = self
        self.scene_setup()
        
        bpy.ops.wm.modal_timer_operator()
        #Dictionary that stores block IDs
        self.block_dict = {}

    def apply_material(self):
        print ("TEST")
        blocks = list(self.block_dict.values())
        print (blocks)    
        blocks.sort(key = lambda x: x.location[0])
        mats = [bpy.data.materials['Red'],\
            bpy.data.materials['Green'],\
            bpy.data.materials['Blue']]
        for bl in blocks:
            bl.data.materials.append(mats[blocks.index(bl) % 3])    

    #Remove block from the scene and id dictionary
    def remove_block(self, block_id):
        #unselect all the objects
        for ob in bpy.data.objects:
            ob.select = False
        #select the object to be deleted
        bpy.data.objects[self.block_dict[block_id].name].select = True
        
        bpy.ops.object.delete()
        del self.block_dict[block_id]

    #Add block to the scene and id dictionary
    def add_block(self, block_id):
        #construct the block mesh and object and
        #add 
        block_mesh = bpy.data.meshes.new('Block_mesh')
        block = bpy.data.objects.new("Block", block_mesh)
        bpy.context.scene.objects.link(block)
        bpy.context.scene.objects.active = block
        block.select = True
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=block_edge)
        bm.to_mesh(block_mesh)
        bm.free()
        self.block_dict[block_id] = block
           
    #Reset the scene by removing all the meshes
    def clear_scene(self):
        #iterate over the objects in the scene
        for ob in bpy.data.objects:
            #If it's a mesh select it
            if ob.type == "MESH":
                ob.select = True
        #remove all selected objects
        bpy.ops.object.delete()

    #Adds objects to the scene    
    def scene_setup(self):        
        self.clear_scene()
        #Creating the materials
        bpy.data.materials.new(name="Red")
        bpy.data.materials.new(name="Blue")
        bpy.data.materials.new(name="Green")
        bpy.data.materials['Red'].diffuse_color = (1, 0, 0)
        bpy.data.materials['Green'].diffuse_color = (0, 1, 0)
        bpy.data.materials['Blue'].diffuse_color = (0, 0, 1)
        
        bpy.ops.mesh.primitive_plane_add(location=(0,0,0), radius=self.table_edge/2)

    def unoccluded(self, block):
        LeftBlocked = False
        RightBlocked = False
        for key in self.block_dict:
            if self.block_dict[key] != block:
                dist_left = get_distance_from_line(block.location, self.kinectLeft, self.block_dict[key].location)
                dist_right = get_distance_from_line(block.location, self.kinectRight, self.block_dict[key].location)
                if dist_left <= 0.05:
                    LeftBlocked = True
                if dist_right <= 0.05:
                    RightBlocked = True
        return LeftBlocked and RightBlocked
                
    def update_scene(self, block_ids, block_locations):
        remove_queue = []
        for key in block_ids:
            if key in self.block_dict:
                idx = block_ids.index(key)
                self.block_dict[key].location = block_locations[idx]
            else:
                min_dist = 10e9
                cand = None
                for key1 in block_dict:
                    if key1 not in block_ids:
                        print (block_locations[block_ids.index(key)], self.block_dict[key1].location)                    
                        cur_dist = bl_dist(block_locations[block_ids.index(key)], self.block_dict[key1].location)
                        if min_dist > cur_dist:
                            min_dist = cur_dist
                            cand = key1
                #print (cand, key)
                if cand != None:
                    self.block_dict[cand].location = block_locations[block_ids.index(key)]
                    self.block_dict[key] = block_dict[cand]
                    del self.block_dict[cand]
                else:
                    add_block(key)
                    self.block_dict[key].location = block_locations[block_ids.index(key)]
               
            
    def get_block_data(self):
        url = "http://127.0.0.1:1236/world-api/block-state.json"
        response = requests.get(url, data="")
        #print (response.text)
        json_data = json.loads(response.text)
        block_ids = []
        block_locations = []
        for segment in json_data['BlockStates']:
            #print (segment)
            block_ids += [segment['ID']]
            str_loc = segment['Position']
            print (segment['Position'])
            block_locations += [[float(x) for x in str_loc.split(",")]]

        #print (json_data['BlockStates'][0]['ID'])
        #print (json_data['BlockStates'][0]['Position'])
        #print (json_data['BlockStates'][1]['ID'])
        #print (json_data['BlockStates'][1]['Position'])
        #str_loc = json_data['BlockStates'][0]['Position']
        #loc = [float(x) for x in str_loc.split(",")]
        #print (block_ids)
        #print (block_locations)
        url = "http://127.0.0.1:1236/world-api/block-metadata.json"
        response = requests.get(url, data="")
        #print (response.text)
        json_data = json.loads(response.text)
        #print ("\n")
        #for bl in json_data["Blocks"]:
        #    print (bl)
        return (block_ids, block_locations)
     
#Timer operator



'''for i in range(0, 20):
    #Getting the blocks coordinates/orientations
    block_locations = [(random.uniform(-1, 1), random.uniform(-1, 1), block_edge/2)]
    #print(block_locations)
#    update_scene(block_locations)
    #updating the scene based on the real-time world state
    #scene_setup(block_locations)
    bpy.context.scene.update()
    time.sleep(.1)
'''
#print('Say "Quit" or "Exit" to terminate the program.')
#thread = Thread(target = mic_loop)
#thread.start()
#block_locations = [(random.uniform(-1, 1), random.uniform(-1, 1), block_edge/2)]


'''    for key in block_dict:
        if key in block_ids:
            idx = block_ids.index(key)
            block_dict[key].location = block_locations[idx]
        else:
            min_dist = 10e9
            cand = None
            for key1 in block_ids:
                if key1 not in block_dict:
                    cur_dist = numpy.linalg.norm(block_locations[block_ids.index(key1)], block_dict[key].location)
                    if min_dist > cur_dist:
                        min_dist = cur_dist
                        cand = key1
            print (cand, key)
            if cand != None:
                block_dict[key].location = block_locations[block_ids.index(cand)]
                block_dict[cand] = block_dict[key]
                del block_dict[key]
            
              
    for key in block_ids:
        if key not in block_dict:
            add_block(key)
            block_dict[key].location = block_locations[block_ids.index(key)]
    
    for key in block_dict:
        if key not in block_ids:
            remove_queue += [key]
    for key in remove_queue:
        remove_block(key)'''
  
'''    print (block_ids.index(block_ids[0]))
    for key in block_ids:
        if key in block_dict:
            idx = block_ids.index(key)
            block_dict[key].location = block_locations[idx]
    

  
    for idx in range(len(block_ids)):
        if block_ids[idx] not in block_dict:
            add_block(block_ids[idx])
        block_dict[block_ids[idx]].location = block_locations[idx]
    
   
    for block in block_data:
        loc = block_data[0] #ideally loc = block[0]
        #ID = block[1]
        for ob in bpy.data.objects:
            if ob.name == 'Cube': #have ID as name? ob.name==ID
                print(ob.name)
                ob.location = loc
    '''    
        #ob = bpy.data.objects[1]#how to identify with ID?
