import spatial
import itertools
#from ulf_parser import *
from ulf_grammar import *
import numpy as np

global_entities = []
world = None

def ident(arg1, arg2):
	return int(arg1 is arg2)

def exist(arg):
	return int(arg is not None)

def color_pred(entity):
	if hasattr(entity, 'color_mod'):
		return entity.color_mod
	elif hasattr(entity, 'color'):
		return entity.color
	return None

#Dictionary that maps the relation names to the names of the functions that implement them
rel_to_func_map = {
	'on.p': spatial.on,
	'on': spatial.on,	

	'to_the_left_of.p': spatial.to_the_left_of_deic,
	'left.a': spatial.to_the_left_of_deic,
	'leftmost.a': spatial.to_the_left_of_deic,
	'to_the_right_of.p': spatial.to_the_right_of_deic,
	'right.a': spatial.to_the_right_of_deic,
	'rightmost.a': spatial.to_the_right_of_deic,
	'right.p': spatial.to_the_right_of_deic,
    'left.p': spatial.to_the_left_of_deic,
    
	'near.p': spatial.near,
	'near_to.p': spatial.near,
	'close_to.p': spatial.near,
	'close.a': spatial.near,
	'on.p': spatial.on,
	'on_top_of.p': spatial.on,
	'above.p': spatial.above,
    'below.p': spatial.below,
    'over.p': spatial.over,
    'under.p': spatial.below,    
    'underneath.p': spatial.below,    
    'supporting.p': spatial.under,

    'in.p': spatial.inside,
    'in': spatial.inside,    
    'inside.p': spatial.inside,

    'touching.p': spatial.touching,
    'touch.v': spatial.touching,
    'adjacent_to.p': spatial.touching,
    
    'at.p': spatial.at,    
    'next_to.p': spatial.at,
    
    'high.a': spatial.higher_than,
    'upper.a': spatial.higher_than,
    'highest.a': spatial.higher_than,
    'topmost.a': spatial.higher_than,
    'top.a': spatial.higher_than,
    'low.a': spatial.lower_than,
    'lowest.a': spatial.lower_than,    

    'in_front_of.p': spatial.in_front_of,
    'front.a': spatial.in_front_of,
    'frontmost.a': spatial.in_front_of,
    
    'behind.p': spatial.behind,
    'backmost.a': spatial.behind,
    'back.a': spatial.behind,
    'farthest.a': spatial.behind,
    'far.a': spatial.behind,
    'between.p': spatial.between,
    'clear.a': spatial.clear,
    'where.a': spatial.where,
    'exist.pred': exist,

    'face.v': spatial.facing,
    'facing.p': spatial.facing,

    'color.pred': color_pred
}

#Dictionary mapping the predicates to the number of their arguments
arity = {
	spatial.on: 2,
	spatial.to_the_left_of_deic: 2,
	spatial.to_the_right_of_deic: 2,
	spatial.near: 2,
	spatial.above: 2,
    spatial.below: 2,
    spatial.over: 2,
    spatial.under: 2,
    spatial.inside: 2,
    spatial.touching: 2,    
    spatial.at: 2,
    spatial.in_front_of: 2,    
    spatial.behind: 2,
    spatial.between: 3,
    spatial.clear: 1,	
	spatial.higher_than: 2,
	spatial.lower_than: 2,
	spatial.where: 1,
	spatial.facing: 2,
	ident: 2,
	exist: 1,
	color_pred: 1
    }

#Returns the sublist of the entity list having the specified color
def filter_by_color(entities, color):
	ret_val = [] if entities == [] or entities is None \
			else [entity for entity in entities if entity.color_mod == color]
	return ret_val

#Returns the list of entities having the specified type
def filter_by_type(entities, type_id):	
	print ("TYPE PROCESSING: ", type_id)
	ret_val = [] if entities == [] or entities is None \
			else [entity for entity in entities if type_id in entity.type_structure or type_id == 'one']
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
			else [entity for entity in entities if entity.type_structure[-1].lower().replace("'", "") == name.lower().replace("'", "")]
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

def form_arg_tuples(args, arity):	
	cert_dict = {}
	for item in args:
		cert_dict[item[0]] = item[1]
	bare_args = [item[0] for item in args]	
	tuples = list(itertools.combinations(bare_args, arity))
	ret_val = [(tup, np.average([cert_dict[item] for item in tup])) for tup in tuples]
	# print ("TUPLES: ", arity)
	# print ("BARE ARGS: ", bare_args)
	# print ("TUPLE LIST: ", tuples)
	# print ("ARGS: ", args)
	# print ("PROC ARGS: ", ret_val)
	return ret_val

def filter_by_numeral(numeral, entities):
	"""
	Return the list of tuples of entities
	determined by the numeral.

	"""
	print ("NUMERAL: ", numeral)
	num = 1
	if numeral.content == "two.d" or numeral.content == "two.a":
		num = 2
	elif numeral.content == "three.d" or numeral.content == "three.a":
		num = 3
	elif numeral.content == "four.d" or numeral.content == "four.a":
		num = 4

	# ret_val = list(itertools.combinations(entities, num))
	# ret_val = [(arg, 1.0) for arg in ret_val]
	ret_val = form_arg_tuples(entities, num)

	return ret_val

def compute_predicate(predicate, *arglists):	
	arg_combinations = list(itertools.product(*arglists))	
	print ("ARG_LISTS: ", arglists, *arglists, arg_combinations)
	if arg_combinations is None or arg_combinations == [] or len(arg_combinations[0]) != arity[predicate]:
		return []
	predicate_values = [(arg, predicate(*arg)) for arg in arg_combinations]	
	return predicate_values

def compute_predicate1(predicate, relata, referents):
	# if referents is not None and referents != []:
	# 	arg_combinations = [(rel[0], ref[0], (rel[1] + ref[1]) / 2) for rel in relata for ref in referents]
	# else:
	# 	arg_combinations = relata
	# #arg_combinations = list(itertools.product(relata, referents))
	#arg_combinations = [(item[0][0], item[1][0], (item[0][1] + item[1][1]) / 2) for item in arg_combinations]
	#print ("ARG_LISTS: ", arglists, *arglists, arg_combinations)
	# if arg_combinations is None or arg_combinations == []:# or len(arg_combinations[0]) != arity[predicate]:
	# 	return []
	predicate_values = []

	print("\n\n\n")
	print ("RELATA: ", relata)
	print ("\nREFS: ", referents)

	for rel in relata:
		if type(rel[0]) != tuple:
			rel = ((rel[0],), rel[1])
		rel_tuples = list(itertools.combinations(rel[0], r = 1))
		rel_cert = rel[1]
		if referents is not None and referents != []:
			for ref in referents:
				if type(ref[0]) != tuple:
					ref = ((ref[0],), ref[1])
				ref_tuples = list(itertools.combinations(ref[0], r = arity[predicate] - 1))
				ref_cert = ref[1]
				print ("REL TUPLES: ", rel_tuples)
				print ("REF TUPLES: ", ref_tuples)
				arg_combinations = list(itertools.product(rel_tuples, ref_tuples))
				print ("ARG_COMBINATIONS: ", arg_combinations)
				arg_combinations = [(*arg0, *arg1) for (arg0, arg1) in arg_combinations]
				print ("ARG_COMBINATIONS1: ", arg_combinations)
				pred_value = np.average([predicate(*arg) for arg in arg_combinations])
				predicate_values.append(((*rel[0], *ref[0]), pred_value))
		else:
			arg_combinations = rel_tuples
			pred_value = np.average([predicate(*arg) for arg in arg_combinations])
			predicate_values.append(((*rel[0], None), pred_value))

	#predicate_values = [(arg, predicate(*arg)) for arg in arg_combinations]	
	return predicate_values

def filter_by_predicate_modifier(predicate_values, modifier):
	"""Return the subset of entities that satisfy the given predicate modifier."""
	if modifier.content is not None and modifier.content != "":
		modifier = modifier.content

	print ("MODIFIER CONTENT: ", modifier)

	if modifier in ['fully.adv-a', 'directly.adv-a', 'very.adv-a', 'fully.mod-a', 'directly.mod-a', 'very.mod-a']:
		return [(arg, val) for (arg, val) in predicate_values if val >= 0.9]
	elif modifier in ['slightly.adv-a', 'slightly.mod-a', 'marginally.adv-a']:
		return [(arg, val) for (arg, val) in predicate_values if val >= 0.5]
	elif modifier in ['halfway.adv-a', 'halfway.mod-a']:
		return [(arg, val) for (arg, val) in predicate_values if val >= 0.8]
	elif type(modifier) == TNeg or modifier in ['not.adv-s', 'not.adv-a', 'not.mod-a']:
		return [(arg, 1 - val*0.3/0.7) for (arg, val) in predicate_values if val < 0.7]
	elif type(modifier) == TSuperMarker:
		#predicate_values.sort(key = lambda x: x[1])
		arg, val = predicate_values[0]
		if val > 0.7 or (len(predicate_values) > 1 and val > 1.1 * predicate_values[1][1]):
			return [(arg, 1.0)]
		else:
			return []
	else:
		return [(arg, val) for (arg, val) in predicate_values if val >= 0.7]

def filter_by_mod(entities, modifier, entity_list):
	if type(modifier) == NColor:
		items = [entity[0] for entity in entities]
		ret_val = filter_by_color(items, modifier.content)
		return [(item, 1.0) for item in ret_val]
	elif type(modifier) == TNumber:		
		ret_val = filter_by_numeral(modifier, entities)
		return ret_val
	elif type(modifier) == TAdj:
		print ("ADJ PROCESSING... PRED = ", modifier, " RELATA = ", entities)
		pred = NPred(content = modifier.content, mods = modifier.mods)
		predicate_values = process_predicate1(pred, relata=entities, entity_list=entity_list)

		answer_set = {}
		for (item, val) in predicate_values:
			if item[0] not in answer_set.keys():
				answer_set[item[0]] = 0
			answer_set[item[0]] = max(answer_set[item[0]], val)
		
		answer_set = [(item, answer_set[item]) for item in answer_set.keys()]
		return answer_set
	elif type(modifier) == NPred or type(modifier) == NRel:
		predicate_values = process_predicate1(modifier, relata=entities, entity_list=entity_list)

		answer_set = {}
		for (item, val) in predicate_values:
			if item[0] not in answer_set.keys():
				answer_set[item[0]] = 0
			answer_set[item[0]] = max(answer_set[item[0]], val)
		
		answer_set = [(item, answer_set[item]) for item in answer_set.keys()]
		return answer_set

def pick_candidates(predicate_values, pick_unique=False):
	if pick_unique:
		return predicate_values[0]
	else:
		max_val = predicate_values[0][1]
		ret_vals = []
		# for item
		# if max_val >= 0.8

def process_predicate(predicate, relata=None, referents=None, entity_list=None):
	"""
	Processes the predicate by computing its values over all the combinations
	of arguments and then appyling each modifiers to obtain more and more
	restricted list of argument tuples that satisfy the constraints of the
	predicate.

	"""
	#print ("ENTERING PREDICATE PROCESSING: ", predicate)
	predicate_func = resolve_predicate(predicate)
	pred_arity = arity[predicate_func]
	modifiers = predicate.mods
	print ("\nPREDICATE COMPONENTS: ", predicate, modifiers)
	unique = False
	

	#Resolve arguments
	print (relata, referents)
	if relata is None:
		relata = resolve_argument(predicate.children[0], entity_list) if len(predicate.children) > 0 else None
		if referents is None:
			referents = resolve_argument(predicate.children[1], entity_list) if len(predicate.children) > 1 else None
	elif referents is None:
		referents = resolve_argument(predicate.children[0], entity_list) if len(predicate.children) > 0 else None
	print ("RESOLVED RELATA:", relata)
	print ("RESOLVED REFERENTS:", referents)	

	if relata is not None and relata != []:
		relata = [item for (item, val) in relata]
	if referents is not None and referents != []:
		#referents = [item for (item, val) in referents]
		if type(referents[0][0]) == tuple:
			arg_len = len(referents[0][0])
			#print ("GETTING TUPLE... ", referents[0], referents[0][0], arg_len)
			referents = [[arg_tuple[idx] for (arg_tuple, val) in referents] for idx in range(arg_len)]
		else:
			referents = [[arg for (arg, val) in referents]]

	#For handling "Where" requests
	if predicate_func == spatial.where:		
		predicate_values = [spatial.where(relatum) for relatum in relata]
		return predicate_values

	#For superlatives	
	if referents is None and pred_arity == 2:
		unique = True
		referents = world.active_context		
		predicate_values = []
		for relatum in relata:
			avg = np.average([val for ref in referents for (arg, val) in compute_predicate(predicate_func, [relatum], [ref])])
			predicate_values.append(((relatum,), avg)) 
		print ("AVG VAL: ", predicate_values)
	#For the rest
	else:
		print ("FINAL_RELATA: ", relata)
		print ("FINAL_REFERENTS: ", referents)
		predicate_values = compute_predicate(predicate_func, relata, *referents) if referents is not None\
						else compute_predicate(predicate_func, relata)

	predicate_values.sort(key = lambda x: x[1])
	predicate_values.reverse()

	print ("PREDICATE VALUES: ", predicate_values)	
	if modifiers is not None and modifiers != []:
		for modifier in modifiers:
			predicate_values = filter_by_predicate_modifier(predicate_values, modifier)
	elif predicate_values is not None and predicate_values != []:
		if unique == False:
			predicate_values = [(arg, val) for (arg, val) in predicate_values if val >= 0.7]
		else:
			predicate_values = [predicate_values[0]]

	print ("RESULTING ARGLISTS AFTER PRED FILTERING: ",  predicate_values)	
	if len(predicate_values) > 0 and type(predicate_values[0][0]) == tuple and \
			len(predicate_values[0][0]) > 1:
		if predicate_func != ident:
			predicate_values = [(arg, val) for (arg, val) in predicate_values if arg[0] not in arg[1:]]
		
	print ("FINAL ARGLISTS RETURNED FROM PRED: ",  predicate_values)
	return predicate_values

def process_predicate1(predicate, relata=None, referents=None, entity_list=None):
	"""
	Processes the predicate by computing its values over all the combinations
	of arguments and then appyling each modifiers to obtain more and more
	restricted list of argument tuples that satisfy the constraints of the
	predicate.

	"""
	#print ("ENTERING PREDICATE PROCESSING: ", predicate)
	predicate_func = resolve_predicate(predicate)
	pred_arity = arity[predicate_func]
	modifiers = predicate.mods
	print ("\nPREDICATE COMPONENTS: ", predicate, modifiers)
	unique = False

	#Resolve arguments
	print ("ARGS BEFORE RESOLVING: ", relata, referents)
	if relata is None:
		relata = resolve_argument(predicate.children[0], entity_list) if len(predicate.children) > 0 else None
		if referents is None:
			referents = resolve_argument(predicate.children[1], entity_list) if len(predicate.children) > 1 else None
	elif referents is None:
		referents = resolve_argument(predicate.children[0], entity_list) if len(predicate.children) > 0 else None
	print ("RESOLVED RELATA:", relata)
	print ("RESOLVED REFERENTS:", referents)
	
	#For handling "Where" and color requests
	if predicate_func == spatial.where:		
		predicate_values = [spatial.where(relatum[0]) for relatum in relata]
		print ("WHERE PRED VALUES: ", predicate_values)
		return predicate_values
	elif predicate_func == color_pred:
		predicate_values = [color_pred(relatum[0]) for relatum in relata]
		return predicate_values

	#For superlatives	
	if (referents is None or referents == []) and pred_arity == 2:
		unique = True
		referents = [(ent, 1.0) for ent in world.active_context]
		print ("REFERENTS FOR SUP:", referents)
		predicate_values = []
		for relatum in relata:
			avg = np.average([val for ref in referents for (arg, val) in compute_predicate1(predicate_func, [relatum], [ref])])
			predicate_values.append(((relatum[0],), avg)) 
		print ("AVG VAL: ", predicate_values)
	#For the rest
	else:
		print ("FINAL_RELATA: ", relata)
		print ("FINAL_REFERENTS: ", referents)
		predicate_values = compute_predicate1(predicate_func, relata, referents)

	predicate_values.sort(key = lambda x: x[1])
	predicate_values.reverse()

	print ("PREDICATE VALUES: ", predicate_values)	
	if modifiers is not None and modifiers != []:
		for modifier in modifiers:
			predicate_values = filter_by_predicate_modifier(predicate_values, modifier)
	elif predicate_values is not None and predicate_values != []:
		if unique == False:
			predicate_values = [(arg, val) for (arg, val) in predicate_values if val >= 0.7]
		else:
			predicate_values = [predicate_values[0]]

	print ("RESULTING ARGLISTS AFTER PRED FILTERING: ",  predicate_values)	
	if len(predicate_values) > 0 and type(predicate_values[0][0]) == tuple and \
			len(predicate_values[0][0]) > 1:
		if predicate_func != ident:
			predicate_values = [(arg, val) for (arg, val) in predicate_values if arg[0] not in arg[1:]]
		
	print ("FINAL ARGLISTS RETURNED FROM PRED: ",  predicate_values)
	return predicate_values

def resolve_argument(arg_object, entities):
	ret_args = entities

	#print (arg_object, entities)
	#print (arg_object.obj_type

	print ("RESOLVING THE ARGUMENT...", arg_object)

	if type(arg_object) == NConjArg:
		args1 = resolve_argument(arg_object.children[0], entities)
		args2 = resolve_argument(arg_object.children[1], entities)
		ret_args = []
		for arg1 in args1:
			for arg2 in args2:
				ret_args.append(((arg1[0], arg2[0]), (arg1[1]+arg2[1]) / 2))
		return ret_args

	arg_type = arg_object.obj_type
	arg_id = arg_object.obj_id
	arg_det = arg_object.det
	arg_plur = arg_object.plur
	arg_mods = arg_object.mods
	#arg_mods.reverse()

	#print (arg_object)
	print ("ARG CANDIDATES: ", entities)
	if arg_type is not None:
		ret_args = filter_by_type(ret_args, arg_type)

	print ("AFTER TYPE RESOLUTION:", ret_args)

	if arg_id is not None:
		ret_args = filter_by_name(ret_args, arg_id)

	print ("AFTER NAME RESOLUTION:", ret_args)

	if ret_args is not None and ret_args != []:
		if type(ret_args[0]) != tuple:
			ret_args = [(item, 1.0) for item in ret_args]

	print ("ARGS BEFORE MODIFIERS: ", ret_args, arg_mods)
	if arg_mods is not None and arg_mods != []:
		for modifier in arg_mods:
			print ("CURRENT MOD: ", modifier)
			ret_args = filter_by_mod(ret_args, modifier, entities)
			print ("CURRENT ARGS: ", ret_args)

	print ("AFTER MOD APPLICATION:", ret_args)
	return ret_args

def resolve_predicate(predicate_object):	
	if type(predicate_object) == str:
		pred = rel_to_func_map[predicate_object]
	elif predicate_object.content is not None and type(predicate_object.content) == str:
		pred = rel_to_func_map[predicate_object.content]
	else:
		if type(predicate_object.content) == TCopulaBe:
			pred = ident
		else:			
			pred = rel_to_func_map[predicate_object.content.content]
	print ("RESOLVING PREDICATE...", pred)
	return pred

def process_query(query, entities):
	#if type(query) != NSentence or (not query.is_question) or query.content == None:
	#	return None	
	if query.predicate is not None:#type(arg) == NRel or type(arg) == NPred:
		print ("\nENTERING NPRED PROCESSING...")
		pred = query.predicate
		
		relata = []
		referents = []

		predicate_values = process_predicate1(pred, entity_list=entities)
		if query.query_type == query.QueryType.DESCR or query.query_type == query.QueryType.ATTR_COLOR:
			return predicate_values		
		if predicate_values is not None and predicate_values != []:
			relata = [(arg[0], val) for (arg, val) in predicate_values]
			relata.sort(key = lambda x: x[1])
			relata.reverse()

			#Remove duplicates
			encountered_relata = []
			filtered_relata = []
			for (arg, val) in relata:
				if arg not in encountered_relata:
					encountered_relata.append(arg)
					filtered_relata.append((arg, val))
			relata = filtered_relata

			if pred.children[0].plur == False:
				relata = [relata[0]]
			
			if len(predicate_values[0][0]) == 2:		
				referents = [(arg[1], val) for (arg, val) in predicate_values]
				if referents is not None:
					referents.sort(key = lambda x: x[1])
					referents.reverse()
					if len(pred.children) > 1 and pred.children[1].plur == False:
						referents = [referents[0]]		
			
		return relata, referents
	elif query.arg is not None:#type(arg) == NArg:
		print ("\nENTERING TOP LEVEL ARG PROCESSING...")
		arg = query.arg
		relata = resolve_argument(arg, entities)
		print ("RESOLVED RELATA:", relata)		
		if relata != None and relata != []:
			if type(relata[0]) != tuple:
				relata = [(item, 1.0) for item in relata]

			relata.sort(key = lambda x: x[1])
			relata.reverse()

			#Remove duplicates
			encountered_relata = []
			filtered_relata = []
			for (arg, val) in relata:
				if arg not in encountered_relata:
					encountered_relata.append(arg)
					filtered_relata.append((arg, val))
			relata = filtered_relata

			if arg.plur == False:
				relata = [relata[0]]
		
		return relata, None
	else:
		return "FAIL"
	ret_set = entities
	if arg.obj_type is not None:
		ret_set = [entity for entity in ret_set if arg.obj_type in entity.type_structure]
	return ret_set