$(document).ready(function(){	
	$.ajax({
			processData: false,
		  type: "POST",
			url: "http://127.0.0.1:8888/maps",
		  data: JSON.stringify({
		  "locations": [
			 {"latitude": 40.718542, "longitude": -74.014102, "name": "\"Stuyvesant\"" },
			 {"latitude": 40.71433, "longitude": -74.010111, "name": "\"Random Point\""}

			]
		  }),
		}).success(function(  ) {
		  console.log("SUCCESS");
		});
	
});