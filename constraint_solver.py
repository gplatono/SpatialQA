#Returns the list of entities having the specified color
def process_color(entities, color):
	return [entity for entity in entities if entity.color_mod == color]

#Returns the list of entities having the specified type
def get_entities_of_type(entities, type_id):
	return [entity for entity in entities if type_id in entity.type_structure]

def process_query(query, entities):
	arg = query.content
	if !query.is_question or arg == None:
		return None
	ret_set = entities
	if arg.obj_type is not None:
		ret_set = [entity for entity in ret_set if arg.obj_type in entity.type_structure]

	return ret_set