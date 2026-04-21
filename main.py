from multiprocessing import Process, Queue, shared_memory, Event
import struct
import time
import uvicorn
import serial
import struct


def start_viewer(queue):
    from afichage import UrsinaViewer
    viewer = UrsinaViewer(queue)
    viewer.run()

def start_api(queue):
    import api

    api.queue = queue
    uvicorn.run("api:app", host="0.0.0.0", port=8000)

def start_tracking(started_event,queue):
    from tracking import face_detection

    try:
        shm = shared_memory.SharedMemory(name='shm_track')
        shm.close()
        shm.unlink()
        print("Mémoire shm_track supprimée.")
    except FileNotFoundError:
        print("Aucune mémoire shm_track à supprimer.")

    shm_track = shared_memory.SharedMemory(create=True, size=4, name='shm_track')
    buffer = shm_track.buf

    started_event.set()
    
    face_detection(buffer,queue)

if __name__ == "__main__":

    # Supprimer ancienne mémoire
    try:
        shm = shared_memory.SharedMemory(name='shm_3D')
        shm.close()
        shm.unlink()
        print("Mémoire shm_3D supprimée.")
    except FileNotFoundError:
        print("Aucune mémoire shm_3D à supprimer.")

    # Créer la queue de communication

    queue = Queue()

    started = Event()
    tracking_process = Process(target=start_tracking, args=(started,queue,))
    tracking_process.start()

    started.wait()

    # Créer mémoire partagée
    shm_3D = shared_memory.SharedMemory(create=True, size=4, name='shm_3D')
    buffer_3D = shm_3D.buf

    # Mémoire track existante
    shm_track = shared_memory.SharedMemory(name='shm_track')
    buffer_track = shm_track.buf
    
    # Lancer Ursina dans un process séparé
    viewer_process = Process(target=start_viewer, args=(queue,))
    viewer_process.start()

    # Lancer l'API dans un process séparé
    api_process = Process(target=start_api, args=(queue,))
    api_process.start()

    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    time.sleep(4)

    while True:
        rot_track = struct.unpack("f", buffer_track[0:4])[0]

        raw_data = ser.readline().decode('utf-8').strip()

        # Check if the string has more than one decimal point
        if raw_data.count('.') <= 1 and raw_data.replace('.', '', 1).replace('-', '', 1).isdigit():
            try:
                buffer_3D[0:4] = struct.pack("f", float(raw_data))
            except ValueError:
                print(f"Skipping malformed data: {raw_data}")
        else:
            print(f"Invalid numeric format received: {raw_data}")
            
        time.sleep(0.1)