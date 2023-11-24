This github includes the backend for the traffic survillence system.

2 cameras with seperate python files to run in parallel, same goes to red1 red2 python files

The main.py consist of ZeroMQ logic, where it conducts the traffic lights by sending signals to the cameras, and the cameras will send the signals to this main file

red1 and red2 will be executed and stopped automatically, according to the logic in the cam1 cam2

Pictures taken from red1 and red2 are saved in the database (firebase) and also the local 

Image processing model is predefined, using yolov4-tiny (light weight not that laggy)

Firebase json key i will share in grp instead to avoid google rules violatation

**reading for cars that passed thru at red lights is inaccurate
** pictures taken for car plate is at red1 red2, but the screenshots tend to take pic of the same car many times (due to haevy image processing load, slower video loading)
**car plate image processing not tested as cant find relevant video for that







