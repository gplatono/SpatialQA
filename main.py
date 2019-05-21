import bpy
import bpy_types
import bpy_extras
import numpy as np
import math
from math import e, pi
import itertools
import os
import sys
import random
import bmesh
from functools import reduce
from mathutils import Vector
import importlib

#The path to the this source file
filepath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, filepath)

from entity import Entity
from geometry_utils import *
#from annot_parser import *
from spatial import *
from ulf_parser import *
from constraint_solver import *
#from query_proc import *

link = False
#The current scene
scene = bpy.context.scene

#List of  possible color modifiers
color_mods = ['black', 'red', 'blue', 'brown', 'green', 'yellow']

relations = ['on', 'to the left of', 'to the right of', 'in front of', 'behind', 'above', 'below', 'over', 'under', 'near', 'touching', 'at', 'between']

types_ids = {
    'chair':  'props.item.furniture.chair',
    'table':  'props.item.furniture.table',    
    'bed':     'props.item.furniture.bed',
    'sofa':  'props.item.furniture.sofa',
    'bookshelf':  'props.item.furniture.bookshelf',
    'desk':  'props.item.furniture.desk',
    'book': 'props.item.portable.book',
    'laptop': 'props.item.portable.laptop',
    'pencil': 'props.item.portable.pencil',
    'pencil holder': 'props.item.portable.pencil holder',
    'note': 'props.item.portable.note',
    'rose': 'props.item.portable.rose',
    'vase': 'props.item.portable.vase',
    'cardbox': 'props.item.portable.cardbox',
    'box': 'props.item.portable.box',
    'ceiling light': 'props.item.stationary.ceiling light',
    'lamp': 'props.item.portable.lamp',
    'apple': 'props.item.food.apple',
    'banana': 'props.item.food.banana',
    'plate': 'props.item.portable.plate',
    'bowl': 'props.item.portable.bowl',
    'trash bin': 'props.item.portable.trash can',
    'trash can': 'props.item.portable.trash can',
    'tv': 'props.item.appliances.tv',
    'poster': 'props.item.stationary.poster',
    'picture': 'props.item.stationary.picture',
    'fridge' : 'props.item.appliances.fridge',
    'ceiling fan': 'props.item.stationary.ceiling fan',
    'block': 'props.item.block',
    'floor': 'world.plane.floor',
    'ceiling': 'world.plane.ceiling',
    'wall': 'world.plane.wall'
}

#The list of entities
entities = []

#Average distance between entities in the scene
avg_dist = 0

#Computes the value of the univariate Gaussian
#Inputs: x - random variable value; mu - mean; sigma - variance
#Return value: real number
def gaussian(x, mu, sigma):
    return e ** (- 0.5 * ((float(x) - mu) / sigma) ** 2) / (math.fabs(sigma) * math.sqrt(2.0 * pi))

#Computes the value of the logistic sigmoid function
#Inputs: x - random variable value; a, b - coefficients
#Return value: real number
def sigmoid(x, a, b):
    return a / (1 + e ** (- b * x)) if b * x > -100 else 0



    
#The following functions are for precomputing the corresponding
#relation for every pair of entities
#
#

def compute_at(entities):
    obj = [[x, [y for y in entities if x != y and near(y, x) > 0.8]] for x in entities]
    return "\n".join(", ".join(y.name for y in x[1]) + " is at the " + x[0].name for x in obj if x[1] != [])

def compute_near(entities):
    obj = [[x, [y for y in entities if x != y and near(y, x) > 0.6]] for x in entities]
    return "\n".join(", ".join(y.name for y in x[1]) + " is near the " + x[0].name for x in obj if x[1] != [])

def compute_on(entities):
    obj = [[x, [y for y in entities if x != y and on(y, x) > 0.8]] for x in entities]
    return "\n".join(", ".join(y.name for y in x[1]) + " is on the " + x[0].name for x in obj if x[1] != [])

def compute_above(entities):
    obj = [[x, [y for y in entities if x != y and above(y, x) > 0.7]] for x in entities]
    return "\n".join(", ".join(y.name for y in x[1]) + " is above the " + x[0].name for x in obj if x[1] != [])

def compute_below(entities):
    obj = [[x, [y for y in entities if x != y and below(y, x) > 0.7]] for x in entities]
    return "\n".join(", ".join(y.name for y in x[1]) + " is below the " + x[0].name for x in obj if x[1] != [])

def compute_over(entities):
    obj = [[x, [y for y in entities if x != y and over(y, x) > 0.7]] for x in entities]
    return "\n".join(", ".join(y.name for y in x[1]) + " is over the " + x[0].name for x in obj if x[1] != [])

#

#Creates and configures the special "observer" object
#(which is just a camera). Needed for deictic relations as
#well as several other aspects requiring the POV concept,
#e.g., taking screenshots.
#Inputs: none
#Return value: the camera object
def get_observer():
    lamp = bpy.data.lamps.new("Lamp", type = 'POINT')
    lamp.energy = 30
    cam = bpy.data.cameras.new("Camera")

    if bpy.data.objects.get("Lamp") is not None:
        lamp_obj = bpy.data.objects["Lamp"]
    else:
        lamp_obj = bpy.data.objects.new("Lamp", lamp)
        scene.objects.link(lamp_obj)
    if bpy.data.objects.get("Camera") is not None:
        cam_ob = bpy.data.objects["Camera"]
    else:
        cam_ob = bpy.data.objects.new("Camera", cam)
        scene.objects.link(cam_ob)    

    lamp_obj.location = (-20, 0, 10)
    cam_ob.location = (-15.5, 0, 7)
    cam_ob.rotation_mode = 'XYZ'
    cam_ob.rotation_euler = (1.1, 0, -1.57)
    bpy.data.cameras['Camera'].lens = 20
    
    bpy.context.scene.camera = scene.objects["Camera"]


    if bpy.data.objects.get("Observer") is None:
        mesh = bpy.data.meshes.new("Observer")
        bm = bmesh.new()
        bm.verts.new(cam_ob.location)
        bm.to_mesh(mesh)
        observer = bpy.data.objects.new("Observer", mesh)    
        scene.objects.link(observer)
        bm.free()
        scene.update()
    else: 
        observer = bpy.data.objects["Observer"]            
    observer_entity = Entity(observer)
    observer_entity.camera = cam_ob
    return observer_entity

#Searches and returns the entity that has the given name
#associated with it
#Inputs: name - human-readable name as a string
#Return value: entity (if exists) or None
def get_entity_by_name(name):
    for entity in entities:
        #print("NAME:",name, entity.name)
        if entity.name.lower() == name.lower():
            return entity
    for col in color_mods:
        if col in name:
            name = name.replace(col + " ", "")
            #print ("MOD NAME:", name)
    for entity in entities:
        #print(name, entity.name)
        if entity.name.lower() == name.lower():
            return entity
    return None
'''
#Places the entity at a specified location and with specified orientation
#Inputs: entity, position - triple of point coordinates, rotation - triple of Euler angles
#Return value: none
def place_entity(entity, position=(0,0,0), rotation=(0,0,0)):
    obj = entity.constituents[0]
    obj.location = position
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler = rotation
    scene.update()

#Places the set of entities within a certain region 
#Inputs: reg - the bounding box of the region, collection - list of entities
#Return value: none
def arrange_entities(reg, collection):
    for entity in collection:
        if entity.get('fixed') is None:
            #print (entity.name)
            if reg[4] == reg[5]:
                pos = (random.uniform(reg[0], reg[1]), random.uniform(reg[2], reg[3]), reg[4])#entity.get_parent_offset()[2])
            else:
                pos = (random.uniform(reg[0], reg[1]), random.uniform(reg[2], reg[3]), random.uniform(reg[4], reg[5]))
            place_entity(entity, pos, (math.pi,0,0))
            while check_collisions(entity):
                print (entity.name, pos)
                if reg[4] == reg[5]:
                    pos = (random.uniform(reg[0], reg[1]), random.uniform(reg[2], reg[3]), reg[4])#entity.get_parent_offset()[2])
                else:
                    pos = (random.uniform(reg[0], reg[1]), random.uniform(reg[2], reg[3]), random.uniform(reg[4], reg[5]))
                place_entity(entity, pos, (math.pi,0,0))
'''


'''
#Checks if the projections of two entities onto a coordinate axis "collide" (overlap)
#Inputs: int_a, int_b - the projections of two entities as intervals (pairs of numbers)
#Return value: Boolean value                
def axis_collision(int_a, int_b):
    return int_a[1] <= int_b[1] and int_a[1] >= int_b[0] or \
int_a[0] >= int_b[0] and int_a[0] <= int_b[1] or \
int_b[0] >= int_a[0] and int_b[0] <= int_a[1] or \
int_b[1] >= int_a[0] and int_b[1] <= int_a[1]
'''

#Checks if the entity "collides" (overlaps) with some other entity along any coordinate axis
#Inputs: a - entity
#Return value: Boolean value                
def check_collisions_for_entity(a):
    for entity in entities:
        if entity != a and check_collision(a, entity):            
            return True
    return False            

#Checks if two entities "collide" (overlap) along some coordinate axis
#Inputs: a,b - entities
#Return value: Boolean value                
def check_collision(a, b):
    span_a = a.get_span()
    span_b = b.get_span()
    ax_1 = span_a[0][0]
    ax_2 = span_a[0][1]
    ay_1 = span_a[1][0]
    ay_2 = span_a[1][1]
    az_1 = span_a[2][0]
    az_2 = span_a[2][1]
    bx_1 = span_b[0][0]
    bx_2 = span_b[0][1]
    by_1 = span_b[1][0]
    by_2 = span_b[1][1]
    bz_1 = span_b[2][0]
    bz_2 = span_b[2][1]
    return (ax_1 <= bx_1 and bx_1 < ax_2 or bx_1 <= ax_1 and ax_1 < bx_2) or \
    (ay_1 <= by_1 and by_1 < ay_2 or by_1 <= ay_1 and ay_1 < by_2) or \
    (az_1 <= bz_1 and bz_1 < az_2 or bz_1 <= az_1 and az_1 < bz_2)
    #return axis_collision((span_a[0], span_a[1]), (span_b[0], span_b[1])) and \
    #                      axis_collision((span_a[2], span_a[3]), (span_b[2], span_b[3])) and \
    #                      axis_collision((span_a[4], span_a[5]), (span_b[4], span_b[5]))

#STUB
def put_on_top(a, b):
    pass


#Render and save the current scene screenshot
#Inputs: none
#Return value: none
def save_screenshot():
    add_props()
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.use_border = False
    scene.render.image_settings.file_format = 'JPEG'
    current_scene = bpy.data.filepath.split("/")[-1].split(".")[0]
    scene.render.filepath = filepath + current_scene + ".jpg"
    bpy.ops.render.render(write_still=True)

#Computes the projection of an entity onto the observer's visual plane
#Inputs: entity - entity, observer - object, representing observer's position
#and orientation
#Return value: list of pixel coordinates in the observer's plane if vision
def vp_project(entity, observer):
    points = reduce((lambda x,y: x + y), [[obj.matrix_world * v.co for v in obj.data.vertices] for obj in entity.constituents if (obj is not None and hasattr(obj.data, 'vertices') and hasattr(obj, 'matrix_world'))])   
    co_2d = [bpy_extras.object_utils.world_to_camera_view(scene, observer.camera, point) for point in points]
    render_scale = scene.render.resolution_percentage / 100
    render_size = (int(scene.render.resolution_x * render_scale), int(scene.render.resolution_y * render_scale),)
    pixel_coords = [(round(point.x * render_size[0]),round(point.y * render_size[1]),) for point in co_2d]
    return pixel_coords


def scaled_axial_distance(a_bbox, b_bbox):
    a_span = (a_bbox[1] - a_bbox[0], a_bbox[3] - a_bbox[2])
    b_span = (b_bbox[1] - b_bbox[0], b_bbox[3] - b_bbox[2])
    a_center = ((a_bbox[0] + a_bbox[1]) / 2, (a_bbox[2] + a_bbox[3]) / 2)
    b_center = ((b_bbox[0] + b_bbox[1]) / 2, (b_bbox[2] + b_bbox[3]) / 2)
    axis_dist = (a_center[0] - b_center[0], a_center[1] - b_center[1])
    return (2 * axis_dist[0] / max(a_span[0] + b_span[0], 2), 2 * axis_dist[1] / max(a_span[1] + b_span[1], 2))

def get_weighted_measure(a, b, observer):
    a_bbox = get_2d_bbox(vp_project(a, observer))
    b_bbox = get_2d_bbox(vp_project(b, observer))
    axial_dist = scaled_axial_distance(a_bbox, b_bbox)
    if axial_dist[0] <= 0:
        return 0
    horizontal_component = sigmoid(axial_dist[0], 1.0, 0.5) - 0.5
    vertical_component = gaussian(axial_dist[1], 0, 2.0)
    distance_factor = math.exp(-0.01 * axial_dist[0])
    return 0.5 * horizontal_component + 0.3 * vertical_component + 0.2 * distance_factor


def fix_ids():
    for ob in scene.objects:
        if ob.get('main') is not None:# and ob.get('id') is None:
            for key in types_ids.keys():
                if key in ob.name.lower():
                    ob['id'] = types_ids[key] + "." + ob.name
            if ob.get('color_mod') is None:
                for color in color_mods:
                    if color in ob.name.lower():
                        ob['color_mod'] = color
                        break

def get_similar_entities(relatum):
    ret_val = []
    relatum = get_entity_by_name(relatum, entities)
    for entity in entities:
        if relatum.type_structure[-2] == entity.type_structure[-2] and (relatum.color_mod is None \
           and entity.color_mod is None or relatum.color_mod == entity.color_mod):
            ret_val += [entity]
    return ret_val

def pick_descriptions(relatum):
    candidates = get_similar_entities(relatum)
    relatum = get_entity_by_name(relatum, entities)
    max_vals = []
    for relation in relations:
        max_val = 0
        if relation != 'between':            
            for ref in entities:
                if ref != relatum:
                    max_val = max([(globals()[rf_mapping[relation]](cand, ref), cand) for cand in candidates], key=lambda arg: arg[0])
        else:
            for pair in itertools.combinations(entities, r = 2):
                if relatum != pair[0] and relatum != pair[1]:
                    max_val = max([(globals()[rf_mapping[relation]](cand, pair[0], pair[1]), cand) for cand in candidates], key=lambda arg: arg[0])
        if max_val[1] == relatum:
            max_vals += [(relation, max_val[0])]
    max_vals.sort(key=lambda arg: arg[1])
    print ("MAX_VALS: {}".format(max_vals))
    max_vals = [item[0] for item in max_vals]
    return tuple(max_vals[0:3])

#The observer object (camera)
observer = get_observer()

def get_entities():
    print (entities)
    return entities

#Entry point
#Implementation of the evaluation pipeline
def main():
    global entities
    #print ("OBJECT TYPE: ", type(scene.objects[0]))
    for obj in scene.objects:
        if obj.get('main') is not None:
            entities.append(Entity(obj))
    global avg_dist
    if len(entities) != 0:
        for pair in itertools.combinations(entities, r = 2):
            avg_dist += dist_obj(pair[0], pair[1])
        avg_dist = avg_dist * 2 / (len(entities) * (len(entities) - 1))

    spatial.entities = entities

    #print (filepath, sys.path)
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        init_parser([entity.name for entity in entities])
        if len(args) != 6:
            result = "*RESULT: MALFORMED*"
        else:
            relation = args[0].lower()
            relatum = args[1].lower()
            referent1 = args[2].lower()
            referent2 = args[3].lower()
            task_type = args[4].lower()
            response = args[5].lower()
            print ("ANNOTATION PARAMS: {}, {}, {}, {}, {}, {}".format(task_type, relatum, relation, referent1, referent2, response))
        
            if task_type == "1":
                best_cand = process_descr(relatum, response, entities)
                if best_cand != None:
                    print(process_descr(relatum, response, entities).name, "==?", relatum)
                print("RESULT:", int(get_entity_by_name(relatum, entities) == best_cand))
            elif task_type == "0":
                print("RESULT:", process_truthjudg(relation, relatum, referent1, referent2, response, entities))
            elif task_type == "2":
                descr = pick_descriptions(relatum)
                print("RESULT: {}".format("#".join(descr)))
        return

    f = open("sqa_input.bw")
    #test = ["the.d", ["red.a", ["block.n", "or.cc", "stack.n"]]]
    #test2 = ["sub", ["what.d", "color.n"], [["pres", "be.v"], ["rep", [["farthest.a", "*p"], "block.n"], ["to.p", ["the.d", "right.n"]]], "*h"]]
    ulfs = f.readlines()



    #testt = [[['pres', 'be.v'], ['the.d', [['|nvidia|', 'and.cc', '|sri|'], ['plur', 'block.n']]], ['in.p', ['the.d', ['same.a', 'stack.n']]]], '?']
    #print (memberof("and.cc", testt))

    print (entities)
    for ulf in ulfs[50:]:
        #print (ulf)
        #if "and.cc" not in ulf:
        #    continue
        #if "sub" not in ulf and "rep" not in ulf:
        #    continue        
        print ("\n" + str(1 + ulfs.index(ulf)) + " out of " + str(len(ulfs)))
        ulf = ulf.lower().strip().replace("{", "").replace("}", "")
        if ";;" not in ulf and ulf != "":
            query = ULFQuery(ulf)
            print (query.query_tree)
            #print (process_query(query.query_tree, entities))
            input("Press Enter to continue...")

    #bl4 = get_entity_by_name("Block 4")
    #bl9 = get_entity_by_name("Block 9")
    #bl11 = get_entity_by_name("Block 11")
    #gb = get_entity_by_name("Green Book")
    #rb = get_entity_by_name("Red Book")
    #pict = get_entity_by_name("Picture 1")
    #pen = get_entity_by_name("Black Pencil")
    #print (entities)
    #spatial.entities = get_entities()
    #print (superlative("behind",None, [e for e in entities if e.name != "Table"]).name)

def memberof (item, lst):
    if type(lst) != list:
        return item == lst
    return reduce(lambda x, y: x or y, list(map(lambda x: memberof(item, x), lst)))

if __name__ == "__main__":
    #save_screenshot()
    #fix_ids()
    #bpy.ops.wm.save_mainfile(filepath=bpy.data.filepath)
    main()
