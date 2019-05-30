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

		#Number of objects in the world
		self.N = len(self.entities)

		self.dimensions = self.get_dimensions()
		
		self.avg_dist = 0
		if len(self.entities) != 0:
			for (a, b) in itertools.combinations(self.entities, r = 2):
				self.avg_dist += distance(a, b)		
		self.avg_dist = self.avg_dist * 2 / (self.N * (self.N - 1))
		
		self.observer = self.create_observer()


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