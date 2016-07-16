# this function returns a rating value for the given number of votes and live time in seconds
def get_rating (votes, live_time):
	live_time_hours = live_time / 60.0 / 60.0 # converting seconds to hours
	gravity = 1.8
	return votes / (live_time_hours + 2) ** gravity
