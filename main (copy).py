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

#The path to the this source file
filepath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, filepath)

from entity import Entity
from geometry_utils import *
from parser import *

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
    'trash bin': 'props.item.portable.trash bin',
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
    
#Dictionary that maps the relation names to the names of the functions that implement them
rf_mapping = {'to the left of': 'to_the_left_of_deic',
              'to the right of': 'to_the_right_of_deic',
              'near': 'near',
              'on': 'on',
              'above': 'above',
              'below': 'below',
              'over': 'over',
              'under': 'under',
              'in': 'inside',
              'inside': 'inside',
              'touching': 'touching',
              'right': 'to_the_right_of_deic',
              'left': 'to_the_left_of_deic',
              'at': 'at',
              'in front of': 'in_front_of_deic',
              'front': 'in_front_of_deic',
              'behind': 'behind_deic',
              'between': 'between'}

#The list of entities
entities = []

#The observer object (camera)
observer = None

#Average distance between entities in the scene
avg_dist = 0

def dist_obj(a, b):
    if type(a) is not Entity or type(b) is not Entity:
        return -1
    bbox_a = a.get_bbox()
    bbox_b = b.get_bbox()
    center_a = a.get_bbox_centroid()
    center_b = b.get_bbox_centroid()
    if a.get('extended') is not None:
        return a.get_closest_face_distance(center_b)
    if b.get('extended') is not None:
        return b.get_closest_face_distance(center_a)
    return point_distance(center_a, center_b)

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

#Computes the normalized area of the intersection of projection of two entities onto the XY-plane
#Inputs: a, b - entities
#Return value: real number
def get_proj_intersection(a, b):
    bbox_a = a.get_bbox()
    bbox_b = b.get_bbox()
    axmin = a.span[0]
    axmax = a.span[1]
    aymin = a.span[2]
    aymax = a.span[3]
    bxmin = b.span[0]
    bxmax = b.span[1]
    bymin = b.span[2]
    bymax = b.span[3]
    xdim = 0
    ydim = 0
    if axmin >= bxmin and axmax <= bxmax:
        xdim = axmax - axmin
    elif bxmin >= axmin and bxmax <= axmax:
        xdim = bxmax - bxmin
    elif axmin <= bxmin and axmax <= bxmax and axmax >= bxmin:
        xdim = axmax - bxmin
    elif axmin >= bxmin and axmin <= bxmax and axmax >= bxmax:
        xdim = bxmax - axmin

    if aymin >= bymin and aymax <= bymax:
        ydim = aymax - aymin
    elif bymin >= aymin and bymax <= aymax:
        ydim = bymax - bymin
    elif aymin <= bymin and aymax <= bymax and aymax >= bymin:
        ydim = aymax - bymin
    elif aymin >= bymin and aymin <= bymax and aymax >= bymax:
        ydim = bymax - aymin
    area = xdim * ydim
    
    #Normalize the intersection area to [0, 1]
    return e ** (area - min((axmax - axmin) * (aymax - aymin), (bxmax - bxmin) * (bymax - bymin)))
    
#Returns the orientation of the entity relative to the coordinate axes
#Inputs: a - entity
#Return value: triple representing the coordinates of the orientation vector
def get_planar_orientation(a):
    dims = a.get_dimensions()
    if dims[0] == min(dims):
        return (1, 0, 0)
    elif dims[1] == min(dims):
        return (0, 1, 0)
    else: return (0, 0, 1)


#Returns the frame size of the current scene
#Inputs: none
#Return value: real number
def get_frame_size():
    max_x = -100
    min_x = 100
    max_y = -100
    min_y = 100
    max_z = -100
    min_z = 100

    #Computes the scene bounding box
    for entity in entities:
        max_x = max(max_x, entity.span[1])
        min_x = min(min_x, entity.span[0])
        max_y = max(max_y, entity.span[3])
        min_y = min(min_y, entity.span[2])
        max_z = max(max_z, entity.span[5])
        min_z = min(min_z, entity.span[4])
    return max(max_x - min_x, max_y - min_y, max_z - min_z)


#Raw metric for the nearness relation
#Doesn't take into account the nearness statistics in the scene
#Inputs: a, b - entities
#Return value: real number from [0, 1], the raw nearness measure
def near_raw(a, b):
    bbox_a = a.get_bbox()
    bbox_b = b.get_bbox()
    dist = dist_obj(a, b)
    max_dim_a = max(bbox_a[7][0] - bbox_a[0][0],
                    bbox_a[7][1] - bbox_a[0][1],
                    bbox_a[7][2] - bbox_a[0][2])
    max_dim_b = max(bbox_b[7][0] - bbox_b[0][0],
                    bbox_b[7][1] - bbox_b[0][1],
                    bbox_b[7][2] - bbox_b[0][2])
    if a.get('planar') is not None:
        print ("TEST", a.name, b.name)
        dist = min(dist, get_planar_distance_scaled(a, b))
    elif b.get('planar') is not None:
        dist = min(dist, get_planar_distance_scaled(b, a))        
    elif a.get('vertical_rod') is not None or a.get('horizontal_rod') is not None or a.get('rod') is not None:
        dist = min(dist, get_line_distance_scaled(a, b))
    elif b.get('vertical_rod') is not None or b.get('horizontal_rod') is not None or b.get('rod') is not None:
        dist = min(dist, get_line_distance_scaled(b, a))
    elif a.get('concave') is not None or b.get('concave') is not None:
        dist = min(dist, closest_mesh_distance_scaled(a, b))

    fr_size = get_frame_size()
    raw_metric = e ** (-0.05 * dist)
    '''0.5 * (1 - min(1, dist / avg_dist + 0.01) +'''    
    return raw_metric * (1 - raw_metric / fr_size)

#Computes the nearness measure for two entities
#Takes into account the scene statistics:
#The raw nearness score is updated depending on whether one object is the closest to another
#Inputs: a, b - entities
#Return value: real number from [0, 1], the nearness measure
def near(a, b):
    raw_near_a = []
    raw_near_b = []
    raw_near_measure = near_raw(a, b)
    for entity in entities:
        if entity != a and entity != b:
            near_a_entity = near_raw(a, entity)
            near_b_entity = near_raw(b, entity)
            #print (entity.name, near_a_entity, near_b_entity)
            #if dist_a_to_entity < raw_dist:
            raw_near_a += [near_a_entity]
            #if dist_b_to_entity < raw_dist:
            raw_near_b += [near_b_entity]
    print ("RAW:", a.name, b.name, raw_near_measure)
    average_near_a = sum(raw_near_a) / len(raw_near_a)
    average_near_b = sum(raw_near_b) / len(raw_near_b)
    #print ("AVER: ", average_near_a, average_near_b)
    near_measure = raw_near_measure + (raw_near_measure - (average_near_a + average_near_b) / 2) * (1 - raw_near_measure)
    #print (near_measure)
    return near_measure

#Computes the between relation (a is between b and c)
#Inputs: a, b, c - entities
#Return value: real number from [0, 1]
def between(a, b, c):
    bbox_a = a.get_bbox()
    bbox_b = a.get_bbox()
    bbox_c = c.get_bbox()
    center_a = a.get_bbox_centroid()
    center_b = b.get_bbox_centroid()
    center_c = c.get_bbox_centroid()
    vec1 = np.array(center_b) - np.array(center_a)
    vec2 = np.array(center_c) - np.array(center_a)
    cos = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 0.001)
    dist = get_distance_from_line(center_b, center_c, center_a) / max(max(a.dimensions), max(b.dimensions), max(c.dimensions))
    
    return math.exp(- 2 * math.fabs(-1 - cos))


#Computes the degree of vertical alignment (coaxiality) between two entities
#The vertical alignment takes the max value if one of the objects is directly above the other
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def v_align(a, b):
    dim_a = a.get_dimensions()
    dim_b = b.get_dimensions()
    center_a = a.get_bbox_centroid()
    center_b = b.get_bbox_centroid()
    return gaussian(0.9 * point_distance((center_a[0], center_a[1], 0), (center_b[0], center_b[1], 0)) / 
                                (max(dim_a[0], dim_a[1]) + max(dim_b[0], dim_b[1])), 0, 1 / math.sqrt(2*pi))

#Computes the degree of vertical offset between two entities
#The vertical offset measures how far apart are two entities one
#of which is above the other. Takes the maximum value when one is
#directly on top of another
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def v_offset(a, b):
    dim_a = a.get_dimensions()    
    dim_b = b.get_dimensions()
    center_a = a.get_bbox_centroid()
    center_b = b.get_bbox_centroid()
    h_dist = math.sqrt((center_a[0] - center_b[0]) ** 2 + (center_a[1] - center_b[1]) ** 2)    
    return gaussian(2 * (center_a[2] - center_b[2] - 0.5*(dim_a[2] + dim_b[2])) /  \
                    (1e-6 + dim_a[2] + dim_b[2]), 0, 1 / math.sqrt(2*pi))

#Computes the "larger-than" relation
#Inputs: a, b - entities
#Return value: real number from [0, 0.5]
def larger_than(a, b):
    bbox_a = a.get_bbox()
    bbox_b = b.get_bbox()
    return 1 / (1 + e ** (bbox_b[7][0] - bbox_b[0][0] \
                          + bbox_b[7][1] - bbox_b[0][1] \
                          + bbox_b[7][2] - bbox_b[0][2] \
                          - (bbox_a[7][0] - bbox_a[0][0] \
                             + bbox_a[7][1] - bbox_a[0][1] \
                             + bbox_a[7][2] - bbox_a[0][2])))


#Computes the "on" relation
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def on(a, b):
    ret_val = 0.5 * (v_offset(a, b) + get_proj_intersection(a, b))
    #print ("ON {}, {}, {}".format(ret_val, get_proj_intersection(a, b), v_offset(a, b)))
    ret_val = max(ret_val, 0.5 * (above(a, b) + touching(a, b)))
    #print ("ON {}".format(ret_val))
    for ob in b.constituents:
        ob_ent = Entity(ob)
        if ob.get('working_surface') is not None or ob.get('planar') is not None:
            ret_val = max(ret_val, 0.5 * (v_offset(a, ob_ent) + get_proj_intersection(a, ob_ent)))
            ret_val = max(ret_val, 0.5 * (int(near(a, ob_ent) > 0.99) + larger_than(ob_ent, a)))
    if b.get('planar') is not None and isVertical(b):
        ret_val = max(ret_val, math.exp(- 0.5 * get_planar_distance_scaled(a, b)))
    #if b.get('planar') is not None :
    #    ret_val = max(ret_val, )
    #if ret_val >= 0.6:
    #    return 0.5 * (ret_val + larger_than(b, a))
    return ret_val

#Computes the "over" relation
#Currently, the motivation behind the model is that
#one object is considered to be over the other
#iff it's above it and relatively close to it.
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def over(a, b):
    bbox_a = a.get_bbox()
    bbox_b = b.get_bbox()
    return 0.5 * above(a, b) + 0.2 * get_proj_intersection(a, b) + 0.3 * near(a, b)


#Computes the "under" relation, which is taken to be symmetric to "over"
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def under(a, b):
    return over(b, a)


#Computes the "closer-than" relation
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def closer_than(a, b, pivot):
    return int(point_distance(a.centroid, pivot.centroid) < point_distance(b.centroid, pivot.centroid))


#Computes the deictic version of the "in-front-of" relation
#For two objects, one is in front of another iff it's closer and
#between the observer and that other object
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def in_front_of_deic(a, b):
#def in_front_of_extr(a, b, observer):
    bbox_a = a.get_bbox()
    max_dim_a = max(bbox_a[7][0] - bbox_a[0][0],
                    bbox_a[7][1] - bbox_a[0][1],
                    bbox_a[7][2] - bbox_a[0][2]) + 0.0001
    dist = get_distance_from_line(observer.centroid, b.centroid, a.centroid)
    #print ("{}, {}, CLOSER: {}, WC_DEIC: {}, WC_EXTR: {}, DIST: {}".format(a.name, b.name, closer_than(a, b, observer), within_cone(b.centroid - observer.centroid, a.centroid - observer.centroid, 0.95), within_cone(b.centroid - a.centroid, Vector((0, -1, 0)) - a.centroid, 0.8), e ** (- 0.1 * get_centroid_distance_scaled(a, b))))
    return 0.5 * (closer_than(a, b, observer) + \
                  max(within_cone(b.centroid - observer.centroid, a.centroid - observer.centroid, 0.95),
                      within_cone(b.centroid - a.centroid, Vector((1, 0, 0)), 0.7))) * \
                      e ** (- 0.05 * get_centroid_distance_scaled(a, b))#e ** (-dist / max_dim_a))

#Enable SVA
#Computes the deictic version of the "behind" relation
#which is taken to be symmetric to "in-front-of"
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def behind_deic(a, b):
    return in_front_of_deic(b, a)

'''
def bbox_inside_test(a, b):
    shared_volume = get_bbox_intersection(a, b)
    return shared_volume / (b.dimensions[0] * b.dimensions[1] * b.dimensions[2] + 0.001)
'''

#Computes the "at" relation
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def at(a, b):
    return 0.8 * near(a, b) + 0.2 * touching(a, b)


def inside(a, b):
    a_bbox = a.bbox
    b_bbox = b.bbox
    shared_volume = get_bbox_intersection(a, b)
    proportion = shared_volume / b.volume
    return sigmoid(proportion, 1.0, 1.0)

    
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

'''
def gen_data(func_name):
    pos = 100.0
    neg = 100.0
    data = open(func_name + ".train", "w")
    index = 0
    for pair in itertools.permutations(entities, r = 2):
        if index < 1000:
            a, b = pair
            if a.name != 'plane' and b.name != 'plane':
                a_bbox_str = " ".join([" ".join([str(x) for x in y]) for y in a.get_bbox()])
                b_bbox_str = " ".join([" ".join([str(x) for x in y]) for y in b.get_bbox()])
                a_cen = a.get_bbox_centroid()
                b_cen = b.get_bbox_centroid()
                outstr = a_bbox_str + " " + b_bbox_str #" ".join([str(x) for x in a_cen]) + " " + " ".join([str(x) for x in b_cen])            
                if globals()[func_name](a, b) > 0.7: # and float(pos) / (pos + neg) <= 0.6:
                    outstr = outstr + " 1\n"
                    #pos = pos + 1
                    data.write(outstr)
                else: #if neg / (pos + neg) <= 0.6:
                    outstr = outstr + " -1\n"
                    #neg = neg + 1
                    data.write(outstr)
                index = index + 1
    data.close()
''' 

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

#Checks if the projections of two entities onto a coordinate axis "collide" (overlap)
#Inputs: int_a, int_b - the projections of two entities as intervals (pairs of numbers)
#Return value: Boolean value                
def axis_collision(int_a, int_b):
    return int_a[1] <= int_b[1] and int_a[1] >= int_b[0] or \
int_a[0] >= int_b[0] and int_a[0] <= int_b[1] or \
int_b[0] >= int_a[0] and int_b[0] <= int_a[1] or \
int_b[1] >= int_a[0] and int_b[1] <= int_a[1]

#Checks if the entity "collides" (overlaps) with some other entity along any coordinate axis
#Inputs: a - entity
#Return value: Boolean value                
def check_collisions(a):
    for entity in entities:
        if entity != a and check_collision(a, entity):
            print (entity.name, a.name)
            return True
    return False            

#Checks if two entities "collide" (overlap) along some coordinate axis
#Inputs: a,b - entities
#Return value: Boolean value                
def check_collision(a, b):
    span_a = a.get_span()
    span_b = b.get_span()
    return axis_collision((span_a[0], span_a[1]), (span_b[0], span_b[1])) and \
                          axis_collision((span_a[2], span_a[3]), (span_b[2], span_b[3])) and \
                          axis_collision((span_a[4], span_a[5]), (span_b[4], span_b[5]))

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

#Given the relations argument specification, returns the entities that
#satisfy that specification
#Inputs: arg - argument object
#Return value: the list of entities
def get_argument_entities(arg):
    ret_val = [get_entity_by_name(arg.token)]
    if ret_val == [None]:
        ret_val = []
        for entity in entities:            
            #print ("TYPE_STR: {} {}".format(entity.name, entity.type_structure))
            if (entity.type_structure is None):
                print ("NONE STRUCTURE", entity.name)                
            if (arg.token in entity.type_structure or arg.token in entity.name.lower() or arg.token == "block" and "cube" in entity.type_structure) \
               and (arg.mod is None or arg.mod.adj is None or arg.mod.adj == "" or entity.color_mod == arg.mod.adj or arg.mod.adj in entity.type_structure[-1].lower()):
                ret_val += [entity]    
    return ret_val

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

#Computes the "touching" relation
#Two entities are touching each other if they
#are "very close"
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def touching(a, b):
    bbox_a = a.get_bbox()
    bbox_b = b.get_bbox()
    center_a = a.get_bbox_centroid()
    center_b = b.get_bbox_centroid()
    rad_a = max(bbox_a[7][0] - bbox_a[0][0], \
                bbox_a[7][1] - bbox_a[0][1], \
                bbox_a[7][2] - bbox_a[0][2]) / 2
    rad_b = max(bbox_b[7][0] - bbox_b[0][0], \
                bbox_b[7][1] - bbox_b[0][1], \
                bbox_b[7][2] - bbox_b[0][2]) / 2
    
    '''for point in bbox_a:
        if point_distance(point, center_b) < rad_b:
            return 1
    for point in bbox_b:
        if point_distance(point, center_a) < rad_a:
            return 1'''
    mesh_dist = 1e9
    if get_centroid_distance_scaled(a, b) <= 1.5:
        mesh_dist = closest_mesh_distance_scaled(a, b)
    return math.exp(- 5 * mesh_dist)

#Filters the entities list according to the set of constraints, i.e.,
#returns the list of entities satisfying certain criteria
#Inputs: entities - list of entities; constaints - list of constraints in the
#form (type, value), e.g., (color_mod, 'black')
#Return value: list of entities
def filter(entities, constraints):
    result = []
    for entity in entities:
        isPass = True
        for cons in constraints:
            #print("TYPE_STR:", entity.name, entity.get_type_structure())
            if cons[0] == 'type' and entity.get_type_structure()[-2] != cons[1]:
                isPass = False
            elif cons[0] == 'color_mod' and entity.color_mod != cons[1]:
                isPass = False
        if isPass:
            result.append(entity)
    return result


#For a description task, finds the best candiadate entity
#Inputs: relation - relation name (string), rel_constraints - the list of constraints
#imposed on the relatum, referents - the list of referent entities
#Return value: the best candidate entity
def eval_find(relation, rel_constraints, referents):
    candidates = filter(entities, rel_constraints)
    print ("CANDIDATES: {}".format(candidates))
    scores = []
    if len(referents[0]) == 1 or relation == "between":
        scores = [(cand, cand.name, max([globals()[rf_mapping[relation]](cand, *ref) for ref in referents if cand not in ref])) for cand in candidates]
    else:
        scores = [(cand, cand.name, max([np.mean([globals()[rf_mapping[relation]](cand, ref) for ref in refset]) for refset in referents if cand not in refset])) for cand in candidates]
    print ("SCORES: {}".format(scores))
    max_score = 0
    best_candidate = None
    for ev in scores:
        if ev[2] > max_score:
            max_score = ev[2]
            best_candidate = ev[0]
    return best_candidate

#Processes a truth-judgement annotation
#Inputs: relation, relatum, referent1, referent2 - strings, representing
#the relation and its arguments; response - user's response for the test
#Return value: the value of the corresponding relation function
def process_truthjudg(relation, relatum, referent1, referent2, response):
    relatum = get_entity_by_name(relatum)
    referent1 = get_entity_by_name(referent1)
    referent2 = get_entity_by_name(referent2)
    print (relatum, referent1, referent2)
    if relation != "between":
        return globals()[rf_mapping[relation]](relatum, referent1)
    else: return globals()[rf_mapping[relation]](relatum, referent1, referent2)

#Extracts the constraints (type and color) for the relatum argument
#from the parsing result.
#Inputs: relatum - string, representing the relation argument;
#rel_constraints - the type and color properties of the relatum
#Return value: The list of pairs ('constraint_name', 'constraint_value')
def get_relatum_constraints(relatum, rel_constraints):
    ret_val = [('type', relatum.get_type_structure()[-2]), ('color_mod', relatum.color_mod)]
    return ret_val

#Processes a description-tast annotation
#Inputs: relatum - string, representing the relation argument;
#response - user's response for the test
#Return value: the best-candidate entity fo the given description
def process_descr(relatum, response):
    rel_constraint = parse(response)
    if rel_constraint is None:
        return None
    relatum = get_entity_by_name(relatum)
    #print ("REF: {}".format(rel_constraint.referents))
    if rel_constraint is None:
        return "*RESULT: NO RELATIONS*"
    referents = list(itertools.product(*[get_argument_entities(ref) for ref in rel_constraint.referents]))
    print("REFS:", referents)
    relation = rel_constraint.token
    return eval_find(relation, get_relatum_constraints(relatum, rel_constraint), referents)

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

#Computes a special function that takes a maximum value at cutoff point
#and decreasing to zero with linear speed to the left, and with exponetial speed to the right
#Inputs: x - position; cutoff - maximum point; left, right - degradation coeeficients for left and
#right sides of the function
#Return value: real number from [0, 1]
def asym_inv_exp(x, cutoff, left, right):
    return math.exp(- right * math.fabs(x - cutoff)) if x >= cutoff else max(0, left * (x/cutoff) ** 3)

#Symmetric to the asym_inv_exp.
#Computes a special function that takes a maximum value at cutoff point
#and decreasing to zero with linear speed to the RIGHT, and with exponetial speed to the LEFT
#Inputs: x - position; cutoff - maximum point; left, right - degradation coeeficients for left and
#right sides of the function
#Return value: real number from [0, 1]
def asym_inv_exp_left(x, cutoff, left, right):
    return math.exp(- left * (x - cutoff)**2) if x < cutoff else max(0, right * (x/cutoff) ** 3)

#Computes the deictic version of to-the-right-of relation
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def to_the_right_of_deic(a, b):
    a_bbox = get_2d_bbox(vp_project(a, observer))
    b_bbox = get_2d_bbox(vp_project(b, observer))
    axial_dist = scaled_axial_distance(a_bbox, b_bbox)
    if axial_dist[0] <= 0:
        return 0
    horizontal_component = asym_inv_exp(axial_dist[0], 1, 1, 0.05)#sigmoid(axial_dist[0], 2.0, 5.0) - 1.0
    vertical_component = math.exp(- 0.5 * math.fabs(axial_dist[1]))
    distance_factor = math.exp(- 0.1 * axial_dist[0])
    #print ("Hor:", horizontal_component, "VERT:", vertical_component, "DIST:", distance_factor)
    weighted_measure = 0.5 * horizontal_component + 0.5 * vertical_component #+ 0.1 * distance_factor
    return weighted_measure

#Computes the deictic version of to-the-left-of relation
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def to_the_left_of_deic(a, b):
    return to_the_right_of_deic(b, a)

#Computes the above relation
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def above(a, b):
    #bbox_a = a.get_bbox()
    #bbox_b = b.get_bbox()
    #span_a = a.get_span()
    #span_b = b.get_span()
    #center_a = a.get_bbox_centroid()
    #center_b = b.get_bbox_centroid()
    #scaled_vertical_distance = (center_a[2] - center_b[2]) / ((span_a[5] - span_a[4]) + (span_b[5] - span_b[4]))
    return within_cone(a.centroid - b.centroid, Vector((0, 0, 1)), 0.45) * e ** (- 0.05 * get_centroid_distance_scaled(a, b))

#Computes the below relation, which is taken to be symmetric to above
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def below(a, b):
    return above(b, a)

#STUB
def in_front_of_intr(a, b):
    pass

#STUB
def behind_intr(a, b):
    in_front_of_intr(b, a)


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
    relatum = get_entity_by_name(relatum)
    for entity in entities:
        if relatum.type_structure[-2] == entity.type_structure[-2] and (relatum.color_mod is None \
           and entity.color_mod is None or relatum.color_mod == entity.color_mod):
            ret_val += [entity]
    return ret_val

def pick_descriptions(relatum):
    candidates = get_similar_entities(relatum)
    relatum = get_entity_by_name(relatum)
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

#Entry point
#Implementation of the evaluation pipeline
def main():
    for obj in scene.objects:
        if obj.get('main') is not None:
            entities.append(Entity(obj))
    global avg_dist
    if len(entities) != 0:
        for pair in itertools.combinations(entities, r = 2):
            avg_dist += dist_obj(pair[0], pair[1])
        avg_dist = avg_dist * 2 / (len(entities) * (len(entities) - 1))

    global observer
    observer = get_observer()
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
                best_cand = process_descr(relatum, response)
                if best_cand != None:
                    print(process_descr(relatum, response).name, "==?", relatum)
                print("RESULT:", int(get_entity_by_name(relatum) == best_cand))
            elif task_type == "0":
                print("RESULT:", process_truthjudg(relation, relatum, referent1, referent2, response))
            elif task_type == "2":
                descr = pick_descriptions(relatum)
                print("RESULT: {}".format("#".join(descr)))
        return

    bl4 = get_entity_by_name("Block 4")
    bl9 = get_entity_by_name("Block 9")
    bl11 = get_entity_by_name("Block 11")
    gb = get_entity_by_name("Green Book")
    rb = get_entity_by_name("Red Book")
    #pict = get_entity_by_name("Picture 1")
    #pen = get_entity_by_name("Black Pencil")    
    print (on(gb, rb))

if __name__ == "__main__":
    #save_screenshot()
    #fix_ids()
    #bpy.ops.wm.save_mainfile(filepath=bpy.data.filepath)
    main()
