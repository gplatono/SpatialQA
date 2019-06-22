import spatial
import itertools
from ulf_parser import *

global_entities = []

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

def compute_predicate(predicate, *arglists):
	arg_combinations = list(itertools.product(*arglists))
	#print ("ARGLISTS: ", *arglists)
	#print ("ARG_COMB: ", arg_combinations)
	#print ("COMPUTING: " + str(predicate))	
	predicate_values = [(arg, predicate(*arg)) for arg in arg_combinations]
	return predicate_values

def filter_by_predicate_modifier(predicate_values, modifier):
	"""Return the subset of entities that satisfy the given predicate modifier."""
	if modifier.content is not None and modifier.content != "":
		modifier = modifier.content

	print ("MODIFIER CONTENT: ", modifier)

	if modifier in ['fully.adv-a', 'directly.adv-a', 'very.adv-a', 'fully.mod-a', 'directly.mod-a', 'very.mod-a']:
		return [(arg, val) for (arg, val) in predicate_values if val >= 0.85]
	elif modifier in ['slightly.adv-a', 'slightly.mod-a', 'marginally.adv-a']:
		return [(arg, val) for (arg, val) in predicate_values if val >= 0.5]
	elif modifier in ['halfway.adv-a', 'halfway.mod-a']:
		return [(arg, val) for (arg, val) in predicate_values if val >= 0.7]
	elif type(modifier) == TNeg or modifier in ['not.adv-s', 'not.adv-a', 'not.mod-a']:
		return [(arg, val) for (arg, val) in predicate_values if val <= 0.3]
	else:
		return [(arg, val) for (arg, val) in predicate_values if val >= 0.5]

def filter_by_mod(entities, modifier, global_entities):
	if type(modifier) == NColor:
		return filter_by_color(entities, modifier.content)
	elif type(modifier) == TNumber:
		#TODO!!!
		pass
	elif type(modifier) == NPred or type(modifier) == NRel:
		print ("ENTERING PRED MOD PROCESSING...", modifier, modifier.mods)
		if modifier.children is not None and modifier.children != []:
			referents = resolve_argument(modifier.children[0], global_entities)
			predicate_values = process_predicate(resolve_predicate(modifier), modifier.mods, entities, referents)
		else:
			predicate_values = process_predicate(resolve_predicate(modifier), modifier.mods, entities)

		answer_entities = list(set([arg[0] for (arg, val) in predicate_values if arg[0] in entities]))
		print ("ANSWER ENTITIES: ", answer_entities)
		return answer_entities

def process_predicate(predicate, modifiers, *arglists):
	"""
	Processes the predicate by computing its values over all the combinations
	of arguments and then appyling each modifiers to obtain more and more
	restricted list of argument tuples that satisfy the constraints of the
	predicate.

	"""
	print ("PREDICATE COMPONENTS: ",  predicate, modifiers, arglists)

	predicate_values = compute_predicate(predicate, *arglists)

	#print ("PREDICATE VALUES: ", predicate, modifiers, predicate_values)	
	if modifiers is not None and modifiers != []:
		for modifier in modifiers:
			predicate_values = filter_by_predicate_modifier(predicate_values, modifier)
			#print ("PREDICATE VALUES AFTER MOD: ", predicate, modifier, predicate_values)
	else:
		predicate_values = [(arg, val) for (arg, val) in predicate_values if val >= 0.7]

	print ("RESULTING ARGLISTS AFTER PRED FILTERING: ",  predicate_values)
	return predicate_values

def resolve_argument(arg_object, entities):
	ret_args = entities

	print (arg_object, entities)
	print (arg_object.obj_type)

	arg_type = arg_object.obj_type
	arg_id = arg_object.obj_id
	arg_det = arg_object.det
	arg_plur = arg_object.plur
	arg_mods = arg_object.mods

	#print (arg_object)
	
	if arg_type is not None:
		ret_args = filter_by_type(ret_args, arg_type)

	print ("AFTER TYPE RESOLUTION:", ret_args)

	if arg_id is not None:
		ret_args = filter_by_name(ret_args, arg_id)

	print ("AFTER NAME RESOLUTION:", ret_args)

	if arg_mods is not None and arg_mods != []:
		for modifier in arg_mods:
			print ("CURRENT MOD: ", modifier)
			ret_args = filter_by_mod(ret_args, modifier, entities)

	print ("AFTER MOD APPLICATION:", ret_args)
	return ret_args

def resolve_predicate(predicate_object):
	#print ("REL:", rel_to_func_dict[relation_object.content.content])

	rel_to_func_map = {
	'on.p': spatial.on,
	'on': spatial.on,
	'to_the_left_of.p': spatial.to_the_left_of_deic,
	'to_the_right_of.p': spatial.to_the_right_of_deic,
	'near.p': spatial.near,
	'near_to.p': spatial.near,
	'close_to.p': spatial.near,
	'close.a': spatial.near,
	'on.p': spatial.on,
	'on_top_of.p': spatial.on,
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
    'next_to.p': spatial.at,
    'clear.a': spatial.clear
    }
	#for key in globals():
	#	print (globals()[key])
	#print (type(rel_to_func_map[relation_object.content.content]))
	#print (predicate_object.content)
	if type(predicate_object.content) == str:
		return rel_to_func_map[predicate_object.content]
	else:
		if type(predicate_object.content) == TCopulaBe:
			return ident
		else:
			return rel_to_func_map[predicate_object.content.content]

def ident(arg1, arg2):
	return arg1 is arg2

def process_query(query, entities):
	#if type(query) != NSentence or (not query.is_question) or query.content == None:
	#	return None	
	if query.predicate is not None:#type(arg) == NRel or type(arg) == NPred:
		print ("ENTERING NPRED PROCESSING...")
		pred = query.predicate
		
		predicate = resolve_predicate(pred)
		print ("PREDICATE:", predicate)
		
		relata = resolve_argument(pred.children[0], entities) if len(pred.children) > 0 else None
		print ("RESOLVED RELATA:", relata)

		referents = resolve_argument(pred.children[1], entities) if len(pred.children) > 1 else None
		print ("RESOLVED REFERENTS:", referents)


		predicate_values = process_predicate(predicate, pred.mods, relata, referents) if referents is not None\
													else process_predicate(predicate, pred.mods, relata)

		"""predicate_values = []
		if referents is not None:
			predicate_values = compute_predicate(relation, relata, referents)
		else:
			predicate_values = compute_predicate(relation, relata)

		if pred.mods is not None and pred.mods != []:
			for mod in arg.mods:
				predicate_values = filter_by_predicate_modifier(predicate_values, mod)
		"""
		relata = [arg[0] for (arg, val) in predicate_values]
		#relata_certainties = [val for (arg, val) in predicate_values]
		referents = [arg[1] for (arg, val) in predicate_values] if referents is not None else None

		return relata, referents
	elif query.arg is not None:#type(arg) == NArg:
		print ("ENTERING TOP LEVEL ARG PROCESSING...")
		arg = query.arg
		relata = resolve_argument(arg, entities)
		print ("RESOLVED RELATA:", relata)
		return relata, None	
	else:
		return "FAIL"
	ret_set = entities
	if arg.obj_type is not None:
		ret_set = [entity for entity in ret_set if arg.obj_type in entity.type_structure]
	return ret_set