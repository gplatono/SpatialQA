from spatial import *

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
	return [entity for entity in entities if entity.color_mod == color]

#Returns the list of entities having the specified type
def filter_by_type(entities, type_id):
	return [entity for entity in entities if type_id in entity.type_structure]

#Returns the list of pairs (relatum, referent) such that the given relation holds
#between them (above the threshold)
def filter_by_relation(relatums, relation, referents, threshold):
        ret_val = []
        for rel in relatums:
                for ref in referents:
                        if relation(rel, ref) >= threshold:
                                ret_val += [(rel, ref)]
        return ret_val

def filter_by_relation_modifier(arg_pairs, relation, modifier):
        ret_val = []
        for pair in arg_pairs:
                pass
                
        

def process_query(query, entities):
	arg = query.content
	if (not query.is_question) or arg == None:
		return None
	ret_set = entities
	if arg.obj_type is not None:
		ret_set = [entity for entity in ret_set if arg.obj_type in entity.type_structure]

	return ret_set
