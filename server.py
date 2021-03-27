from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule, TextElement
from mesa.visualization.UserParam import UserSettableParameter

from canvas.SimpleContinuousModule import SimpleCanvas
from model import DeliveryModel, Car, Truck, Job, Warehouse

SPACE_SIZE = 20
CANVAS_SIZE = 500


def draw(agent):
    """
    Portrayal Method for canvas
    """
    if agent is None:
        return

    if type(agent) is Job:
        priority_color_map = {
            1: "#FF4E11",
            2: "#FAB733",
            3: "#69B34C"
        }
        portrayal = {
            "Shape": "triangle",
            "r": CANVAS_SIZE / SPACE_SIZE * 0.75,
            "val": agent.value,
            "Color": priority_color_map[agent.priority]
        }
    elif type(agent) is Warehouse:
        portrayal = {
            "Shape": "rect",
            "w": CANVAS_SIZE / SPACE_SIZE,
            "h": CANVAS_SIZE / SPACE_SIZE,
            "Color": "#654321"
        }

    else:
        portrayal = {"Shape": "circle", "r": CANVAS_SIZE / (SPACE_SIZE*2), "load": agent.curr_load}

        if type(agent) is Truck:
            portrayal["Color"] = "#95DDE3"
        else:
            portrayal["Color"] = "#E3ADB5"

    return portrayal


# happy_element = HappyElement()
canvas_element = SimpleCanvas(draw, CANVAS_SIZE, CANVAS_SIZE)
# happy_chart = ChartModule([{"Label": "happy", "Color": "Black"}])

model_params = {
    "space_size": SPACE_SIZE,
    "jobs": UserSettableParameter("slider", "Jobs", 10, 1, 30, 1),
    "agents": UserSettableParameter(
        "slider", "Agents", 5, 1, 10, 1
    ),
    "split": UserSettableParameter("slider", "Proportion of Truck agents", 0.4, 0, 1, 0.1),
}

# server = ModularServer(
#     Schelling, [canvas_element, happy_element, happy_chart], "Schelling", model_params
# )

server = ModularServer(
    DeliveryModel, [canvas_element], "Delivery", model_params
)
