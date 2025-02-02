# A python module for parsing and executing BPMN models

## Supported BPMN elements so far:

### Events
- Message 
    - Catch event is supported at the moment
    - To activate Catch MessageEvent, post request must be sent at `/instance/{instance_id}/task/{task_id}/message`
    - If there is data associated with the request it must be sent as JSON 
        - Engine will process data and store JSON key:value pairs into process variables
- Timer
    - At the moment timer definition type **must** be `Duration`
    - Duration must be specified in ISO 8601 format for duration - `PnYnMnDTnHnMnS`
        - P - is obligatory
        - T - is obligatory when specifing hours,minutues and/or seconds
        - e.g. `P1DT3H20S` - one day,three hours and 20 seconds
        - e.g. `P2W` - two weeks -> weeks **can not** be mixed with other letters
- Error
    - When used as EndEvent 
        - Global Error reference must be added 
        - Message **must** be specified as it is used to find BoundaryEvent catching the error
    - When used as BoundaryEvent
        - To catch the error, Message Variable **must** be the same as the Message used in the EndEvent

### Start events
- Message
- Timer
- None

### End events
- Terminate
- Error
    - Supported only on SubProcess and CallActivity
- None

### Interrupting Boundary events
- Timer
- Error 
- Message

### Intermediate Catch events
- Message
- Timer

### User Task
- Form fields
    - Id, Type, Label
    - Validation, Properties
- Element Documentation 

### Service Task & Send Task
- Supported implementation at the moment is **Connector**
    - Connector Id **must** be `http-connector`
- Input variables and output variables for Service and Send task **must** be specified inside **Input/Output** tab
    - Input parameters type at the moment can be **String or Expression** and if you plan to use process variables you should use expression, eg. `${my_process_variable}`, only **String or Expression** type is currently supporting expressions
        - All input variables will be send as JSON to the service  
    - Output parameters will be saved to process variables by their _name_, **String or Expression** is currently advised although only Script is not supported 
        - It is expected that service response with JSON
        - It will try to match Output parameter _name_ with keys inside JSON -> if found -> process_variables\[_name_] = response\[_name_]

### Call Activity
- CallActivity Type **must** be BPMN
- Called Element **must** be *process_id* of process you wish to start
- Binding **must** be **deployment** if you wish to call process from other BPMN diagram, other bindings assumes that called process is inside the same diagram as Call Activity

### Gateways (Exclusive, Parallel)

### Sequence flow with conditions
- To use conditions on sequence flows you **must** chose Condition Type **Expression** and in Expression you need to write `key:value` where `key` is the process variable name and `value` is string
- eg. `standard:BPMN` -> engine will check -> `process_variables["standard"]` == `"BPMN"` -> if True returns True -> process continues on that Sequence Flow
- In the future real expression will be possible 

### Collaboration Diagrams
- In case there is more then 1 Pool in Collaboration diagram you **MUST** specify in **Extensions/Properties** a property with _name_ `is_main` and _value_ `True` for your **main** Pool so the engine knows where to start the process

---

## Pending features:
-   full fledged REST API
-   all standard BPMN elements
-   ...

---

## Supported DMN elements so far:
### Decision table


## Example BPMN model used for demo:
![image](https://user-images.githubusercontent.com/714889/114159824-81c65d80-9926-11eb-8b74-6d5dd9bb82ea.png)

> The package can be used as a standalone server exposing a REST API (see `server.py`)

Example execution trace:

```python
Running process 1
-----------------
        [1] --> msg in: t_wrong
        [1] Waiting for user... [UserTask(Which option?)]
        [1] --> msg in: t0
        [1] DOING: UserTask(Which option?)
        [1] Waiting for user... [UserTask(Down), UserTask(Up)]
        [1] --> msg in: tup
        [1] DOING: UserTask(Up)
        [1] Waiting for user... [UserTask(Down), ParallelGateway(ParallelGateway_0vffee4)]
        [1] --> msg in: t_wrong
        [1] Waiting for user... [UserTask(Down), ParallelGateway(ParallelGateway_0vffee4)]
        [1] --> msg in: tdown
        [1] DOING: UserTask(Down)
        [1] DOING: ManualTask(Manual Task 2)
        [1] DOING: ServiceTask(Task 3)
        [1]     - checking variables={} with ['option==1']...
        [1]       DONE: Result is False
        [1]     - going down default path...
        [1] Waiting for user... [UserTask(Task down)]
        [1] --> msg in: t_wrong
        [1] Waiting for user... [UserTask(Task down)]
        [1] --> msg in: tup2
        [1] Waiting for user... [UserTask(Task down)]
        [1] --> msg in: t_wrong
        [1] Waiting for user... [UserTask(Task down)]
        [1] --> msg in: tdown2
        [1] DOING: UserTask(Task down)
        [1] DONE
Running process 2
-----------------
        [2] --> msg in: t_wrong
        [2] Waiting for user... [UserTask(Which option?)]
        [2] --> msg in: t0
        [2] DOING: UserTask(Which option?)
        [2] Waiting for user... [UserTask(Down), UserTask(Up)]
        [2] --> msg in: tup
        [2] DOING: UserTask(Up)
        [2] Waiting for user... [UserTask(Down), ParallelGateway(ParallelGateway_0vffee4)]
        [2] --> msg in: t_wrong
        [2] Waiting for user... [UserTask(Down), ParallelGateway(ParallelGateway_0vffee4)]
        [2] --> msg in: tdown
        [2] DOING: UserTask(Down)
        [2] DOING: ManualTask(Manual Task 2)
        [2] DOING: ServiceTask(Task 3)
        [2]     - checking variables={} with ['option==1']...
        [2]       DONE: Result is False
        [2]     - going down default path...
        [2] Waiting for user... [UserTask(Task down)]
        [2] --> msg in: t_wrong
        [2] Waiting for user... [UserTask(Task down)]
        [2] --> msg in: tup2
        [2] Waiting for user... [UserTask(Task down)]
        [2] --> msg in: t_wrong
        [2] Waiting for user... [UserTask(Task down)]
        [2] --> msg in: tdown2
        [2] DOING: UserTask(Task down)
        [2] DONE
```

