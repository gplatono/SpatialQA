from entity import Entity
import itertools
import bpy
import bmesh
from geometry_utils import *

class World(object):
	"""
	Incapsulates the Blender scene and all the objects in it,
	i.e., a self-contained 'worldlet', as well as provides 
	the convenient API to access their properties, like the size
	of the world, object hierarchies, etc.
	"""
	def __init__(self, scene):
		self.scene = scene
		self.entities = []

		for obj in self.scene.objects:
			if obj.get('main') is not None:
				self.entities.append(Entity(obj))

		#self.test = shared_volume(self.entities[0], self.entities[1])
		#shared_volume(self.entities[0], self.entities[1])

		#Number of objects in the world
		self.N = len(self.entities)

		self.dimensions = self.get_dimensions()
		
		self.avg_dist = 0
		if len(self.entities) != 0:
			for (a, b) in itertools.combinations(self.entities, r = 2):
				self.avg_dist += distance(a, b)
		self.avg_dist = self.avg_dist * 2 / (self.N * (self.N - 1))
		
		self.observer = self.create_observer()

		#List of  possible color modifiers
		self.color_mods = ['black', 'red', 'blue', 'brown', 'green', 'yellow']

	def get_observer(self):
		if not hasattr(self, 'observer') or self.observer == None:
			self.observer = self.create_observer()
		return self.observer

	def create_observer(self):
		"""Create and configure the special "observer" object
		(which is just a camera). Needed for deictic relations as
		well as several other aspects requiring the POV concept,
		e.g., taking screenshots.
		"""
		lamp = bpy.data.lamps.new("Lamp", type = 'POINT')
		lamp.energy = 30
		cam = bpy.data.cameras.new("Camera")

		if bpy.data.objects.get("Lamp") is not None:
			lamp_obj = bpy.data.objects["Lamp"]
		else:
			lamp_obj = bpy.data.objects.new("Lamp", lamp)
			self.scene.objects.link(lamp_obj)
		if bpy.data.objects.get("Camera") is not None:
			cam_ob = bpy.data.objects["Camera"]
		else:
			cam_ob = bpy.data.objects.new("Camera", cam)
			self.scene.objects.link(cam_ob)    

		lamp_obj.location = (-20, 0, 10)
		cam_ob.location = (-15.5, 0, 7)
		cam_ob.rotation_mode = 'XYZ'
		cam_ob.rotation_euler = (1.1, 0, -1.57)
		bpy.data.cameras['Camera'].lens = 20

		bpy.context.scene.camera = self.scene.objects["Camera"]

		if bpy.data.objects.get("Observer") is None:
			mesh = bpy.data.meshes.new("Observer")
			bm = bmesh.new()
			bm.verts.new(cam_ob.location)
			bm.to_mesh(mesh)
			observer = bpy.data.objects.new("Observer", mesh)    
			self.scene.objects.link(observer)
			bm.free()
			self.scene.update()
		else: 
			observer = bpy.data.objects["Observer"]            
		observer_entity = Entity(observer)
		observer_entity.camera = cam_ob
		return observer_entity

	def get_dimensions(self):
		"""
		Compute the dimensions of the salient part of the world
		by finding the smallest bounding box containing all the 
		objects.
		"""
		x_min = [entity.x_min for entity in self.entities]
		x_max = [entity.x_max for entity in self.entities]
		y_min = [entity.y_min for entity in self.entities]
		y_max = [entity.y_max for entity in self.entities]
		z_min = [entity.z_min for entity in self.entities]
		z_max = [entity.z_max for entity in self.entities]

		return [[x_min, x_max], [y_min, y_max], [z_min, z_max]]

	def show_bbox(self, entity):
		"""Displays the bounding box around the entity in the scene."""
		mesh = bpy.data.meshes.new(entity.name + '_mesh')
		obj = bpy.data.objects.new(entity.name + '_bbox', mesh)
		self.scene.objects.link(obj)
		self.scene.objects.active = obj
		bbox = entity.bbox
		mesh.from_pydata(bbox, [], [(0, 1, 3, 2), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5), (4, 5, 7, 6)])
		mesh.update()

	def find_entity_by_name(self, name):
		"""
		Search and return the entity that has the given name
		associated with it.

		Inputs: name - human-readable name as a string

		Returns: entity (if exists) or None.
		"""

		for entity in self.entities:
			if entity.name.lower() == name.lower():
				return entity
		

		for col in self.color_mods:
			if col in name:
				name = name.replace(col + " ", "")				
		for entity in self.entities:			
			if entity.name.lower() == name.lower():
				return entity
		return None
