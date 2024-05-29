justify_user_prompt_1 = """
	Give the most promising ticket.
	The response JSON must be like the following:
	{
		"ticket": <The numbers of three players expecting to arrive 1st, 2nd and 3rd, in that order. Numbers are separated by `-`.>
	}
"""

justify_user_prompt_2 = """
	Give an argument for justifying why {comb} is the most promising ticket.
	You must argue your justify in a persuasive and professional tone, based on the rules of boat racing and also the provided statistical tables.
	The argument must be in Japanese.
	Don't change your prediction, just clarify the argument. Don't use fake statistic numbers, only use numbers specified in the provided tables.

	The response JSON must be like the following:
	{{
		"justify": <The argument for why {comb} is the most promising. Don't use the word `チケット`. Format the text with paragraphs separated by \n. Use players' names in explanation if they were specified in the tables.>
	}}

	Table 1: Performance statistics of players at {jcd} over the last three seasons.
	<table_conent>
	{jcd_stat}
	</table_content>

	Table-2: Performance statistics of players on the current starting course over the last three seasons.
	<table_content>
	{general_stat}
	</table_content>
"""

justify_sys_prompt = """
	You are an AI assistant to help customers who want to purchase a betting ticket for Japanese boat racing.
	Over the year, boat race seasons are held throughout Japan.
	Today's game is played at {jcd}.
	There are total six players participating to compete.
	Each player has a number from 1 to 6, depending on the course they start on.
	Win or lose in a boat race is determined by the player's experience, ability and also some of luck.
	Since boat racing is a closed elliptic curve, the innermost course (i.e., Course 1) is often considered advantageous, but this is not necessarily true.
	Quick and good start timing is very important for players when the launching signal is released.
	In a betting ticket, purchasers must enter the numbers of the players you expect to arrive 1st, 2nd and 3rd, in that order.
	You must recommend a promising ticket for your customer and also justify your prediction.
	Your response must always be in JSON format.
"""
