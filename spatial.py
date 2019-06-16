import numpy as np
import math
from entity import Entity
from geometry_utils import *
from queue import Queue
from mathutils import Vector
#from main import *

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
              'between': 'between',
              'next to': 'at' 
}

entities = []

def dist_obj(a, b):
    if type(a) is not Entity or type(b) is not Entity:
        return -1
    bbox_a = a.bbox
    bbox_b = b.bbox
    center_a = a.bbox_centroid
    center_b = b.bbox_centroid
    if a.get('extended') is not None:
        return a.get_closest_face_distance(center_b)
    if b.get('extended') is not None:
        return b.get_closest_face_distance(center_a)
    return point_distance(center_a, center_b)

#Computes the normalized area of the intersection of projection of two entities onto the XY-plane
#Inputs: a, b - entities
#Return value: real number
def get_proj_intersection(a, b):
    bbox_a = a.bbox
    bbox_b = b.bbox
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
    return math.e ** (area - min((axmax - axmin) * (aymax - aymin), (bxmax - bxmin) * (bymax - bymin)))
    
#Returns the orientation of the entity relative to the coordinate axes
#Inputs: a - entity
#Return value: triple representing the coordinates of the orientation vector
def get_planar_orientation(a):
    dims = a.dimensions
    if dims[0] == min(dims):
        return (1, 0, 0)
    elif dims[1] == min(dims):
        return (0, 1, 0)
    else: return (0, 0, 1)

#Returns the frame size of the current scene
#Inputs: none
#Return value: real number
def get_frame_size(entities):
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


#Computes the degree of vertical alignment (coaxiality) between two entities
#The vertical alignment takes the max value if one of the objects is directly above the other
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def v_align(a, b):
    dim_a = a.dimensions
    dim_b = b.dimensions
    center_a = a.bbox_centroid
    center_b = b.bbox_centroid
    return gaussian(0.9 * point_distance((center_a[0], center_a[1], 0), (center_b[0], center_b[1], 0)) / 
                                (max(dim_a[0], dim_a[1]) + max(dim_b[0], dim_b[1])), 0, 1 / math.sqrt(2*pi))

#Computes the degree of vertical offset between two entities
#The vertical offset measures how far apart are two entities one
#of which is above the other. Takes the maximum value when one is
#directly on top of another
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def v_offset(a, b):
    dim_a = a.dimensions    
    dim_b = b.dimensions
    center_a = a.bbox_centroid
    center_b = b.bbox_centroid
    h_dist = math.sqrt((center_a[0] - center_b[0]) ** 2 + (center_a[1] - center_b[1]) ** 2)    
    return gaussian(2 * (center_a[2] - center_b[2] - 0.5*(dim_a[2] + dim_b[2])) /  \
                    (1e-6 + dim_a[2] + dim_b[2]), 0, 1 / math.sqrt(2*pi))


#==========================================================================================


    

#Raw metric for the nearness relation
#Doesn't take into account the nearness statistics in the scene
#Inputs: a, b - entities
#Return value: real number from [0, 1], the raw nearness measure
def near_raw(a, b):
    bbox_a = a.bbox
    bbox_b = b.bbox
    dist = dist_obj(a, b)
    max_dim_a = max(bbox_a[7][0] - bbox_a[0][0],
                    bbox_a[7][1] - bbox_a[0][1],
                    bbox_a[7][2] - bbox_a[0][2])
    max_dim_b = max(bbox_b[7][0] - bbox_b[0][0],
                    bbox_b[7][1] - bbox_b[0][1],
                    bbox_b[7][2] - bbox_b[0][2])
    if a.get('planar') is not None:
        #print ("TEST", a.name, b.name)
        dist = min(dist, get_planar_distance_scaled(a, b))
    elif b.get('planar') is not None:
        dist = min(dist, get_planar_distance_scaled(b, a))        
    elif a.get('vertical_rod') is not None or a.get('horizontal_rod') is not None or a.get('rod') is not None:
        dist = min(dist, get_line_distance_scaled(a, b))
    elif b.get('vertical_rod') is not None or b.get('horizontal_rod') is not None or b.get('rod') is not None:
        dist = min(dist, get_line_distance_scaled(b, a))
    elif a.get('concave') is not None or b.get('concave') is not None:
        dist = min(dist, closest_mesh_distance_scaled(a, b))

    fr_size = get_frame_size(entities)
    raw_metric = math.e ** (- 0.05 * dist)
    '''0.5 * (1 - min(1, dist / avg_dist + 0.01) +'''    
    return raw_metric * (1 - raw_metric / fr_size)

entities = None
#Computes the nearness measure for two entities
#Takes into account the scene statistics:
#The raw nearness score is updated depending on whether one object is the closest to another
#Inputs: a, b - entities
#Return value: real number from [0, 1], the nearness measure
def near(a, b):
    #entities = get_entities()
    #print (entities)
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
    print ("RAW_NEAR_A: ", raw_near_a, entities)
    #print ("RAW:", a.name, b.name, raw_near_measure)
    average_near_a = sum(raw_near_a) / len(raw_near_a)
    average_near_b = sum(raw_near_b) / len(raw_near_b)
    avg_near = 0.5 * (average_near_a + average_near_b)
    max_near_a = max(raw_near_a)
    max_near_b = max(raw_near_b)
    max_near = max(raw_near_measure, max_near_a, max_near_b)
    #print ("AVER: ", average_near_a, average_near_b)
    ratio = raw_near_measure / max_near
    if (raw_near_measure < avg_near):
        near_measure_final = 0.5 * raw_near_measure
    else:        
        near_measure_final = raw_near_measure * ratio
    near_measure = raw_near_measure + (raw_near_measure - avg_near) * min(raw_near_measure, 1 - raw_near_measure)
    print ("RAW: {}; NEAR: {}; FINAL: {}; AVER: {};".format(raw_near_measure, near_measure, near_measure_final, (average_near_a + average_near_b) / 2))
    return near_measure

#Computes the between relation (a is between b and c)
#Inputs: a, b, c - entities
#Return value: real number from [0, 1]
def between(a, b, c):
    bbox_a = a.bbox
    bbox_b = a.bbox
    bbox_c = c.bbox
    center_a = a.bbox_centroid
    center_b = b.bbox_centroid
    center_c = c.bbox_centroid
    vec1 = np.array(center_b) - np.array(center_a)
    vec2 = np.array(center_c) - np.array(center_a)
    cos = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 0.001)
    dist = get_distance_from_line(center_b, center_c, center_a) / max(max(a.dimensions), max(b.dimensions), max(c.dimensions))    
    return math.exp(- 2 * math.fabs(-1 - cos))


#Computes the "larger-than" relation
#Inputs: a, b - entities
#Return value: real number from [0, 0.5]
def larger_than(a, b):
    bbox_a = a.bbox
    bbox_b = b.bbox
    return 1 / (1 + math.e ** (bbox_b[7][0] - bbox_b[0][0] \
                          + bbox_b[7][1] - bbox_b[0][1] \
                          + bbox_b[7][2] - bbox_b[0][2] \
                          - (bbox_a[7][0] - bbox_a[0][0] \
                             + bbox_a[7][1] - bbox_a[0][1] \
                             + bbox_a[7][2] - bbox_a[0][2])))

#Computes the "on" relation
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def on(a, b):
    ret_val = 0.5 * (above(a, b) + touching(a, b))
    print ("CURRENT ON:", ret_val)
    if b.get('planar') is not None and larger_than(b, a) and a.centroid[2] > 0.5 * a.dimensions[2]:
        ret_val = max(ret_val, touching(a, b))    
    #ret_val = 0.5 * (v_offset(a, b) + get_proj_intersection(a, b))
    #print ("ON {}, {}, {}".format(ret_val, get_proj_intersection(a, b), v_offset(a, b)))
    #ret_val = max(ret_val, 0.5 * (above(a, b) + touching(a, b)))
    #print ("ON {}".format(ret_val))
    for ob in b.constituents:
        ob_ent = Entity(ob)
        if ob.get('working_surface') is not None or ob.get('planar') is not None:
            ret_val = max(ret_val, 0.5 * (v_offset(a, ob_ent) + get_proj_intersection(a, ob_ent)))
            ret_val = max(ret_val, 0.5 * (int(near(a, ob_ent) > 0.99) + larger_than(ob_ent, a)))
    if b.get('planar') is not None and isVertical(b):
        ret_val = max(ret_val, math.exp(- 0.5 * get_planar_distance_scaled(a, b)))
    return ret_val

#Computes the "over" relation
#Currently, the motivation behind the model is that
#one object is considered to be over the other
#iff it's above it and relatively close to it.
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def over(a, b):
    bbox_a = a.bbox
    bbox_b = b.bbox
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
    bbox_a = a.bbox
    max_dim_a = max(bbox_a[7][0] - bbox_a[0][0],
                    bbox_a[7][1] - bbox_a[0][1],
                    bbox_a[7][2] - bbox_a[0][2]) + 0.0001
    dist = get_distance_from_line(get_observer().centroid, b.centroid, a.centroid)
    #print ("{}, {}, CLOSER: {}, WC_DEIC: {}, WC_EXTR: {}, DIST: {}".format(a.name, b.name, closer_than(a, b, observer), within_cone(b.centroid - observer.centroid, a.centroid - observer.centroid, 0.95), within_cone(b.centroid - a.centroid, Vector((0, -1, 0)) - a.centroid, 0.8), e ** (- 0.1 * get_centroid_distance_scaled(a, b))))
    return math.e ** (- 0.01 * get_centroid_distance_scaled(a, b)) * within_cone(b.centroid - a.centroid, Vector((1, 0, 0)), 0.7)
    '''0.3 * closer_than(a, b, observer) + \
                  0.7 * (max(within_cone(b.centroid - observer.centroid, a.centroid - observer.centroid, 0.95),
                  within_cone(b.centroid - a.centroid, Vector((1, 0, 0)), 0.7)) * \
                  e ** (- 0.2 * get_centroid_distance_scaled(a, b)))#e ** (-dist / max_dim_a))'''

#Enable SVA
#Computes the deictic version of the "behind" relation
#which is taken to be symmetric to "in-front-of"
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def behind_deic(a, b):
    return in_front_of_deic(b, a)

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


#Computes the "touching" relation
#Two entities are touching each other if they
#are "very close"
#Inputs: a, b - entities
#Return value: real number from [0, 1]
def touching(a, b):
    bbox_a = a.bbox
    bbox_b = b.bbox
    center_a = a.bbox_centroid
    center_b = b.bbox_centroid
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
    print ("MESH_DIST:", closest_mesh_distance_scaled(a, b))
    shared_volume = shared_volume_scaled(a, b)
    print ("SHARED VOLUME:", shared_volume)
    planar_dist = 1e9
    if a.get("planar") is not None:
        planar_dist = get_planar_distance_scaled(b, a)
    elif b.get("planar") is not None:
        planar_dist = get_planar_distance_scaled(a, b)
    print ("PLANAR DIST: ", planar_dist)    
    if get_centroid_distance_scaled(a, b) <= 1.5:
        mesh_dist = closest_mesh_distance_scaled(a, b)
    mesh_dist = min(mesh_dist, planar_dist)
    if shared_volume == 0:
        return math.exp(- 4 * mesh_dist)
    else:
        return 0.3 * math.exp(- 2 * mesh_dist) + 0.7 * (shared_volume > 0)


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

def above(a, b):
    """Computes the 'a above b' relation, returns the certainty value.

    Parameters:
    a, b - objects of type Entity

    Return value:
    float value from [0, 1]
    """
    #bbox_a = a.bbox
    #bbox_b = b.bbox
    #span_a = a.get_span()
    #span_b = b.get_span()
    #center_a = a.get_bbox_centroid()
    #center_b = b.get_bbox_centroid()
    #scaled_vertical_distance = (center_a[2] - center_b[2]) / ((span_a[5] - span_a[4]) + (span_b[5] - span_b[4]))
    #print ("ABOVE:", sigmoid(a.centroid[2] - b.centroid[2], 1, 0.1))
    #print ("CONE:",within_cone(a.centroid - b.centroid, Vector((0, 0, 1)), 0.05))    
    return within_cone(a.centroid - b.centroid, Vector((0, 0, 1)), 0.05) * sigmoid(a.centroid[2] - b.centroid[2], 1, 0.1)#math.e ** (- 0.01 * get_centroid_distance_scaled(a, b))

def below(a, b):
    """Computes the 'a below b' relation, returns the certainty value.

    Parameters:
    a, b - objects of type Entity

    Return value:
    float value from [0, 1]
    """
    return above(b, a)

#STUB
def in_front_of_intr(a, b):
    pass

#STUB
def behind_intr(a, b):
    in_front_of_intr(b, a)

def clear(obj):
    """Return the degree to which the object obj is clear, i.e., has nothing on top."""
    ent_on = [on(entity, obj) for entity in entities if entity is not obj]
    return 1 - max(ent_on)

def higher_than_centroidwise(a, b):
    """Compute whether the centroid of a is higher than the centroid of b."""

    a0 = a.get_centroid()
    b0 = b.get_centroid()    
    return a0[2] > b0[2]#1 / (1 + math.exp(-(a0[2] - b0[2])))

def taller_than(a, b):
    pass

def superlative(relation, arg, entities):
    func = globals()[rf_mapping[relation]]
    if arg != None:
        result = max([(e, func(e, arg)) for e in entities if e != arg], key=lambda x: x[1])[0]
    else:
        result = entities[0]
        if len(entities) > 1:
            for e in entities[1:]:
                if func(e, result) > func(result, e):
                    result = e
    return result

def in_front_of_extr(obj, world):
    return 1


def extract_contiguous(entities):
    """
    Extract all the contiguous subsets of entities from the given set.

    Returns:
    A list of lists, where each inner list represents a contiguous subset of entities.
    """

    if entities == []:
        return []

    groups = []

    #A flag marking if the given index has been processed and assigned a group.    
    processed = [0] * len(entities)
    
    q = Queue()

    for idx in range(len(entities)):

        """
        If the current entity has not been assigned to a group yet,
        add it to the BFS queue and create a new group for it.
        """        
        if processed[idx] == 0:
            q.put(idx)
            processed[idx] = 1
            current_group = [entities[idx]]

            """
            Perform a BFS to find all the entities reachable from the one
            that originated the current group.
            """            
            while not q.empty():
                curr_idx = q.get()
                for idx1 in range(curr_idx, len(entities)):
                    if processed[idx1] == 0 and touching(entities[curr_idx], entities[idx1]) > 0.85:
                        q.put(idx1)
                        processed[idx1] = 1
                        current_group.append(entities[idx1])

            groups.append(current_group)

    return groups
