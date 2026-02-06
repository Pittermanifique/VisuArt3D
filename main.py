from multiprocessing import Process, Queue, shared_memory, Event
import struct
import time
import uvicorn


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

    # Boucle principale
    while True:
        rot_track = struct.unpack("f", buffer_track[0:4])[0]
        buffer_3D[0:4] = struct.pack("f", rot_track * 180)
        time.sleep(0.1)