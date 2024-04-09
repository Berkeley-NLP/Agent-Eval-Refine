import random
COMMAND_MAP = {
    "swipe right": "idb ui swipe --udid {udid} 200 200 300 200 --duration 0.1",
    "swipe left": "idb ui swipe --udid {udid} 400 200 300 200 --duration 0.1",
    "swipe up": "idb ui swipe --udid {udid} 200 400 200 200 --duration 0.1",
    "swipe down": "idb ui swipe --udid {udid} 200 200 200 400 --duration 0.1",
    "press home": "idb ui button --udid {udid} HOME",
    "press back": "idb ui button --udid {udid} HOME", #there is no back button so do press home
    "task complete": "end",
}
#this is the configuration for iphone 14
WIDTH = 390
HEIGHT = 844
def translate_action(raw_action):
    """
	Try Translate the Android raw outputted action from CogAgent to IOS idb action
	supported actions are: 
	swipe right, 
	swipe left, 
	swipe down, 
	press home,
	press back,
	task complete,
	tap,
	type.

	Because of difference of android and ios,
	swipe up is 50% interpreted as swipe left and 50% interpreted as swipe right.

	Invalid actions will be interpreted as task complete.

	Returns:
		translated_action: one of the supported actions listed above
		idb_action: actual corresponding idb command of translated action
	"""
    try:
        raw_action = raw_action.split('Grounded Operation:')[1]
        #check if it is swipe or press home
        for k in COMMAND_MAP.keys():
            if "swipe up" in raw_action.lower():
                if random.random() < 0.5:
                    return "swipe left", COMMAND_MAP["swipe left"]
                else:
                    return "swipe right", COMMAND_MAP["swipe right"]
            if k in raw_action.lower():
                return k, COMMAND_MAP[k]
        #check if it is tap
        if "tap" in raw_action:
            numbers = raw_action.split('[[')[1].split(',')
            x = int(numbers[0])
            y = int(numbers[1].split(']]')[0])
            X = int(x * WIDTH/1000)
            Y = int(y * HEIGHT/1000)
            return raw_action, f"idb ui tap " + "--udid {udid} " + f"{X} {Y}" 
    
        if "type" in raw_action:
            to_type = raw_action.split('"')[1]
            return raw_action, f"idb ui text "+ "--udid {udid} " +  f"\"{to_type}\""
        return "Invalid action", COMMAND_MAP["task complete"]
    except:
        return "Invalid action", COMMAND_MAP["task complete"]
