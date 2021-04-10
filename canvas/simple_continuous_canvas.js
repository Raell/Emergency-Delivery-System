var ContinuousVisualization = function(height, width, context) {
	var height = height;
	var width = width;
	var context = context;

	this.draw = function(objects) {
		for (var i in objects) {
			var p = objects[i];
			if (p.Shape == "rect")
				this.drawRectangle(p.x, p.y, p.w, p.h, p.obstacle, p.Color);
			if (p.Shape == "circle")
				this.drawCircle(p.x, p.y, p.r, p.load, p.max, p.Color);
			if (p.Shape == "triangle")
				this.drawTriangle(p.x, p.y, p.r, p.val, p.Color);
		};

	};

	this.drawCircle = function(x, y, radius, load, max_load, color) {
		var cx = x * width;
		var cy = y * height;
		var r = radius;

		context.beginPath();
		context.arc(cx, cy, r, 0, Math.PI * 2, false);
		context.closePath();

		context.strokeStyle = "#000000";
		context.lineWidth = 1;
		context.stroke();

		context.fillStyle = color;
		context.fill();

		context.fillStyle = "#FFFFFF";
		context.lineWidth = 0.5;
		for (let i = 0; i < max_load; i++) {
			context.strokeRect(cx-r*0.3, cy+r*0.5-(r*i*0.4), r*0.6, r*0.4);
			context.fillRect(cx-r*0.3, cy+r*0.5-(r*i*0.4), r*0.6, r*0.4);
		}
		context.fillStyle = "#a08f73";
		for (let i = 0; i < load; i++) {
			context.fillRect(cx - r * 0.3, cy + r * 0.5 - (r * i * 0.4), r * 0.6, r * 0.4);
		}

	};

	this.drawTriangle = function(x, y, radius, val, color) {
		var cx = x * width;
		var cy = y * height;
		var r = radius;

		context.beginPath();
		context.moveTo(cx, cy - r)
		context.lineTo(cx - r * Math.cos(7/6 * Math.PI), cy - r * Math.sin(7/6 * Math.PI))
		context.lineTo(cx - r * Math.cos(11/6 * Math.PI), cy - r * Math.sin(11/6 * Math.PI))
		context.closePath();

		context.fillStyle = color;
		context.fill();

		context.strokeStyle = "#6A6A6A";
		context.lineWidth = 1;
		context.stroke();
		context.fillStyle = "#ffffff";
		var font_size = r;
		context.font = font_size + "px sans-serif";
		context.textAlign = "center";
		context.fillText(val, cx, cy + 0.25 * r);

	};

	this.drawRectangle = function(x, y, w, h, obstacle, color) {
		context.beginPath();
		var dx = w;
		var dy = h;

		// Keep the drawing centered:
		var x0 = (x * width) - 0.5 * dx;
		var y0 = (y * height) - 0.5 * dy;
		context.fillStyle = color;
		context.fillRect(x0, y0, dx, dy);

		if (!obstacle) {
			context.strokeStyle = "#000000";
			context.lineWidth = 0.1;
			context.strokeRect(x0, y0, dx, dy);
			context.fillStyle = "#ffffff";
			var font_size = w * 0.6;
			context.font = font_size + "px sans-serif";
			context.textAlign = "center";
			context.fillText("W", x * width, y * height + w * 0.22);
		}
	};

	this.resetCanvas = function() {
		context.clearRect(0, 0, height, width);
		context.beginPath();
	};
};

var Simple_Continuous_Module = function(canvas_width, canvas_height) {
	// Create the element
	// ------------------

	// Create the tag:
	var canvas_tag = "<canvas width='" + canvas_width + "' height='" + canvas_height + "' ";
	canvas_tag += "style='border:1px dotted'></canvas>";
	// Append it to body:
	var canvas = $(canvas_tag)[0];
	$("#elements").append(canvas);

	// Create the context and the drawing controller:
	var context = canvas.getContext("2d");
	var canvasDraw = new ContinuousVisualization(canvas_width, canvas_height, context);

	this.render = function(data) {
		canvasDraw.resetCanvas();
		canvasDraw.draw(data);
	};

	this.reset = function() {
		canvasDraw.resetCanvas();
	};

};