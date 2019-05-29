import spatial
from ulf_parser import *

#Dictionary that maps the relation names to the names of the functions that implement them
rel_to_func_dict = {'to_the_left_of.p': 'to_the_left_of_deic',
              'to_the_right_of.p': 'to_the_right_of_deic',
              'near.p': 'near',
              'on.p': 'on',
              'above.p': 'above',
              'below.p': 'below',
              'over.p': 'over',
              'under.p': 'under',
              'in.p': 'inside',
              'inside.p': 'inside',
              'touch.v': 'touching',
              'right.p': 'to_the_right_of_deic',
              'left.p': 'to_the_left_of_deic',
              'at.p': 'at',
              'in_front_of.p': 'in_front_of_deic',
              'front.p': 'in_front_of_deic',
              'behind.p': 'behind_deic',
              'between.p': 'between',
              'next_to.p': 'at'
}


#Returns the sublist of the entity list having the specified color
def filter_by_color(entities, color):
	ret_val = [] if entities == [] or entities is None \
			else [entity for entity in entities if entity.color_mod == color]
	return ret_val
	#return [entity for entity in entities if entity.color_mod == color]

#Returns the list of entities having the specified type
def filter_by_type(entities, type_id):
	print ("TYPE PROCESSING: ", type_id)
	ret_val = [] if entities == [] or entities is None \
			else [entity for entity in entities if type_id in entity.type_structure]
	return ret_val
	# # for entity in entities:
	# # 	print (entity.type_structure)
	# if entities == [] or entities is None:
	# 	return []
	# else:
	# 	return [entity for entity in entities if type_id in entity.type_structure]

#Returns the list of entities having the specified type
def filter_by_name(entities, name):
	ret_val = [] if entities == [] or entities is None \
			else [entity for entity in entities if entity.type_structure[-1].lower() == name.lower()]
	return ret_val
	# if entities == [] or entities is None:
	# 	return []
	# 	#print ("NAME:", entities[0].type_structure, type(name))
	# else:
	# 	return [entity for entity in entities if entity.type_structure[-1].lower() == name.lower()]

#Returns the list of pairs (relatum, referent) such that the given relation holds
#between them (above the threshold)
def filter_relation_by_threshold(relatums, relation, referents, threshold):
        ret_val = []
        for rel in relatums:
                for ref in referents:
                        if relation(rel, ref) >= threshold:
                                ret_val += [(rel, ref)]
        return ret_val

def filter_by_relation(relatums, relation, referents, modifier=None):
	ret_val = []
	if modifier in ['fully.adv-a', 'directly.adv-a', 'very.adv-a', 'fully.mod-a', 'directly.mod-a', 'very.mod-a']:
		return filter_relation_by_threshold(relatums, relation, referents, 0.9)
	elif modifier in ['slightly.adv-a', 'slightly.mod-a', 'marginally.adv-a']:
		return filter_relation_by_threshold(relatums, relation, referents, 0.5)
	elif modifier in ['halfway.adv-a', 'halfway.mod-a']:
		return filter_relation_by_threshold(relatums, relation, referents, 0.7)
	else:
		return filter_relation_by_threshold(relatums, relation, referents, 0.5)

def filter_by_predicate(predicate, args1, args2=None, args3=None, args4=None):
	predicate	

def filter_by_predicate_modifier(entities, pred_mod):
	"""Return the subset of entities that satisfy the given predicate modifier."""
	ret_val = []
	for entity in entities:


def filter_by_mod(entities, modifier):
	if type(modifier) == NColor:
		return filter_by_color(entities, modifier.content)
	elif type(modifier) == TNumber:
		#TODO!!!
		pass
	elif type(modifier) == NPred or type(modifier) == NRel:
		return filter_by_predicate_modifier(entities, modifier)
        
def resolve_argument(arg_object, entities):
	ret_args = entities

	arg_type = arg_object.obj_type
	arg_id = arg_object.obj_id
	arg_det = arg_object.det
	arg_plur = arg_object.plur
	arg_mods = arg_object.mods

	#print (arg_object)

	print ("BEFORE TYPE:", ret_args)

	if arg_type is not None:
		ret_args = filter_by_type(ret_args, arg_type)

	print ("BEFORE NAME:", ret_args)

	if arg_id is not None:
		ret_args = filter_by_name(ret_args, arg_id)

	print ("RESOLVED ARGS:", ret_args, [arg.name for arg in ret_args])

	if arg_mods is not None and arg_mods != []:
		for modifier in arg_mods:
			ret_args = filter_by_mod(entities, modifier)			

	return ret_args

def resolve_relation(relation_object):
	#print ("REL:", rel_to_func_dict[relation_object.content.content])
	rel_to_func_map = {
	'on.p': spatial.on,
	'on': spatial.on,
	'to_the_left_of.p': spatial.to_the_left_of_deic,
	'to_the_right_of.p': spatial.to_the_right_of_deic,
	'near.p': spatial.near,
	'close_to.p': spatial.near,
	'close.a': spatial.near,
	'on.p': spatial.on,
	'above.p': spatial.above,
    'below.p': spatial.below,
    'over.p': spatial.over,
    'under.p': spatial.under,
    'in.p': spatial.inside,
    'in': spatial.inside,    
    'inside.p': spatial.inside,
    'touch.v': spatial.touching,
    'right.p': spatial.to_the_right_of_deic,
    'left.p': spatial.to_the_left_of_deic,
    'at.p': spatial.at,
    'in_front_of.p': spatial.in_front_of_deic,
    'front.p': spatial.in_front_of_deic,
    'behind.p': spatial.behind_deic,
    'between.p': spatial.between,
    'next_to.p': spatial.at
    }
	#for key in globals():
	#	print (globals()[key])
	#print (type(rel_to_func_map[relation_object.content.content]))
	return rel_to_func_map[relation_object.content.content]

                
def process_query(query, entities):
	print ("ENTERING THE QUERY PROCESSING:")
	#print (entities)
	if type(query) != NSentence or (not query.is_question) or query.content == None:
		return None
	arg = query.content	
	if type(arg) == NRel or type(arg) == NPred:
		relation = resolve_relation(arg)
		print ("RELATION:", relation)
		res = spatial.near_raw(entities[0], entities[1])
		relata = resolve_argument(arg.children[0], entities) if len(arg.children) > 0 else None
		referents = resolve_argument(arg.children[1], entities) if len(arg.children) > 1 else None
		return "NPRED"
	elif type(arg) == NArg:
		relata = resolve_argument(arg, entities)
		print (relata)
	else:
		return "FAIL"
	ret_set = entities
	if arg.obj_type is not None:
		ret_set = [entity for entity in ret_set if arg.obj_type in entity.type_structure]
	return ret_set