prompt = {
	"intro": """You are an autonomous intelligent agent tasked with navigating a web browser. You will be given web-based tasks. These tasks will be accomplished through the use of specific actions you can issue.

Here's the information you'll have:
The user's objective: This is the task you're trying to complete.
The web page's accessibility tree: This is a simplified representation of the webpage, providing key information.
The web page's URL: This is the page you're currently navigating.
The open tabs: These are the tabs you have open.

The actions you can perform fall into several categories:

Page Operation Actions:
`click [id]`: This action clicks on an element with a specific id on the webpage.
`type [id] [content] [press_enter_after=0|1]`: Use this to type the content into the field with id. By default, the "Enter" key is pressed after typing unless press_enter_after is set to 0.
`hover [id]`: Hover over an element with id.
`press [key_comb]`:  Simulates the pressing of a key combination on the keyboard (e.g., Ctrl+v).
`scroll [direction=down|up]`: Scroll the page up or down.

Tab Management Actions:
`new_tab`: Open a new, empty browser tab.
`tab_focus [tab_index]`: Switch the browser's focus to a specific tab using its index.
`close_tab`: Close the currently active tab.

URL Navigation Actions:
`goto [url]`: Navigate to a specific URL.
`go_back`: Navigate to the previously viewed page.
`go_forward`: Navigate to the next page (if a previous 'go_back' action was performed).

Completion Action:
`stop [answer]`: Issue this action when you believe the task is complete. If the objective is to find a text-based answer, provide the answer in the bracket.

Now you are trying to evaluate your performance on a past task. You will be given the objective of the task, the history of interaction including the observations you had and the actions you issued, and the status of the task. You will also be given the memory of your previous attempts. Your goal is to think about the strategy and path you took to attempt to complete the task. Try to summarize the reason why you failed to complete the task, and devise a concise, new plan that accounts for your mistake and can be helpful when you are solving the same task. Try to think differently from the previous attempts. Try to focus on the key aspect and make the plan concise.
""",
	"examples": [
		(
			"""OBJECTIVE: Compare the time for walking and driving route from AMC Waterfront to Carnegie Mellon University

OBSERVATION AND ACTION HISTORY:
OBSERVATION 0:
Tab 0 (current): Dashboard / Magento Admin

[1] RootWebArea 'Dashboard / Magento Admin' focused: True
	[178] link 'Magento Admin Panel'
		[201] img 'Magento Admin Panel'
	[85] menubar '' orientation: horizontal
		[87] link '\ue604 DASHBOARD'
		[90] link '\ue60b SALES'
		[96] link '\ue608 CATALOG'
		[102] link '\ue603 CUSTOMERS'
		[108] link '\ue609 MARKETING'
		[114] link '\ue602 CONTENT'
		[120] link '\ue60a REPORTS'
		[138] link '\ue60d STORES'
		[144] link '\ue610 SYSTEM'
		[150] link '\ue612 FIND PARTNERS & EXTENSIONS'
	[821] button 'System Messages: 1'
	[902] StaticText 'One or more '
	[903] link 'indexers are invalid'
	[904] StaticText '. Make sure your '
	[905] link 'Magento cron job'
	[906] StaticText ' is running.'
	[240] heading 'Dashboard'
	[242] link '\ue600 admin'
	[244] link '\ue607'
	[913] textbox '\ue60c' required: False
	[48] main ''
		[219] StaticText 'Scope:'
		[250] button 'All Store Views' hasPopup: menu
		[253] link '\ue633 What is this?'
		[226] button 'Reload Data'
		[917] HeaderAsNonLandmark ''
			[919] StaticText 'Advanced Reporting'
		[920] StaticText "Gain new insights and take command of your business' performance, using our dynamic product, order, and customer reports tailored to your customer data."
		[921] link 'Go to Advanced Reporting \ue644'
		[924] StaticText 'Chart is disabled. To enable the chart, click '
		[925] link 'here'
		[1154] StaticText 'Revenue'
		[1054] StaticText '$0.00'
		[1155] StaticText 'Tax'
		[1156] StaticText 'Shipping'
		[1157] StaticText 'Quantity'
		[1068] StaticText '0'
		[57] tablist '' multiselectable: False orientation: horizontal
			[59] tab 'The information in this tab has been changed. This tab contains invalid data. Please resolve this before saving. Loading... Bestsellers' expanded: True selected: True controls: grid_tab_ordered_products_content
				[67] link 'The information in this tab has been changed. This tab contains invalid data. Please resolve this before saving. Loading... Bestsellers'
			[61] tab 'The information in this tab has been changed. This tab contains invalid data. Please resolve this before saving. Loading... Most Viewed Products' expanded: False selected: False controls: ui-id-1
				[69] link 'The information in this tab has been changed. This tab contains invalid data. Please resolve this before saving. Loading... Most Viewed Products'
			[63] tab 'The information in this tab has been changed. This tab contains invalid data. Please resolve this before saving. Loading... New Customers' expanded: False selected: False controls: ui-id-2
				[71] link 'The information in this tab has been changed. This tab contains invalid data. Please resolve this before saving. Loading... New Customers'
			[65] tab 'The information in this tab has been changed. This tab contains invalid data. Please resolve this before saving. Loading... Customers' expanded: False selected: False controls: ui-id-3
				[73] link 'The information in this tab has been changed. This tab contains invalid data. Please resolve this before saving. Loading... Customers'
		[79] tabpanel 'The information in this tab has been changed. This tab contains invalid data. Please resolve this before saving. Loading... Bestsellers'
			[1088] table ''
				[1158] row ''
					[1159] columnheader 'Product' required: False
					[1160] columnheader 'Price' required: False
					[1161] columnheader 'Quantity' required: False
				[1162] row 'http://localhost:7780/admin/catalog/product/edit/id/29/'
					[1167] gridcell 'Sprite Stasis Ball 65 cm' required: False
					[1168] gridcell '$27.00' required: False
					[1169] gridcell '6' required: False
		[930] StaticText 'Lifetime Sales'
		[933] StaticText '$0.00'
		[937] StaticText 'Average Order'
		[944] StaticText 'Last Orders'
		[945] table ''
			[979] row ''
				[980] columnheader 'Customer' required: False
				[981] columnheader 'Items' required: False
				[982] columnheader 'Total' required: False
			[983] row 'http://localhost:7780/admin/sales/order/view/order_id/299/'
				[988] gridcell 'Sarah Miller' required: False
				[989] gridcell '5' required: False
				[990] gridcell '$194.40' required: False
			[984] row 'http://localhost:7780/admin/sales/order/view/order_id/65/'
				[991] gridcell 'Grace Nguyen' required: False
				[992] gridcell '4' required: False
				[993] gridcell '$190.00' required: False

ACTION 0: stop [N/A]

STATUS: FAILED

REFLECTIONS FROM PREVIOUS ATTEMPTS: none""",
			"I think the task is impossible to complete, thus I issue the stop action. However, the task is not completed successfully, which means I am wrong. I think I should go to the \"REPORT\" tab and do a search there for the best-selling products next time."
		),
		(
			"""OBJECTIVE: List out reviewers, if exist, who mention about good fingerprint resistant

OBSERVATION AND ACTION HISTORY:
OBSERVATION 0:
URL: http://localhost:7770/3-pack-samsung-galaxy-s6-screen-protector-nearpow-tempered-glass-screen-protector-with-9h-hardness-crystal-clear-easy-bubble-free-installation-scratch-resist.html
Tab 0 (current): [3 Pack] Samsung Galaxy S6 Screen Protector, Nearpow [Tempered Glass] Screen Protector with [9H Hardness] [Crystal Clear] [Easy Bubble-Free Installation] [Scratch Resist]
[1] RootWebArea '[3 Pack] Samsung Galaxy S6 Screen Protector, Nearpow [Tempered Glass] Screen Protector with [9H Hardness] [Crystal Clear] [Easy Bubble-Free Installation] [Scratch Resist]' focused: True
	[1314] link 'My Account'
	[1312] link 'My Wish List'
	[1316] link 'Sign Out'
	[1319] StaticText 'Welcome, Emma Lopez!'
	[1220] link 'Skip to Content'
	[1229] link 'store logo'
		[1322] img 'one_stop_market_logo'
	[1323] link '\ue611 My Cart'
	[2246] StaticText 'Search'
	[1508] combobox '\ue615 Search' autocomplete: both hasPopup: listbox required: False expanded: False
	[2249] link 'Advanced Search'
	[1511] button 'Search' disabled: True
	[1096] tablist '' multiselectable: False orientation: horizontal
		[1098] tabpanel ''
			[40] menu '' orientation: vertical
				[791] menuitem '\ue622 Beauty & Personal Care' hasPopup: menu
				[856] menuitem '\ue622 Sports & Outdoors' hasPopup: menu
				[866] menuitem '\ue622 Clothing, Shoes & Jewelry' hasPopup: menu
				[880] menuitem '\ue622 Home & Kitchen' hasPopup: menu
				[917] menuitem '\ue622 Office Products' hasPopup: menu
				[925] menuitem '\ue622 Tools & Home Improvement' hasPopup: menu
				[930] menuitem '\ue622 Health & Household' hasPopup: menu
				[936] menuitem '\ue622 Patio, Lawn & Garden' hasPopup: menu
				[941] menuitem '\ue622 Electronics' hasPopup: menu
				[1002] menuitem '\ue622 Cell Phones & Accessories' hasPopup: menu
				[1017] menuitem '\ue622 Video Games' hasPopup: menu
				[1030] menuitem '\ue622 Grocery & Gourmet Food' hasPopup: menu
	[1253] link 'Home'
	[1256] StaticText '[3 Pack] Samsung Galaxy S6 Screen Protector, Nearpow [Tempered Glass] Screen Protector with [9H Hardness] [Crystal Clear] [Easy Bubble-Free Installation] [Scratch Resist]'
	[5] main ''
		[1257] heading '[3 Pack] Samsung Galaxy S6 Screen Protector, Nearpow [Tempered Glass] Screen Protector with [9H Hardness] [Crystal Clear] [Easy Bubble-Free Installation] [Scratch Resist]'
		[11] generic 'Availability'
			[13] StaticText 'IN STOCK'
		[1331] StaticText 'SKU'
		[1467] StaticText 'B01G31IYM0'
		[1264] LayoutTable ''
			[1469] StaticText 'Rating:'
			[1334] generic '78%'
				[2221] StaticText '% of'
				[2224] StaticText '100'
			[1335] link '12\xa0 Reviews '
			[1336] link 'Add Your Review'
		[1338] StaticText '$7.99'
		[1279] LayoutTable ''
			[1483] StaticText 'Qty'
			[1484] spinbutton 'Qty' required: False valuemin: 0 valuemax: 0 valuetext: 
			[1485] button 'Add to Cart'
		[1281] link 'Add to Wish List'
		[1282] link 'Add to Compare'
		[1287] link 'Skip to the end of the images gallery'
		[1117] button 'Previous'
		[1119] generic 'Image'
			[2252] img 'Image'
		[1118] button 'Next'

ACTION 0: 
click [1335] where [1335] is [1335] link '12\xa0 Reviews '

OBSERVATION 1: 
URL: http://localhost:7770/3-pack-samsung-galaxy-s6-screen-protector-nearpow-tempered-glass-screen-protector-with-9h-hardness-crystal-clear-easy-bubble-free-installation-scratch-resist.html
Tab 0 (current): [3 Pack] Samsung Galaxy S6 Screen Protector, Nearpow [Tempered Glass] Screen Protector with [9H Hardness] [Crystal Clear] [Easy Bubble-Free Installation] [Scratch Resist]
[1] RootWebArea '[3 Pack] Samsung Galaxy S6 Screen Protector, Nearpow [Tempered Glass] Screen Protector with [9H Hardness] [Crystal Clear] [Easy Bubble-Free Installation] [Scratch Resist]' focused: True
	[5] main ''
		[1349] StaticText 'Skip to the beginning of the images gallery'
		[1106] tablist '' multiselectable: False orientation: horizontal
			[1107] tab 'Details' expanded: False selected: False controls: description
				[1350] link 'Details'
			[1110] tab 'Reviews (12)' expanded: True selected: True controls: reviews
				[1352] link 'Reviews (12)'
			[2365] tabpanel 'Reviews (12)'
				[2460] StaticText 'Customer Reviews'
				[2555] StaticText "Best screen protectors I've used!"
				[2519] LayoutTable ''
					[2556] LayoutTableRow ''
						[2699] LayoutTableCell 'Rating'
						[2700] generic '100%'
				[2559] StaticText 'It is super clear and fingerprint resistant. It was kind of hard trying to get it on, and I did get some hairs on the sticky side, but all in all it was great! Bubbles went away around the small hairs so you can barely tell they are there. They also give you tons of extra tools to help you clean the screen and get dust particles off of the screen before you put it on. I think it was just me being clumsy with all of the dust particles getting inside the screen.'
				[2562] StaticText 'Review by '
				[2564] StaticText 'Rachel'
				[2567] StaticText 'Posted on '
				[2568] time ''
					[2701] StaticText '4/18/23'
				[2569] StaticText 'Good screen protector for the money and good customer service'
				[2522] LayoutTable ''
					[2570] LayoutTableRow ''
						[2702] LayoutTableCell 'Rating'
						[2703] generic '80%'
				[2573] StaticText 'This is the second time I have used this product. It is a little tricky to apply. I had it on my phone for about 10 months and had dropped my phone a few times without incident. The last drop shattered the protector but thankfully did what it was supposed to do and protected my phone screen. The second one in the package had a small chip in it, which caused it to have a hairline crack all the way through. I emailed the company and they were very quick to respond and sent a new one free of charge. I am very satisfied with the product and only give it a four star rating because it is sometimes very difficult to get out the bubbles. I have 2 very tiny specks that would just not come out.'
				[2576] StaticText 'Review by '
				[2578] StaticText 'chris'
				[2581] StaticText 'Posted on '
				[2582] time ''
					[2704] StaticText '4/18/23'
				[2583] StaticText 'Bubbles still there after a few days'
				[2525] LayoutTable ''
					[2584] LayoutTableRow ''
						[2705] LayoutTableCell 'Rating'
						[2706] generic '80%'
				[2587] StaticText "OK, so my first impression was, wow it worked with only 1 small bubble. I was like OK, it's normal to have a few small bubbles. The description says that the small bubbles will disappear after a couple days. Well it's been over a week and the one small tiny bubble is still there. It never went away. Ugh I need to add this to my review. The glue does not last forever. It started to come off about a month after I put it on. The bad thing when it does start to come off, it's easy to take off the screen protectant."
                
ACTION 1:
stop [Rachel]

STATUS: FAILED

REFLECTIONS FROM PREVIOUS ATTEMPTS: none""",
			"I find the review from Rachel, which is the answer to the objective. I issue the stop action with the answer. However, the task is not completed successfully. This might be because I missed other reviews that also mention about good fingerprint resistant. I think I should read all the reviews next time."
		),
	],
	"template": """OBJECTIVE: {objective}

OBSERVATION AND ACTION HISTORY:
{trajectory}
STATUS: {status}

REFLECTIONS FROM PREVIOUS ATTEMPTS: {memory}""",
	"meta_data": {
		"observation": "accessibility_tree",
		"action_type": "id_accessibility_tree",
		"keywords": ["objective", "trajectory", "status", "memory"],
		"prompt_constructor": "ReflectionGenerationPromptConstructor",
		"answer_phrase": "",
		"action_splitter": "```"
	},
}
