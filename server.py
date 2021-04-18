from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule, TextElement
from mesa.visualization.UserParam import UserSettableParameter

from canvas.SimpleContinuousModule import SimpleCanvas
from model import DeliveryModel, Car, Truck, Job, Warehouse, Obstacle

SPACE_SIZE = 32
# SPACE_SIZE = 20
# CANVAS_SIZE = 700
CANVAS_SIZE = 480


def draw(thing):
    """
    Portrayal Method for canvas
    """
    if thing is None:
        return

    if type(thing) is Job:
        # priority_color_map = {
        #     1: "#FF4E11",
        #     2: "#FAB733",
        #     3: "#69B34C"
        # }
        priority_img = {
            1: "canvas/job_1.png",
            2: "canvas/job_2.png",
            3: "canvas/job_3.png"
        }
        portrayal = {
            "Shape": priority_img[thing.priority],
            "Layer": 0,
            "text": thing.value,
            "text_color": "#000000"
        }

    elif type(thing) in [Truck, Car]:
        portrayal = {
            "Shape": "circle",
            "r": 1,
            "Filled": True,
            "Layer": 1,
            "text": thing.curr_load,
            "text_color": "#000000"
        }

        if type(thing) is Truck:
            portrayal["Color"] = "#95DDE3"
        else:
            portrayal["Color"] = "#E3ADB5"

    elif type(thing) is Warehouse:
        portrayal = {
            "Shape": "rect",
            "w": 0.75,
            "h": 0.75,
            "Filled": True,
            "Color": "#654321",
            "Layer": 0,
            "text": "W",
            "text_color": "#FFFFFF"
        }

    elif type(thing) is Obstacle:
        portrayal = {
            "Shape": "rect",
            "w": 1,
            "h": 1,
            "Filled": True,
            "Color": "#555555",
            "Layer": 0
        }

    return portrayal


# happy_element = HappyElement()
# canvas_element = SimpleCanvas(draw, CANVAS_SIZE, CANVAS_SIZE)
# happy_chart = ChartModule([{"Label": "happy", "Color": "Black"}])
canvas_element = CanvasGrid(draw, SPACE_SIZE, SPACE_SIZE, CANVAS_SIZE, CANVAS_SIZE)

model_params = {
    "space_size": SPACE_SIZE,
    "jobs": UserSettableParameter("slider", "Total Pooled Jobs", 15, 5, 20, 5),
    "agents": UserSettableParameter(
        "slider", "Agents", 5, 1, 10, 1
    ),
    "warehouses": UserSettableParameter("slider", "Warehouses", 1, 1, 3, 1),
    "split": UserSettableParameter("slider", "Proportion of Truck agents", 0.4, 0, 1, 0.1),
    "allocation": UserSettableParameter("choice",
                                        "Task Allocation Method",
                                        "HungarianMethod",
                                        choices=["HungarianMethod", "RandomAllocation"]
                                        ),
    "use_seed": UserSettableParameter("checkbox", "Use Random Seed", True),
    "seed": UserSettableParameter("number", "Random Seed", 42)
}

# server = ModularServer(
#     Schelling, [canvas_element, happy_element, happy_chart], "Schelling", model_params
# )

server = ModularServer(
    DeliveryModel, [canvas_element], "Emergency Delivery System", model_params
)
