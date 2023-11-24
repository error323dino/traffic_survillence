import zmq

context = zmq.Context()

subscriber1 = context.socket(zmq.SUB)
subscriber1.connect("tcp://localhost:5556")
subscriber1.setsockopt_string(zmq.SUBSCRIBE, "")
subscriber2 = context.socket(zmq.SUB)
subscriber2.connect("tcp://localhost:5554")
subscriber2.setsockopt_string(zmq.SUBSCRIBE, "")

ach1 = context.socket(zmq.SUB)
ach1.connect("tcp://localhost:5557")
ach1.setsockopt_string(zmq.SUBSCRIBE, "")
ach2 = context.socket(zmq.SUB)
ach2.connect("tcp://localhost:5553")
ach2.setsockopt_string(zmq.SUBSCRIBE, "")


poller = zmq.Poller()
poller.register(subscriber1, zmq.POLLIN)
poller.register(subscriber2, zmq.POLLIN)

poller.register(ach1, zmq.POLLIN)
poller.register(ach2, zmq.POLLIN)


publisher = context.socket(zmq.PUB)
publisher.bind("tcp://*:5555")  

processes = ["Process 1", "Process 2"]

current_green_index = 0

while True:
    next_green_index = (current_green_index + 1) % len(processes)
    next_green_process = processes[next_green_index]

    socks = dict(poller.poll(100))
    
    intent_message = "Changing to Green"
    received = False

    while True:
        print(f"Sending to {next_green_process}")
        publisher.send_string(f"{intent_message} for {next_green_process}")
        try:
            if next_green_process == "Process 1":
                acknowledgment = ach1.recv_string(flags=zmq.NOBLOCK)
            else:
                acknowledgment = ach2.recv_string(flags=zmq.NOBLOCK)
            print(acknowledgment)
            print(f"Sent green light to {next_green_process}")
            received = True
            break
        except zmq.error.Again:
            pass
 
    if received == True:
        while True:
            if next_green_process == "Process 1":
                red = subscriber1.recv_string()
            else:
                red = subscriber2.recv_string()
            print(f"{next_green_process} is now red")
            current_green_index = next_green_index
            break