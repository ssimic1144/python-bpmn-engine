from aiohttp import web
import aiohttp_cors
from time_distribution_probability import SimulationDAG
import nsga2 
import re
import sys
import os
import json
import time
#import tracemalloc
#Get parent path so it's possible to import modules from parent directory
parent_path = os.path.dirname(__file__) + "/../" 
sys.path.append(parent_path)
from bpmn_model import BpmnModel

routes = web.RouteTableDef()

#Tracemalloc
#tracemalloc.start()

#Temporary nsga2 solution storage
solution_task_list = {}

#DAG simulation storage -> model_name : simulation object
#Note for future -> store in database
dag_storage = {}

models = {}

models_directory = parent_path+"models/"
for file in os.listdir(models_directory):
    if file.endswith(".bpmn"):
        m = BpmnModel(file)
        models[file] = m

#In the future persistance for simulation, etc. will be needed
async def run_as_server(app):
    app["bpmn_models"] = models


def default_simulation_error_handler(e):
    if isinstance(e,KeyError) and re.match(".*\.bpmn",str(e)):
        error_m = f"Simulation for {str(e)} is not instantiated!" 
        return web.json_response({"error":type(e).__name__ ,"error_message":str(error_m)})
    else:
        return web.json_response({"error":type(e).__name__ ,"error_message":str(e)})

#@routes.get("/simulation/tracemalloc")
#async def get_tracemalloc(request):
#    size, peak = tracemalloc.get_traced_memory()
#    return web.json_response({"size":size,"peak":peak})

@routes.post("/simulation/dag/model/{model_name}")
async def handle_new_dag_simulation(request):
    model_name = request.match_info.get("model_name")
    try:
        dag_simulation = SimulationDAG(app["bpmn_models"][model_name])
        dag_storage[model_name] = dag_simulation
        return web.json_response({"status":"OK"})
    except Exception as e:
        return web.json_response({"error":type(e).__name__ ,"error_message":str(e)})

@routes.get("/simulation/dag/model/{model_name}/total")
async def get_dag_simulation_total_distribution(request):
    model_name = request.match_info.get("model_name")
    try:
        total_time, total_cost = dag_storage[model_name].create_total_distribution(plot=False)
        #Numpy array needs to be converted to list to be sent as JSON response
        total_time = total_time.tolist()
        total_cost = total_cost.tolist()
        total = {"time":total_time, "cost":total_cost}
        #Remove this later
        total = {}
        return web.json_response({"status":"OK", "results":total})
    except Exception as e:
        return default_simulation_error_handler(e)

@routes.get("/simulation/dag/model/{model_name}/total/optimized")
async def get_dag_simulation_optimized_total_distribution(request):
    model_name = request.match_info.get("model_name")
    #Frontend needs to send tasks list as JSON for the solution user choose
    #tasks_list = await request.json()
    #This is temporary and will be removed after testing
    tasks_list = solution_task_list[model_name]
    total_time, total_cost = dag_storage[model_name].create_optimized_total_distribution(tasks_list, plot=True)
    #total_time = total_time.tolist()
    #total_cost = total_cost.tolist()
    #total = {"time":total_time, "cost":total_cost}
    #Remove this later
    total = {}
    return web.json_response({"status":"OK", "results":total})

@routes.get("/simulation/dag/model/{model_name}/total/path/in")
async def get_path_given_constraint(request):
    params = dict(request.query)
    model_name = request.match_info.get("model_name")
    try:
        start = int(params["start"])
        end = int(params["end"])
        path = dag_storage[model_name].find_path_given_duration_constraint(start, end, json=True)
        return web.json_response({"status":"OK", "results":path})
    except Exception as e:
        return default_simulation_error_handler(e)

@routes.get("/simulation/dag/model/{model_name}/nsga2")
async def handle_nsga2_optimization_solutions_for_dag(request):
    params = dict(request.query)
    model_name = request.match_info.get("model_name")
    try:
        tasks_from_bpmn = dag_storage[model_name].get_tasks_for_optimization()
        tasks_from_bpmn["simulation object"] = dag_storage[model_name]
        tasks_ids = dag_storage[model_name].get_tasks_ids_for_optimization()
        population_size = int(params["population_size"]) if "population_size" in params else 35
        generations = int(params["generations"]) if "generations" in params else 5 
        start = time.time()
        solutions = nsga2.run(tasks_from_bpmn, tasks_ids, population_size, generations, plot=True, json=True)
        #Temporary -> will be removed later
        if isinstance(solutions["solutions"], dict):
            solution_task_list[model_name] = [json.loads(x) for x in solutions["solutions"]["tasks_list"]]
            print("Single solution!")
        print("Time : ", time.time()-start)
        return web.json_response({"status":"OK", "results": solutions})
    except Exception as e:
        return default_simulation_error_handler(e)

app = None


def run():
    global app
    app = web.Application()
    app.on_startup.append(run_as_server)
    app.add_routes(routes)

    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*",
            )
        },
    )

    for route in list(app.router.routes()):
        cors.add(route)

    return app


async def serve():
    return run()


if __name__ == "__main__":
    app = run()
    web.run_app(app, port=8081)
