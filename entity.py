import bpy
import bpy_types
import numpy
import math
from math import e, pi
import itertools
import os
import sys
import random
from mathutils import Vector
from geometry_utils import *

#This class comprises the implementation of the special "Entity"-type
#used in the project to represent the relevant Blender objects
#
class Entity:
    scene = bpy.context.scene

    def __init__(self, components, name=None):
        if type(components) == bpy_types.Object:
            self.components = []
            self.ent_type = "PRIMITIVE"
            self.build_from_bpy_object(components)
        elif type(components) == list and components != [] and type(components[0]) == Entity:
            self.components = components
            self.name = name
            self.ent_type = "STRUCTURE"
            self.build_from_entities(components)

    def build_from_entities(self, components):
        
        #Constituent objects
        #First object in the list is the parent or head object
        #Defining the entity
        self.constituents = [item for item in entity.constituents for entity in components]
   
        #Total mesh of the entity
        self.total_mesh = self.get_total_mesh()

        #The coordiante span of the entity. In other words,        
        #the minimum and maximum coordinates of entity's points
        self.span = self.get_span()

        #The bounding box, stored as a list of triples of vertex coordinates
        self.bbox = self.get_bbox()

        #Bounding box's centroid
        self.bbox_centroid = self.get_bbox_centroid()

        #Entity's mesh centroid
        self.centroid = self.get_centroid()

        #Dimensions of the entity in the format
        #[xmax - xmin, ymax - ymin, zmax - zmin]
        self.dimensions = self.get_dimensions()

        self.radius = self.get_radius()

        #The faces of the mesh comrising the entity
        self.faces = self.get_faces()

        #The longitudinal vector
        self.longitudinal = []

        #The frontal vector
        self.frontal = []

        #The parent offset
        self.parent_offset = self.get_parent_offset()

        self.volume = self.get_volume()            
    
    def build_from_bpy_object(self, main_object):

        #Constituent objects
        #First object in the list is the parent or head object
        #Defining the entity
        self.constituents = [main_object]
        #print ("ENTITY_MAIN:", main)

        #Filling in the constituent objects starting with the parent
        queue = [main_object]
        while len(queue) != 0:
            par = queue[0]
            queue.pop(0)
            for ob in Entity.scene.objects:                
                if ob.parent == par and ob.type == "MESH":
                    self.constituents.append(ob)
                    queue.append(ob)

        #Name of the entity
        self.name = main_object.name

        #Color of the entity
        self.color_mod = self.get_color_mod()

        #The type structure
        #Each object belong to hierarchy of types, e.g.,
        #Props -> Furniture -> Chair
        #This structure will be stored as a list
        #['Props', 'Furniture', 'Chair']
        self.type_structure = self.get_type_structure()

        #Total mesh of the entity
        self.total_mesh = self.get_total_mesh()

        #The coordiante span of the entity. In other words,        
        #the minimum and maximum coordinates of entity's points
        self.span = self.get_span()

        #The bounding box, stored as a list of triples of vertex coordinates
        self.bbox = self.get_bbox()

        #Bounding box's centroid
        self.bbox_centroid = self.get_bbox_centroid()

        #Entity's mesh centroid
        self.centroid = self.get_centroid()

        #Dimensions of the entity in the format
        #[xmax - xmin, ymax - ymin, zmax - zmin]
        self.dimensions = self.get_dimensions()

        self.radius = self.get_radius()

        #The faces of the mesh comrising the entity
        self.faces = self.get_faces()

        #The longitudinal vector
        self.longitudinal = []

        #The frontal vector
        self.frontal = []

        #The parent offset
        self.parent_offset = self.get_parent_offset()

        self.volume = self.get_volume()

    def set_type_structure(self, type_structure):
        self.type_structure = type_structure
        
    #Sets the direction of the longitudinal axis of the entity    
    def set_longitudinal(self, direction):
        self.longitudinal = direction

    #Sets the direction of the frontal axis of the entity
    def set_frontal(self, direction):
       	self.frontal = direction        

    #Calculates the coordinate span of the entity
    def get_span(self):
        if(hasattr(self, 'span') and self.span is not None):
            return self.span
        else:
            mesh = self.get_total_mesh()            
            return [min([v[0] for v in mesh]),
                    max([v[0] for v in mesh]),
                    min([v[1] for v in mesh]),
                    max([v[1] for v in mesh]),
                    min([v[2] for v in mesh]),
                    max([v[2] for v in mesh])]
                
            
            '''lower = [obj.matrix_world * (obj.location.x - obj.dimensions.x / 2.0) for obj in self.constituents]
            upper = [obj.matrix_world * (obj.location.x + obj.dimensions.x / 2.0) for obj in self.constituents]
            print (min([item[0] for item in lower]))
            return [min([item[0] for item in lower]),
                    max([item[0] for item in lower]),
                    min([item[1] for item in lower]),
                    max([item[1] for item in lower]),
                    min([item[2] for item in lower]),
                    max([item[2] for item in lower])]'''
            #return [min([(obj.matrix_world * (obj.location.x - obj.dimensions.x / 2.0)).x for obj in self.constituents]),
	    #        max([(obj.matrix_world * (obj.location.x + obj.dimensions.x / 2.0)).x for obj in self.constituents]),
	    #        min([(obj.matrix_world * (obj.location.y - obj.dimensions.y / 2.0)).y for obj in self.constituents]),
	    #        max([(obj.matrix_world * (obj.location.y + obj.dimensions.y / 2.0)).y for obj in self.constituents]),
	    #        min([(obj.matrix_world * (obj.location.z - obj.dimensions.z / 2.0)).z for obj in self.constituents]),
	    #        max([(obj.matrix_world * (obj.location.z + obj.dimensions.z / 2.0)).z for obj in self.constituents])]

    #Calculates the bounding box of the entity
    def get_bbox(self):
        if(hasattr(self, 'bbox') and self.bbox is not None):
            return self.bbox
        else:
            span = self.get_span()
            #bpy.context.scene.update()
            return [(span[0], span[2], span[4]),
	            (span[0], span[2], span[5]),
		    (span[0], span[3], span[4]),
		    (span[0], span[3], span[5]),
		    (span[1], span[2], span[4]),
		    (span[1], span[2], span[5]),
		    (span[1], span[3], span[4]),
		    (span[1], span[3], span[5])]

    #Computes the bounding box centroid
    def get_bbox_centroid(self):
        if(hasattr(self, 'bbox_centroid') and self.bbox_centroid is not None):
            return self.bbox_centroid
        else:
            bbox = self.get_bbox()
            return [bbox[0][0] + (bbox[7][0] - bbox[0][0]) / 2,
                    bbox[0][1] + (bbox[7][1] - bbox[0][1]) / 2,
                    bbox[0][2] + (bbox[7][2] - bbox[0][2]) / 2]

    #Gets the dimensions of the entity as a list of number
    def get_dimensions(self):
        if(hasattr(self, 'dimensions') and self.dimensions is not None):
            return self.dimensions
        else:
            bbox = self.get_bbox()
            return [bbox[7][0] - bbox[0][0], bbox[7][1] - bbox[0][1], bbox[7][2] - bbox[0][2]]

    #Checks if the entity has a given property
    def get(self, property):
        return self.constituents[0].get(property)

    #Coomputes the distance from a point to closest face of the entity
    def get_closest_face_distance(self, point):
        return min([get_distance_from_plane(point, face[0], face[1], face[2]) for face in self.faces])

    #STUB
    def get_closest_distance(self, other_entity):
        this_faces = self.get_faces()
        other_faces = other_entity.get_faces()

    #Returns the list of faces of the entity
    def get_faces(self):
        if(hasattr(self, 'faces') and self.faces is not None):
            return self.faces
        else:
            faces = []
            for ob in self.constituents:
                for face in ob.data.polygons:
                    faces.append([ob.matrix_world * ob.data.vertices[i].co for i in face.vertices])
        return faces

    def print(self):
        print (self.name)

    #Displays the bounding box around the entity in Blender
    def show_bbox(self):
        mesh = bpy.data.meshes.new(self.name + '_mesh')
        obj = bpy.data.objects.new(self.name + '_bbox', mesh)
        bpy.context.scene.objects.link(obj)
        bpy.context.scene.objects.active = obj
        bbox = self.get_bbox()
        mesh.from_pydata(bbox, [], [(0, 1, 3, 2), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5), (4, 5, 7, 6)])
        mesh.update()

    #Computes the total mesh centroid
    def get_centroid(self):
        if not hasattr(self, 'centroid') or self.centroid is None:
            centroid = Vector((0, 0, 0))
            vertex_count = 0
            for v in self.get_total_mesh():
                centroid += v
                vertex_count += 1
            centroid /= vertex_count
            self.centroid = centroid
        return self.centroid
            

    #Returns the hierachy of types of the entity
    def get_type_structure(self):
        if not hasattr(self, 'type_structure') or self.type_structure is None:
            if self.constituents[0].get('id') is not None:
                self.type_structure = self.constituents[0]['id'].split(".")
            else: self.type_structure = None
        return self.type_structure

    #Returns the color of the entity
    def get_color_mod(self):
        if not hasattr(self, 'color_mod') or self.color_mod is None:
            if self.constituents[0].get('color_mod') is not None:
                self.color_mod = self.constituents[0]['color_mod'].lower()
            else:
                self.color_mod = None
        return self.color_mod

    #Returns the offset of the entity relative to the location of its head object
    def get_parent_offset(self):
        span = self.get_span()
        if span is not None:
            return self.constituents[0].location.x - span[0], self.constituents[0].location.y - span[2], self.constituents[0].location.z - span[4]
        else:
            return None

    def get_radius(self):
        if not hasattr(self, 'radius'):
            total_mesh = self.get_total_mesh()
            centroid = self.get_centroid()
            self.radius = max([numpy.linalg.norm(v - centroid) for v in total_mesh])
        return self.radius
            

    #Returns the total mesh of the entity (the union of the meshes
    #of its constituent objects)
    def get_total_mesh(self):
        if not hasattr(self, 'total_mesh'):
            vertices = []
            for obj in self.constituents:
                vertices += [obj.matrix_world * v.co for v in obj.data.vertices]
            self.total_mesh = vertices
        return self.total_mesh

    def get_volume(self):
        if not hasattr(self, 'volume'):
            span = self.get_span()
            self.volume = (span[1] - span[0]) * (span[3] - span[2]) * (span[5] - span[4])
        return self.volume
